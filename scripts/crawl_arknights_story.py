#!/usr/bin/env python3
"""Crawl rendered Arknights story pages into text-and-image Markdown documents.

The output contract is documented in:
    docs/明日方舟/剧情抓取规范.md

The site is a SvelteKit client-rendered application, so this crawler uses
Selenium to wait for and read the rendered DOM. Images are downloaded with
requests and embedded locally.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import unquote, urljoin, urlsplit

import requests
from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait


BASE_URL = "https://ass.m-j.bond"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs" / "明日方舟"
ASSETS_ROOT = PROJECT_ROOT / "docs" / "assets" / "明日方舟"
CONTRACT_VERSION = "1.0"


@dataclass(frozen=True)
class ActivitySpec:
    folder: str
    source_title: str


# The folder name is user-facing; source_title is the exact title shown by the
# source site and is used to locate the activity card.
ACTIVITIES: dict[str, ActivitySpec] = {
    "骑兵与猎人": ActivitySpec("骑兵与猎人", "骑兵与猎人"),
    "生于黑夜": ActivitySpec("生于黑夜", "生于黑夜"),
    "遗尘漫步": ActivitySpec("遗尘漫步", "遗尘漫步"),
    "覆潮之下": ActivitySpec("覆潮之下", "覆潮之下"),
    "愚人号": ActivitySpec("愚人号", "愚人号"),
    "空想花庭": ActivitySpec("空想花庭", "空想花庭"),
    "崔林特尔·梅之金": ActivitySpec("崔林特尔·梅之金", "崔林特尔梅之金"),
    "生路": ActivitySpec("生路", "生路"),
    "巴别塔": ActivitySpec("巴别塔", "巴别塔"),
}

DEFAULT_ACTIVITIES = (
    "生于黑夜",
    "遗尘漫步",
    "覆潮之下",
    "愚人号",
    "空想花庭",
    "崔林特尔·梅之金",
    "生路",
    "巴别塔",
)


TIMELINE_JS = r"""
const clean = (value) => (value || "")
  .replace(/\u00a0/g, " ")
  .replace(/[ \t]+/g, " ")
  .replace(/\n{3,}/g, "\n\n")
  .trim();

return Array.from(document.querySelectorAll("li.timeline-item"))
  .map((item) => {
    const code = clean(
      item.querySelector(".timeline-opposite-content p")?.textContent
    );
    const link = item.querySelector(".timeline-content a");
    const summary = clean(
      item.querySelector(".timeline-content p")?.textContent
    );
    if (!link) return null;
    return {
      code,
      title: clean(link.textContent),
      summary,
      href: new URL(link.getAttribute("href"), location.href).href
    };
  })
  .filter(Boolean);
"""


STORY_JS = r"""
const clean = (value) => (value || "")
  .replace(/\u00a0/g, " ")
  .replace(/[ \t]+/g, " ")
  .replace(/\n{3,}/g, "\n\n")
  .trim();

const root = document.querySelector("div.block > div.text-lg");
if (!root) return null;

const blocks = [];
for (const element of Array.from(root.children)) {
  const className = typeof element.className === "string"
    ? element.className
    : "";

  if (className.includes("music")) {
    blocks.push({
      type: "music",
      text: clean(element.querySelector("button")?.textContent || element.textContent)
    });
    continue;
  }

  const image = Array.from(element.children)
    .find((child) => child.tagName === "IMG");
  if (image) {
    const source =
      image.currentSrc ||
      image.getAttribute("src") ||
      image.getAttribute("data-src") ||
      (image.alt?.startsWith("http") ? image.alt : "");
    blocks.push({
      type: "image",
      src: clean(source),
      alt: clean(image.alt)
    });
    continue;
  }

  if (element.children.length >= 2) {
    const speaker = clean(
      element.children[0]?.innerText ||
      element.children[0]?.textContent
    );
    const text = clean(
      element.children[1]?.innerText ||
      element.children[1]?.textContent
    );
    if (speaker || text) {
      blocks.push({ type: "dialogue", speaker, text });
    }
    continue;
  }

  const text = clean(element.innerText || element.textContent);
  if (text) blocks.push({ type: "text", text });
}

