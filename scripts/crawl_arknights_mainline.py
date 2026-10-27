#!/usr/bin/env python3
"""Crawl every main-story chapter from ASS into one document per stage."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.parse import unquote, urlsplit

import requests

import crawl_arknights_story as core


MAINLINE_ROOT = core.DOCS_ROOT / "主线"


MAINLINE_CARDS_JS = r"""
return Array.from(document.querySelectorAll(".card"))
  .map((card) => {
    const buttons = Array.from(card.querySelectorAll("button"));
    const typeButton = buttons.find((button) =>
      ["主线", "支线", "剧情"].includes((button.textContent || "").trim())
    );
    if (!typeButton || (typeButton.textContent || "").trim() !== "主线") {
      return null;
    }
    const titleButton = buttons.find(
      (button) => button !== typeButton && button.classList.contains("cardname")
    );
    const cover = card.querySelector(".cardcover");
    const background = cover ? getComputedStyle(cover).backgroundImage : "";
    const match = background.match(/url\(["']?(.*?)["']?\)/);
    return {
      title: (titleButton?.textContent || "").trim(),
      cover: match ? match[1] : ""
    };
  })
  .filter((card) => card && card.title);
"""


def discover_cards(driver) -> list[dict[str, str]]:
    driver.get(core.BASE_URL + "/activities")
    core.wait_js(
        driver,
        "return document.readyState === 'complete' && "
        "document.querySelectorAll('.card').length > 0;",
        timeout=45,
        description="主线章节列表加载",
    )
    cards = driver.execute_script(MAINLINE_CARDS_JS)
    if not cards:
        raise RuntimeError("没有发现主线章节卡片")
    return cards


def open_chapter(
    driver,
    card: dict[str, str],
) -> tuple[str, list[dict[str, str]]]:
    driver.get(core.BASE_URL + "/activities")
    title_json = json.dumps(card["title"], ensure_ascii=False)
    ready_script = f"""
    const wanted = {title_json};
    return Array.from(document.querySelectorAll(".card")).some((card) => {{
      const buttons = Array.from(card.querySelectorAll("button"));
      const isMainline = buttons.some(
        (button) => (button.textContent || "").trim() === "主线"
      );
      return isMainline && buttons.some(
        (button) =>
          button.classList.contains("cardname") &&
          (button.textContent || "").trim() === wanted &&
          (button.textContent || "").trim() !== "主线"
      );
    }});
    """
    core.wait_js(
        driver,
        ready_script,
        timeout=45,
        description=f"定位主线章节：{card['title']}",
    )
    driver.execute_script(
        f"""
        const wanted = {title_json};
        const card = Array.from(document.querySelectorAll(".card")).find((card) => {{
          const buttons = Array.from(card.querySelectorAll("button"));
          return buttons.some(
              (button) => (button.textContent || "").trim() === "主线"
            ) &&
            buttons.some(
              (button) =>
                button.classList.contains("cardname") &&
                (button.textContent || "").trim() === wanted &&
                (button.textContent || "").trim() !== "主线"
            );
        }});
        const titleButton = Array.from(card.querySelectorAll("button")).find(
          (button) =>
            button.classList.contains("cardname") &&
            (button.textContent || "").trim() === wanted
        );
        titleButton.scrollIntoView({{ block: "center" }});
        titleButton.click();
        """
    )
    core.wait_js(
        driver,
        "return location.pathname !== '/activities';",
        timeout=45,
        description=f"进入主线章节：{card['title']}",
    )
    timeline = core.wait_js(
        driver,
        core.TIMELINE_JS,
        timeout=45,
        description=f"读取主线剧情目录：{card['title']}",
    )
    if not isinstance(timeline, list) or not timeline:
        raise RuntimeError(f"没有读到主线剧情目录：{card['title']}")
    return driver.current_url, timeline


def crawl_chapter(
    driver,
    session: requests.Session,
    card: dict[str, str],
    *,
    timeout: int,
) -> dict[str, object]:
    title = card["title"]
    print(f"[主线章节] {title}", flush=True)
    chapter_url, timeline = open_chapter(driver, card)
    print(f"  剧情节点：{len(timeline)}", flush=True)

    stories = []
    for position, item in enumerate(timeline, start=1):
        print(
            f"  [{position:02d}/{len(timeline):02d}] "
            f"{item['code']} {item['title']}",
            flush=True,
        )
        stories.append(core.extract_story(driver, item, timeout=timeout))

    stage_groups = core.group_stories_by_stage(stories)
    print(f"  合并后关卡：{len(stage_groups)}", flush=True)

    all_urls = {
        block["src"]
        for story in stories
        for block in story["blocks"]
        if block.get("type") == "image" and block.get("src")
    }
    used_names: dict[str, str] = {}
    image_names: dict[str, str] = {}
    for url in sorted(all_urls):
        image_names[url] = core.image_file_name(url, used_names)

    safe_title = core.safe_component(title)
    chapter_root = MAINLINE_ROOT / safe_title
    image_root = core.ASSETS_ROOT / "主线" / safe_title
    chapter_root.mkdir(parents=True, exist_ok=True)
    image_root.mkdir(parents=True, exist_ok=True)
    image_link_prefix = os.path.relpath(
        image_root, chapter_root
    ).replace("\\", "/")

    downloaded = 0
    for url, name in image_names.items():
        if core.download_image(
            session, url, image_root / name, timeout=timeout
        ):
            downloaded += 1

    cover_url = card.get("cover", "")
    cover_name = ""
    if cover_url:
        suffix = Path(unquote(urlsplit(cover_url).path)).suffix or ".png"
        cover_name = f"event-cover{suffix}"
        if core.download_image(
            session, cover_url, image_root / cover_name, timeout=timeout
        ):
            downloaded += 1

    spec = core.ActivitySpec(title, title)
    rendered = []
    for position, segments in enumerate(stage_groups, start=1):
        file_name, content, stage_title, summaries = core.render_chapter(
            spec,
            position,
            segments,
            image_names,
            source_kind="主线章节",
            image_link_prefix=image_link_prefix,
        )
        core.verify_chapter(content, chapter_root)
        rendered.append(
            {
                "file_name": file_name,
                "content": content,
                "title": stage_title,
                "code": segments[0]["code"],
                "summaries": summaries,
            }
        )

    for old_file in chapter_root.glob("*.md"):
        if old_file.name != "index.md" and old_file.name[:2].isdigit():
            old_file.unlink()

    for chapter in rendered:
        (chapter_root / chapter["file_name"]).write_text(
            chapter["content"], encoding="utf-8"
        )

    index_lines = [f"# {title}", ""]
    if cover_name:
        index_lines.extend(
            (f"![章节封面]({image_link_prefix}/{cover_name})", "")
        )
    index_lines.extend(
        (
            f"> 明日方舟主线章节「{title}」剧情存档，"
            f"共收录 {len(rendered)} 个关卡。  ",
            f"> 来源：[ASS 明日方舟剧情站]({chapter_url})  ",
            "",
            "游戏原文及图片版权归 Arknights / 上海鹰角网络科技有限公司所有，"
            "此处仅作剧情资料存档。",
            "",
            "## 关卡目录",
            "",
            "| 序号 | 编号 | 标题 | 简介 |",
            "| ---: | --- | --- | --- |",
        )
    )
    for position, chapter in enumerate(rendered, start=1):
        summary = "<br>".join(
            core.clean_text(item).replace("\n", " ")
            for item in chapter["summaries"]
        ).replace("|", "\\|")
        index_lines.append(
            f"| {position} | {chapter['code'] or '—'} | "
            f"[{chapter['title']}]({core.markdown_link_target(chapter['file_name'])}) | "
            f"{summary} |"
        )
    index_lines.append("")
    (chapter_root / "index.md").write_text(
        "\n".join(index_lines), encoding="utf-8"
    )

    normalised = [
        core.normalise_blocks(
            block for segment in segments for block in segment["blocks"]
        )
        for segments in stage_groups
    ]
    return {
        "chapter": title,
        "stages": len(rendered),
        "dialogue_blocks": sum(
            block.get("type") == "dialogue"
            for blocks in normalised
            for block in blocks
        ),
        "image_references": sum(
            block.get("type") == "image"
            for blocks in normalised
            for block in blocks
        ),
        "image_files_downloaded": downloaded,
    }


def write_mainline_index(cards: list[dict[str, str]]) -> None:
    rows = []
    for position, card in enumerate(cards, start=1):
        chapter_root = MAINLINE_ROOT / core.safe_component(card["title"])
        if not (chapter_root / "index.md").exists():
            continue
        count = len(list(chapter_root.glob("[0-9][0-9]-*.md")))
        rows.append((position, card["title"], count))

    lines = [
        "# 明日方舟主线剧情",
        "",
        "按主线章节整理的剧情文本与场景图。每个关卡合并为一篇文档，"
        "标题只保留剧情名。",
        "",
        "整理规则：[剧情抓取与整理规范](../剧情抓取规范.md)",
        "",
        "| 序号 | 章节 | 关卡数 |",
        "| ---: | --- | ---: |",
    ]
    for position, title, count in rows:
        folder = core.markdown_link_target(core.safe_component(title))
        lines.append(
            f"| {position} | [{title}]({folder}/index.md) | {count} |"
        )
    lines.append("")
    MAINLINE_ROOT.mkdir(parents=True, exist_ok=True)
    (MAINLINE_ROOT / "index.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="抓取 ASS 明日方舟全部主线剧情。"
    )
    parser.add_argument(
        "--chapter",
        action="append",
        help="只抓取指定主线章节，可重复。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="仅处理前 N 个章节，用于验证。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": core.BASE_URL + "/",
        }
    )

    driver = core.make_driver()
    started = time.time()
    cards = discover_cards(driver)
    if args.chapter:
        wanted = set(args.chapter)
        cards = [card for card in cards if card["title"] in wanted]
        missing = wanted - {card["title"] for card in cards}
        if missing:
            driver.quit()
            raise SystemExit("未知主线章节：" + "、".join(sorted(missing)))
    if args.limit:
        cards = cards[: args.limit]
    failures = []
    results = []
    try:
        for card in cards:
            try:
                results.append(
                    crawl_chapter(driver, session, card, timeout=45)
                )
            except Exception as exc:
                failures.append({"chapter": card["title"], "error": str(exc)})
                print(f"  抓取失败：{exc}", file=sys.stderr, flush=True)
            finally:
                write_mainline_index(cards)
                core.write_collection_index()
    finally:
        driver.quit()

    print(json.dumps(results, ensure_ascii=False, indent=2))
    if failures:
        print(json.dumps({"failures": failures}, ensure_ascii=False, indent=2))
        return 1
    print(f"完成：{len(results)} 个主线章节，耗时 {time.time() - started:.1f} 秒")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
