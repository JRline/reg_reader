#!/usr/bin/env python3
"""
Populates stub article nodes for every article in a chapter's outline, so the TOC/navigation
is complete for the whole chapter even before each article has been through the full
chatbot-translation pipeline. Never overwrites an article that already has real content
(children != [] or text_ja set) — this is purely additive scaffolding.

Usage:
    python3 build_skeleton.py <feed_id> <chapter_id> <chapter_number> <chapter_heading> <outline.tsv>

outline.tsv: three tab-separated columns, "第十一条の二<TAB>heading (ja, or empty)<TAB>heading (en, or empty)".

Example:
    python3 build_skeleton.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 feeds/fsa-basel-cap-jp/ch2_outline.tsv
"""
import json
import re
import sys
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"

KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
                "六": 6, "七": 7, "八": 8, "九": 9}


def kanji_to_int(s: str) -> int:
    if not s:
        return 0
    if "十" in s:
        tens_part, _, ones_part = s.partition("十")
        tens = KANJI_DIGITS.get(tens_part, 1) if tens_part else 1
        ones = KANJI_DIGITS.get(ones_part, 0) if ones_part else 0
        return tens * 10 + ones
    return KANJI_DIGITS.get(s, 0)


def article_number_to_slug(number: str) -> str:
    """'第十一条の十四' -> 'art11-14'; '第三条' -> 'art3'."""
    m = re.match(r"第([一二三四五六七八九十百]+)条(の([一二三四五六七八九十]+))?", number)
    if not m:
        raise ValueError(f"Can't parse article number: {number}")
    main = kanji_to_int(m.group(1))
    sub = kanji_to_int(m.group(3)) if m.group(3) else None
    return f"art{main}" + (f"-{sub}" if sub else "")


def load_outline(path: Path):
    entries = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        parts = (line.split("\t") + ["", ""])[:3]
        number = parts[0].strip()
        heading = parts[1].strip() or None
        heading_en = parts[2].strip() or None
        entries.append((number, heading, heading_en))
    return entries


def make_stub(article_id: str, number: str, heading: str | None, heading_en: str | None):
    return {
        "id": article_id,
        "type": "article",
        "number": number,
        "heading": heading,
        "heading_en": heading_en,
        "text_ja": None,
        "text_en": None,
        "summary_ja": None,
        "summary_en": None,
        "translation_status": "pending",
        "clauses_ja": [],
        "clauses_en": [],
        "refs": [],
        "defined_terms": [],
        "children": [],
    }


def has_real_content(node: dict) -> bool:
    return bool(node.get("text_ja")) or bool(node.get("children"))


def main():
    if len(sys.argv) not in (6, 7):
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id, chapter_number, chapter_heading, outline_path = sys.argv[1:6]
    chapter_heading_en = sys.argv[6] if len(sys.argv) == 7 else None

    feed_path = FEEDS_DIR / feed_id / "feed.json"
    if feed_path.exists():
        feed = json.loads(feed_path.read_text(encoding="utf-8"))
    else:
        feed = {"feed_id": feed_id, "root": {
            "id": feed_id, "type": "document", "number": None, "heading": None,
            "text_ja": None, "text_en": None, "children": [],
        }}

    root = feed["root"]
    chapter = next((c for c in root["children"] if c["id"] == chapter_id), None)
    if chapter is None:
        chapter = {
            "id": chapter_id, "type": "chapter", "number": chapter_number, "heading": chapter_heading,
            "heading_en": chapter_heading_en,
            "text_ja": None, "text_en": None, "clauses_ja": [], "clauses_en": [],
            "refs": [], "defined_terms": [], "children": [],
        }
        root["children"].append(chapter)
    elif chapter_heading_en and not chapter.get("heading_en"):
        chapter["heading_en"] = chapter_heading_en

    by_id = {a["id"]: a for a in chapter["children"]}
    added, skipped = 0, 0
    for number, heading, heading_en in load_outline(Path(outline_path)):
        slug = article_number_to_slug(number)
        article_id = f"{chapter_id}.{slug}"
        existing = by_id.get(article_id)
        if existing and has_real_content(existing):
            skipped += 1
            continue
        by_id[article_id] = make_stub(article_id, number, heading, heading_en)
        added += 1

    # Preserve outline order.
    ordered_ids = [f"{chapter_id}.{article_number_to_slug(n)}" for n, _, _ in load_outline(Path(outline_path))]
    chapter["children"] = [by_id[i] for i in ordered_ids if i in by_id]

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Skeleton built: {added} stub articles added, {skipped} already had real content (left untouched).")
    print(f"Wrote {feed_path}")


if __name__ == "__main__":
    main()