return {
  documentTitle: document.title,
  savedFrom: location.href,
  blocks
};
"""


def clean_text(value: str | None) -> str:
    if not value:
        return ""
    value = value.replace("\u00a0", " ")
    value = re.sub(r"[ \t]+", " ", value)
    value = re.sub(r"\n{3,}", "\n\n", value)
    return value.strip()


def wait_js(
    driver: webdriver.Chrome,
    script: str,
    *,
    timeout: int,
    description: str,
) -> Any:
    try:
        return WebDriverWait(driver, timeout, poll_frequency=0.2).until(
            lambda current: current.execute_script(script) or False
        )
    except TimeoutException as exc:
        raise RuntimeError(f"等待超时：{description}") from exc


def make_driver() -> webdriver.Chrome:
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1440,1200")
    options.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/131.0.0.0 Safari/537.36"
    )
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(90)
    return driver


def discover_activity(
    driver: webdriver.Chrome,
    spec: ActivitySpec,
    *,
    timeout: int,
) -> tuple[str, str, list[dict[str, str]]]:
    driver.get(f"{BASE_URL}/activities")
    wait_js(
        driver,
        "return document.readyState === 'complete' && "
        "document.querySelectorAll('button').length > 0;",
        timeout=timeout,
        description=f"活动列表加载：{spec.source_title}",
    )

    title_json = json.dumps(spec.source_title, ensure_ascii=False)
    card_script = f"""
    const wanted = {title_json};
    const button = Array.from(document.querySelectorAll("button"))
      .find((item) => (item.textContent || "").trim() === wanted);
    if (!button) return null;
    const card = button.closest(".card");
    const cover = card?.querySelector(".cardcover");
    const background = cover ? getComputedStyle(cover).backgroundImage : "";
    const match = background.match(/url\\(["']?(.*?)["']?\\)/);
    return {{ coverUrl: match ? match[1] : "" }};
    """
    card = wait_js(
        driver,
        card_script,
        timeout=timeout,
        description=f"定位活动卡片：{spec.source_title}",
    )

    driver.execute_script(
        f"""
        const wanted = {title_json};
        const button = Array.from(document.querySelectorAll("button"))
          .find((item) => (item.textContent || "").trim() === wanted);
        button.scrollIntoView({{ block: "center" }});
        button.click();
        """
    )
    wait_js(
        driver,
        "return location.pathname !== '/activities';",
        timeout=timeout,
        description=f"进入活动：{spec.source_title}",
    )
    items = wait_js(
        driver,
        TIMELINE_JS,
        timeout=timeout,
        description=f"读取活动剧情目录：{spec.source_title}",
    )
    if not isinstance(items, list) or not items:
        raise RuntimeError(f"没有读到剧情目录：{spec.source_title}")
    return str(card.get("coverUrl", "")), driver.current_url, items


def extract_story(
    driver: webdriver.Chrome,
    item: dict[str, str],
    *,
    timeout: int,
) -> dict[str, Any]:
    driver.get(item["href"])
    wait_js(
        driver,
        "return !!document.querySelector('div.block > div.text-lg') && "
        "document.querySelector('div.block > div.text-lg').children.length > 0;",
        timeout=timeout,
        description=f"加载剧情正文：{item['title']}",
    )
    story = driver.execute_script(STORY_JS)
    if not story or not story.get("blocks"):
        raise RuntimeError(f"剧情正文为空：{item['title']}")
    return {
        **item,
        **story,
    }


def join_dialogue(left: str, right: str) -> str:
    """Join consecutive lines by the same speaker without changing the prose."""
    if not left:
        return right
    if not right:
        return left
    if left[-1].isascii() and left[-1].isalnum():
        if right[0].isascii() and right[0].isalnum():
            return f"{left} {right}"
    return left + right


def normalise_blocks(raw_blocks: Iterable[dict[str, Any]]) -> list[dict[str, str]]:
    """Apply the text/image contract to one rendered story page.

    Music blocks are removed and are transparent to merging. Images and
    text-only blocks are boundaries, so speakers are never merged across them.
    """
    blocks: list[dict[str, str]] = []
    for raw in raw_blocks:
        block_type = raw.get("type")
        if block_type == "music":
            continue

        if block_type == "image":
            source = clean_text(raw.get("src"))
            if source:
                blocks.append(
                    {
                        "type": "image",
                        "src": source,
                        "alt": clean_text(raw.get("alt")),
                    }
                )
            continue

        if block_type == "dialogue":
            speaker = clean_text(raw.get("speaker"))
            text = clean_text(raw.get("text"))
            if not text:
                continue
            if not speaker:
                blocks.append({"type": "text", "text": text})
                continue
            if (
                blocks
                and blocks[-1].get("type") == "dialogue"
                and blocks[-1].get("speaker") == speaker
            ):
                blocks[-1]["text"] = join_dialogue(blocks[-1]["text"], text)
            else:
                blocks.append(
                    {"type": "dialogue", "speaker": speaker, "text": text}
                )
            continue

        if block_type == "text":
            text = clean_text(raw.get("text"))
            if text:
                blocks.append({"type": "text", "text": text})

    for previous, current in zip(blocks, blocks[1:]):
        if (
            previous.get("type") == current.get("type") == "dialogue"
            and previous.get("speaker") == current.get("speaker")
        ):
            raise RuntimeError(
                f"同角色台词未合并：{previous.get('speaker')}"
            )

    return blocks


def image_file_name(url: str, used: dict[str, str]) -> str:
    parsed = urlsplit(url)
    raw_name = Path(unquote(parsed.path)).name
    raw_name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", raw_name).strip(" .")
    if not raw_name:
        suffix = Path(parsed.path).suffix or ".png"
        raw_name = "image-" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:12] + suffix
    if raw_name in used and used[raw_name] != url:
        stem = Path(raw_name).stem
        suffix = Path(raw_name).suffix
        digest = hashlib.sha1(url.encode("utf-8")).hexdigest()[:8]
        raw_name = f"{stem}-{digest}{suffix}"
    used[raw_name] = url
    return raw_name


def download_image(
    session: requests.Session,
    url: str,
    target: Path,
    *,
    timeout: int,
) -> bool:
    if target.exists() and target.stat().st_size > 0:
        return False

    response = session.get(url, timeout=timeout)
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "").split(";")[0].strip()
    if not content_type.startswith("image/"):
        raise RuntimeError(
            f"图片响应不是 image/*：{url}，Content-Type={content_type or '缺失'}"
        )

    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + ".part")
    temporary.write_bytes(response.content)
    os.replace(temporary, target)
    return True


def safe_component(value: str) -> str:
    value = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "·", value)
    return value.strip(" .") or "untitled"


def markdown_link_target(file_name: str) -> str:
    return file_name.replace(" ", "%20")


def strip_story_label(title: str) -> str:
    """Remove flow labels so the document title contains only the story name."""
    previous = None
    cleaned = title.strip()
    while cleaned != previous:
        previous = cleaned
        cleaned = re.sub(r"\s*(?:行动前|行动后|幕间)\s*$", "", cleaned).strip()
    return cleaned


def group_stories_by_stage(
    stories: list[dict[str, Any]],
) -> list[list[dict[str, Any]]]:
    """Group timeline entries by stage code while preserving source order."""
    groups: dict[str, list[dict[str, Any]]] = {}
    for story in stories:
        key = clean_text(story.get("code")) or clean_text(story.get("title"))
        groups.setdefault(key, []).append(story)
    return list(groups.values())


def render_chapter(
    spec: ActivitySpec,
    index: int,
    segments: list[dict[str, Any]],
    image_names: dict[str, str],
    *,
    source_kind: str = "活动",
    image_link_prefix: str = "images",
) -> tuple[str, str, str, list[str]]:
    first = segments[0]
    code = clean_text(first["code"])
    title = strip_story_label(first["title"])
    if code:
        title = re.sub(
            rf"^\s*{re.escape(code)}(?:\s+|$)", "", title
        ).strip()
    blocks = normalise_blocks(
        block for segment in segments for block in segment["blocks"]
    )
    file_parts = [f"{index:02d}"]
    if code:
        file_parts.append(safe_component(code))
    file_parts.append(safe_component(title.replace(" ", "-")))
    file_name = "-".join(file_parts) + ".md"
    source_title = spec.source_title
    lines = [
        f"# {title}",
        "",
        f"> {source_kind}：{source_title}  ",
    ]
    if code:
        lines.append(f"> 编号：{code}  ")
    lines.append(
        "> 原始页面："
        + " · ".join(
            f"[{position}]({segment['href']})"
            for position, segment in enumerate(segments, start=1)
        )
    )
    if source_title != spec.folder:
        lines.append(f"> 站内活动名：{source_title}  ")

    summaries = [
        clean_text(segment.get("summary"))
        for segment in segments
        if clean_text(segment.get("summary"))
    ]
    lines.append("")
    if len(summaries) == 1:
        lines.append(f"**剧情简介**：{summaries[0].replace(chr(10), ' ')}")
    else:
        lines.append("**剧情简介**：")
        for summary in summaries:
            lines.extend(("", summary))
    lines.extend(("", "---", ""))

    for block in blocks:
        if block["type"] == "image":
            name = image_names[block["src"]]
            lines.extend((f"![场景图]({image_link_prefix}/{name})", ""))
        elif block["type"] == "dialogue":
            lines.extend(
                (f"**{html.escape(block['speaker'])}**：{block['text']}", "")
            )
        elif block["type"] == "text":
            lines.extend((block["text"], ""))

    return file_name, "\n".join(lines).strip() + "\n", title, summaries


def verify_chapter(content: str, root: Path) -> None:
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^>\s*♪", stripped):
            raise RuntimeError("输出仍包含由音乐事件生成的提示行")
        if stripped in {"音乐停止", "> 音乐停止"}:
            raise RuntimeError("输出仍包含音乐停止提示")

    for match in re.finditer(r"!\[[^\]]*\]\(([^)]+)\)", content):
        image_path = (root / unquote(match.group(1))).resolve()
        docs_root = PROJECT_ROOT.joinpath("docs").resolve()
        if docs_root not in image_path.parents:
            raise RuntimeError(f"图片路径逃出 docs 目录：{image_path}")
        if not image_path.is_file() or image_path.stat().st_size == 0:
            raise RuntimeError(f"图片文件缺失：{image_path}")


def crawl_activity(
    driver: webdriver.Chrome,
    session: requests.Session,
    spec: ActivitySpec,
    *,
    timeout: int,
) -> dict[str, Any]:
    print(f"[抓取] {spec.folder}", flush=True)
    cover_url, activity_url, timeline = discover_activity(
        driver, spec, timeout=timeout
    )
    print(f"  剧情节点：{len(timeline)}", flush=True)

    stories = []
    for position, item in enumerate(timeline, start=1):
        print(
            f"  [{position:02d}/{len(timeline):02d}] {item['code']} {item['title']}",
            flush=True,
        )
        stories.append(extract_story(driver, item, timeout=timeout))
    stage_groups = group_stories_by_stage(stories)
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
        image_names[url] = image_file_name(url, used_names)

    activity_root = DOCS_ROOT / spec.folder
    image_root = ASSETS_ROOT / spec.folder
    activity_root.mkdir(parents=True, exist_ok=True)
    image_root.mkdir(parents=True, exist_ok=True)
    image_link_prefix = os.path.relpath(
        image_root, activity_root
    ).replace("\\", "/")

    downloaded = 0
    for url, name in image_names.items():
        if download_image(session, url, image_root / name, timeout=timeout):
            downloaded += 1

    cover_name = ""
    if cover_url:
        cover_path = Path(unquote(urlsplit(cover_url).path)).name or "cover.png"
        suffix = Path(cover_path).suffix or ".png"
        cover_name = f"event-cover{suffix}"
        if download_image(
            session, cover_url, image_root / cover_name, timeout=timeout
        ):
            downloaded += 1

    rendered = []
    for position, segments in enumerate(stage_groups, start=1):
        file_name, content, title, summaries = render_chapter(
            spec,
            position,
            segments,
            image_names,
            image_link_prefix=image_link_prefix,
        )
        verify_chapter(content, activity_root)
        rendered.append(
            {
                "file_name": file_name,
                "content": content,
                "title": title,
                "code": segments[0]["code"],
                "summaries": summaries,
                "sources": [segment["href"] for segment in segments],
            }
        )

    # All pages and assets have been fetched and validated before replacing
    # previously generated chapter files.
    for old_file in activity_root.glob("*.md"):
        if old_file.name != "index.md" and re.match(r"^\d{2,3}-", old_file.name):
            old_file.unlink()

    for chapter in rendered:
        (activity_root / chapter["file_name"]).write_text(
            chapter["content"], encoding="utf-8"
        )

    index_lines = [
        f"# {spec.source_title}",
        "",
    ]
    if cover_name:
        index_lines.extend(
            (f"![活动封面]({image_link_prefix}/{cover_name})", "")
        )
    source_note = (
        f"> 站内活动名：{spec.source_title}  \n"
        if spec.source_title != spec.folder
        else ""
    )
    index_lines.extend(
        (
            f"> 明日方舟活动「{spec.source_title}」剧情存档，"
            f"共收录 {len(rendered)} 个关卡的剧情。  ",
            f"> 来源：[ASS 明日方舟剧情站]({activity_url})  ",
            f"> 抓取日期：{date.today().isoformat()}  ",
            source_note.rstrip(),
            "",
            "游戏原文及图片版权归 Arknights / 上海鹰角网络科技有限公司所有，"
            "此处仅作剧情资料存档。",
            "",
            "## 剧情目录",
            "",
            "| 序号 | 编号 | 标题 | 简介 |",
            "| ---: | --- | --- | --- |",
        )
    )
    for position, chapter in enumerate(rendered, start=1):
        summary = "<br>".join(
            clean_text(item).replace("\n", " ")
            for item in chapter["summaries"]
        ).replace("|", "\\|")
        index_lines.append(
            f"| {position} | {chapter['code']} | "
            f"[{chapter['title']}]({markdown_link_target(chapter['file_name'])}) | "
            f"{summary} |"
        )
    index_lines.append("")
    (activity_root / "index.md").write_text(
        "\n".join(index_lines), encoding="utf-8"
    )

    stage_blocks = [
        normalise_blocks(
            block for segment in segments for block in segment["blocks"]
        )
        for segments in stage_groups
    ]
    dialogue_count = sum(
        block.get("type") == "dialogue"
        for blocks in stage_blocks
        for block in blocks
    )
    return {
        "activity": spec.folder,
        "chapters": len(rendered),
        "dialogue_blocks": dialogue_count,
        "image_references": sum(
            block.get("type") == "image"
            for blocks in stage_blocks
            for block in blocks
        ),
        "image_files_downloaded": downloaded,
        "output": str(activity_root),
    }


def write_collection_index() -> None:
    rows: list[tuple[str, str, int]] = []
    mainline_index = DOCS_ROOT / "主线" / "index.md"
    if mainline_index.exists():
        chapters = len(
            list((DOCS_ROOT / "主线").rglob("[0-9][0-9]-*.md"))
        )
        rows.append(("主线", "主线/index.md", chapters))

    for spec in ACTIVITIES.values():
        event_index = DOCS_ROOT / spec.folder / "index.md"
        if not event_index.exists():
            continue
        chapters = len(list((DOCS_ROOT / spec.folder).glob("[0-9][0-9]-*.md")))
        rows.append((spec.folder, f"{spec.folder}/index.md", chapters))

    lines = [
        "# 明日方舟剧情存档",
        "",
        "按主线和活动整理的明日方舟剧情文本与场景图。每个关卡合并为一篇文档，"
        "正文不保留音乐提示，同一角色相邻的连续台词会合并。",
        "",
        "整理规则：[剧情抓取与整理规范](剧情抓取规范.md)",
        "",
        "| 主线/活动 | 关卡数 |",
        "| --- | ---: |",
    ]
    for name, target, chapters in rows:
        lines.append(
            f"| [{name}]({markdown_link_target(target)}) | {chapters} |"
        )
    lines.append("")
    DOCS_ROOT.mkdir(parents=True, exist_ok=True)
    (DOCS_ROOT / "index.md").write_text("\n".join(lines), encoding="utf-8")


def resolve_activity_names(values: list[str] | None, include_all: bool) -> list[str]:
    if include_all:
        return list(ACTIVITIES)
    if not values:
        return list(DEFAULT_ACTIVITIES)

    resolved = []
    source_to_folder = {
        spec.source_title: folder for folder, spec in ACTIVITIES.items()
    }
    for value in values:
        if value in ACTIVITIES:
            resolved.append(value)
        elif value in source_to_folder:
            resolved.append(source_to_folder[value])
        else:
            raise SystemExit(f"未知活动：{value}。可用活动：{', '.join(ACTIVITIES)}")
    return resolved


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="抓取 ASS 明日方舟剧情并生成纯文字+图片 Markdown。"
    )
    parser.add_argument(
        "--activity",
        action="append",
        help="指定活动，可重复。默认抓取本次新增的 8 个活动。",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="抓取配置中全部活动，包括《骑兵与猎人》。",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=45,
        help="单页等待和网络请求超时秒数，默认 45。",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    names = resolve_activity_names(args.activity, args.all)
    session = requests.Session()
    session.headers.update(
        {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/131.0.0.0 Safari/537.36"
            ),
            "Referer": BASE_URL + "/",
        }
    )

    driver = make_driver()
    started = time.time()
    results = []
    try:
        for name in names:
            results.append(
                crawl_activity(
                    driver,
                    session,
                    ACTIVITIES[name],
                    timeout=args.timeout,
                )
            )
    except (RuntimeError, WebDriverException, requests.RequestException) as exc:
        print(f"抓取失败：{exc}", file=sys.stderr)
        return 1
    finally:
        driver.quit()

    write_collection_index()
    elapsed = time.time() - started
    print(json.dumps(results, ensure_ascii=False, indent=2))
    print(f"完成：{len(results)} 个活动，耗时 {elapsed:.1f} 秒")
    print(f"汇总目录：{DOCS_ROOT / 'index.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
