#!/usr/bin/env python3
"""
Re-resolves internal references across an ALREADY-INGESTED feed, using the full document
tree as context. Pure post-processing — touches only ref target_ids/target_feed/
resolution_status, never text_ja/text_en/clauses. No model calls, no re-translation.

Why this exists as a separate pass rather than being part of ingest.py's per-article
flow: ingest.py builds one article at a time and only ever had visibility into that
article's own paragraphs, so it could only resolve relative refs like 前項/前二項. Once
every article in a chapter is loaded (as they now are), absolute citations like
"第五条第二項" or "前三条" become resolvable too — but only with a view of the whole
chapter, which this script has and per-article ingestion doesn't.

Usage:
    python3 reresolve_refs.py <feed_id> <chapter_id>

Example:
    python3 reresolve_refs.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2
"""
import json
import re
import sys
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"

KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
FULLWIDTH_DIGITS = "０１２３４５６７８９"
ARABIC_DIGITS = "0123456789"
TO_ARABIC = str.maketrans(FULLWIDTH_DIGITS, ARABIC_DIGITS)


def kanji_to_int(s: str) -> int:
    if not s:
        return 0
    if "十" in s:
        tens_part, _, ones_part = s.partition("十")
        tens = KANJI_DIGITS.get(tens_part, 1) if tens_part else 1
        ones = KANJI_DIGITS.get(ones_part, 0) if ones_part else 0
        return tens * 10 + ones
    return KANJI_DIGITS.get(s, 0)


def paragraph_number_to_int(number: str) -> int:
    """Paragraph 'number' field is None for the first (unnumbered) paragraph, else a
    full-width-digit string like '２', '１０' as printed in the source."""
    if number is None:
        return 1
    return int(number.translate(TO_ARABIC))


# Ordered by specificity — checked in this order, first match wins.
REL_PARAGRAPH_RE = re.compile(r"^前(二)?項")
NEXT_PARAGRAPH_RE = re.compile(r"^次(二)?項")
REL_ARTICLE_RE = re.compile(r"^前([二三四五六七八九十]?)条")
NEXT_ARTICLE_RE = re.compile(r"^次([二三四五六七八九十]?)条")
SAME_ARTICLE_RE = re.compile(r"^同条(第(?P<para>[一二三四五六七八九十百]+)項)?")
ABS_CITATION_RE = re.compile(
    r"^第(?P<art>[一二三四五六七八九十百]+)条(の(?P<artsub>[一二三四五六七八九十]+))?"
    r"(第(?P<para>[一二三四五六七八九十百]+)項)?"
)
ABS_PARAGRAPH_ONLY_RE = re.compile(r"^第(?P<para>[一二三四五六七八九十百]+)項")
SAME_PARAGRAPH_RE = re.compile(r"^同項")
CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百]+章")


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


def build_context(chapter: dict):
    article_ids_ordered = [a["id"] for a in chapter["children"]]
    article_number_to_id = {a["number"]: a["id"] for a in chapter["children"] if a.get("number")}
    paragraphs_by_article = {}
    parent_article_of = {}
    for art in chapter["children"]:
        para_ids = [p["id"] for p in art["children"] if p.get("type") == "paragraph"]
        paragraphs_by_article[art["id"]] = para_ids
        for p in art["children"]:
            if p.get("type") == "paragraph":
                parent_article_of[p["id"]] = art["id"]
    return {
        "article_ids_ordered": article_ids_ordered,
        "article_number_to_id": article_number_to_id,
        "paragraphs_by_article": paragraphs_by_article,
        "parent_article_of": parent_article_of,
    }


