#!/usr/bin/env python3
"""Validate generated Arknights story documents against the Markdown contract."""

from __future__ import annotations

import re
import sys
from pathlib import Path
from urllib.parse import unquote


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOCS_ROOT = PROJECT_ROOT / "docs" / "明日方舟"
DIALOGUE_RE = re.compile(r"^\*\*(.+?)\*\*：(.*)$", re.S)
IMAGE_RE = re.compile(r"!\[[^\]]*\]\(([^)]+)\)")
LOCAL_MD_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+\.md)\)")
CODE_RE = re.compile(r"^>\s*编号：(.+?)\s*$", re.M)
STORY_LABEL_RE = re.compile(r"行动(?:前|后)|幕间")
DOCS_DIR = PROJECT_ROOT / "docs"


def validate_links(content: str, document: Path, errors: list[str]) -> None:
    root = document.parent.resolve()
    docs_root = DOCS_DIR.resolve()
    for match in IMAGE_RE.finditer(content):
        target = (root / unquote(match.group(1))).resolve()
        if docs_root not in target.parents:
            errors.append(f"{document}: 图片路径逃出目录：{target}")
        elif not target.is_file() or target.stat().st_size == 0:
            errors.append(f"{document}: 图片缺失或为空：{target}")

    for match in LOCAL_MD_RE.finditer(content):
        raw_target = match.group(1)
        if "://" in raw_target or raw_target.startswith("#"):
            continue
        target = (root / unquote(raw_target)).resolve()
        if docs_root not in target.parents and docs_root != target.parent:
            errors.append(f"{document}: 链接路径逃出目录：{target}")
        elif not target.is_file():
            errors.append(f"{document}: Markdown 链接缺失：{target}")


def validate_chapter(content: str, document: Path, errors: list[str]) -> None:
    for line in content.splitlines():
        stripped = line.strip()
        if re.match(r"^>\s*♪", stripped):
            errors.append(f"{document}: 存在音乐事件生成的 ♪ 提示行")
        if stripped in {"音乐停止", "> 音乐停止"}:
            errors.append(f"{document}: 存在音乐停止提示")

    blocks = [
        block.strip()
        for block in re.split(r"\n\s*\n", content)
        if block.strip()
    ]
    previous_speaker: str | None = None
    for block in blocks:
        match = DIALOGUE_RE.match(block)
        speaker = match.group(1) if match else None
        if speaker is not None and speaker == previous_speaker:
            errors.append(f"{document}: 存在连续同角色段落：{speaker}")
        previous_speaker = speaker

    validate_links(content, document, errors)


def validate_stage_identity(
    content: str,
    document: Path,
    seen_codes: set[str],
    errors: list[str],
) -> None:
    if STORY_LABEL_RE.search(document.stem):
        errors.append(f"{document}: 文件名仍包含行动前/行动后/幕间")

    first_line = content.splitlines()[0] if content.splitlines() else ""
    if STORY_LABEL_RE.search(first_line):
        errors.append(f"{document}: 一级标题仍包含行动前/行动后/幕间")

    code_match = CODE_RE.search(content)
    if code_match:
        identifier = code_match.group(1).strip()
    else:
        identifier = first_line.removeprefix("# ").strip()
    if not identifier:
        errors.append(f"{document}: 缺少关卡编号或剧情名")
        return
    if identifier in seen_codes:
        errors.append(f"{document}: 同一章节内重复的关卡标识：{identifier}")
    seen_codes.add(identifier)


def validate_chapter_directory(
    activity_root: Path,
    errors: list[str],
) -> tuple[int, int]:
    chapters = sorted(
        path
        for path in activity_root.glob("*.md")
        if path.name != "index.md"
    )
    if not chapters:
        errors.append(f"{activity_root}: 没有剧情文件")
        return 0, 0

    seen_codes: set[str] = set()
    image_references = 0
    for chapter in chapters:
        content = chapter.read_text(encoding="utf-8")
        image_references += len(IMAGE_RE.findall(content))
        validate_chapter(content, chapter, errors)
        validate_stage_identity(content, chapter, seen_codes, errors)
    return len(chapters), image_references


def main() -> int:
    errors: list[str] = []
    chapter_count = 0
    image_references = 0

    if not DOCS_ROOT.is_dir():
        print(f"目录不存在：{DOCS_ROOT}", file=sys.stderr)
        return 1

    for activity_root in sorted(
        (path for path in DOCS_ROOT.iterdir() if path.is_dir()),
        key=lambda path: path.name,
    ):
        index = activity_root / "index.md"
        if not index.is_file():
            if (
                activity_root.name != "主线"
                and not any(activity_root.glob("[0-9][0-9]-*.md"))
            ):
                continue
            errors.append(f"{activity_root}: 缺少 index.md")
            continue
        validate_links(index.read_text(encoding="utf-8"), index, errors)

        if activity_root.name == "主线":
            chapter_dirs = sorted(
                (
                    path
                    for path in activity_root.iterdir()
                    if path.is_dir()
                ),
                key=lambda path: path.name,
            )
            if not chapter_dirs:
                errors.append(f"{activity_root}: 没有主线章节目录")
            for chapter_root in chapter_dirs:
                chapter_index = chapter_root / "index.md"
                if not chapter_index.is_file():
                    errors.append(f"{chapter_root}: 缺少 index.md")
                else:
                    validate_links(
                        chapter_index.read_text(encoding="utf-8"),
                        chapter_index,
                        errors,
                    )
                count, references = validate_chapter_directory(
                    chapter_root, errors
                )
                chapter_count += count
                image_references += references
        else:
            count, references = validate_chapter_directory(
                activity_root, errors
            )
            chapter_count += count
            image_references += references

    collection_index = DOCS_ROOT / "index.md"
    if not collection_index.is_file():
        errors.append(f"{DOCS_ROOT}: 缺少汇总 index.md")
    else:
        validate_links(
            collection_index.read_text(encoding="utf-8"),
            collection_index,
            errors,
        )

    if errors:
        print("\n".join(f"- {error}" for error in errors), file=sys.stderr)
        print(f"验收失败：{len(errors)} 个问题", file=sys.stderr)
        return 1

    print(f"验收通过：{chapter_count} 个关卡，{image_references} 个图片位置")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