def resolve(raw_text: str, current_paragraph_id: str, ctx: dict, last_para_target: list):
    """Returns (status, target_ids). status in resolved/internal_unavailable/None(=leave as-is)."""
    current_article_id = ctx["parent_article_of"][current_paragraph_id]
    para_siblings = ctx["paragraphs_by_article"][current_article_id]
    para_index = para_siblings.index(current_paragraph_id)

    m = REL_PARAGRAPH_RE.match(raw_text)
    if m:
        count = 2 if m.group(1) else 1
        if para_index - count < 0:
            return "internal_unavailable", []  # would cross into the preceding article
        targets = para_siblings[para_index - count: para_index]
        last_para_target[0] = targets[-1]
        return "resolved", targets

    m = NEXT_PARAGRAPH_RE.match(raw_text)
    if m:
        count = 2 if m.group(1) else 1
        end = para_index + 1 + count
        if end > len(para_siblings):
            return "internal_unavailable", []  # would cross into the following article
        targets = para_siblings[para_index + 1: end]
        last_para_target[0] = targets[-1]
        return "resolved", targets

    m = REL_ARTICLE_RE.match(raw_text)
    if m:
        count = kanji_to_int(m.group(1)) if m.group(1) else 1
        art_index = ctx["article_ids_ordered"].index(current_article_id)
        if art_index - count < 0:
            return "internal_unavailable", []
        return "resolved", ctx["article_ids_ordered"][art_index - count: art_index]

    m = NEXT_ARTICLE_RE.match(raw_text)
    if m:
        count = kanji_to_int(m.group(1)) if m.group(1) else 1
        art_index = ctx["article_ids_ordered"].index(current_article_id)
        end = art_index + 1 + count
        if end > len(ctx["article_ids_ordered"]):
            return "internal_unavailable", []
        return "resolved", ctx["article_ids_ordered"][art_index + 1: end]

    m = SAME_ARTICLE_RE.match(raw_text)
    if m:
        if m.group("para"):
            n = kanji_to_int(m.group("para"))
            if 1 <= n <= len(para_siblings):
                last_para_target[0] = para_siblings[n - 1]
                return "resolved", [para_siblings[n - 1]]
            return "internal_unavailable", []
        return "resolved", [current_article_id]  # bare 同条, or 同条+item with no paragraph — best available granularity

    m = ABS_CITATION_RE.match(raw_text)
    if m:
        art_number_str = f"第{m.group('art')}条" + (f"の{m.group('artsub')}" if m.group("artsub") else "")
        target_article_id = ctx["article_number_to_id"].get(art_number_str)
        if not target_article_id:
            return "internal_unavailable", []
        if m.group("para"):
            n = kanji_to_int(m.group("para"))
            target_paras = ctx["paragraphs_by_article"].get(target_article_id, [])
            if 1 <= n <= len(target_paras):
                last_para_target[0] = target_paras[n - 1]
                return "resolved", [target_paras[n - 1]]
            return "internal_unavailable", [target_article_id]  # article exists, that paragraph doesn't (yet)
        return "resolved", [target_article_id]

    m = ABS_PARAGRAPH_ONLY_RE.match(raw_text)
    if m:
        n = kanji_to_int(m.group("para"))
        if 1 <= n <= len(para_siblings):
            last_para_target[0] = para_siblings[n - 1]
            return "resolved", [para_siblings[n - 1]]
        return "internal_unavailable", []

    if SAME_PARAGRAPH_RE.match(raw_text) and last_para_target[0]:
        return "resolved", [last_para_target[0]]

    if CHAPTER_RE.match(raw_text):
        # Only one chapter is loaded in this feed right now, so any citation to "第◯章"
        # is necessarily to a chapter we don't have — valid citation, unloaded target.
        return "internal_unavailable", []

    return None, None  # unparseable with current patterns — leave whatever it had


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id = sys.argv[1:3]

    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)
    ctx = build_context(chapter)

    stats = {"newly_resolved": 0, "internal_unavailable": 0, "still_unresolved": 0, "left_alone": 0}
    still_unresolved_samples = []

    for art in chapter["children"]:
        for node in walk(art):
            if node.get("type") != "paragraph":
                continue
            last_para_target = [None]
            for r in node.get("refs", []):
                if r.get("scope") != "internal":
                    continue
                status, target_ids = resolve(r["raw_text"], node["id"], ctx, last_para_target)
                if status is None:
                    if r.get("resolution_status") == "unresolved":
                        stats["still_unresolved"] += 1
                        if len(still_unresolved_samples) < 20:
                            still_unresolved_samples.append((node["id"], r["raw_text"]))
                    else:
                        stats["left_alone"] += 1
                    continue
                was_unresolved = r.get("resolution_status") != "resolved"
                r["resolution_status"] = status
                r["target_ids"] = target_ids
                r["target_feed"] = feed_id if status == "resolved" else None
                if status == "resolved" and was_unresolved:
                    stats["newly_resolved"] += 1
                elif status == "internal_unavailable":
                    stats["internal_unavailable"] += 1

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Newly resolved: {stats['newly_resolved']}")
    print(f"Marked internal_unavailable (valid citation, target not loaded): {stats['internal_unavailable']}")
    print(f"Still unresolved (pattern not recognized, e.g. item-level 前号/第◯号 alone): {stats['still_unresolved']}")
    if still_unresolved_samples:
        print("Samples of still-unresolved (for judging whether more patterns are worth adding):")
        for node_id, raw_text in still_unresolved_samples:
            print(f"  [{node_id}] \"{raw_text}\"")
    print(f"\nWrote {feed_path}")


if __name__ == "__main__":
    main()
