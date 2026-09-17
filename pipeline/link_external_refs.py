#!/usr/bin/env python3
"""
Links external refs to content that's ALREADY been digitized in another feed (e.g.
jp-mof-consolidated-fs-regulation), which Sonnet's per-paragraph output can't know about
since each chunk is processed in isolation. Pure post-processing, no model calls, no
new PDF fetching — this only connects citations to feeds that already exist.

Usage:
    python3 link_external_refs.py <feed_id> <chapter_id>
"""
import json
import re
import sys
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"

# Extend as more external feeds get built. Longest names first so a short-name variant
# doesn't shadow a longer one that also matches as a prefix.
LAW_NAME_TO_FEED = {
    "連結財務諸表の用語、様式及び作成方法に関する規則": "jp-mof-consolidated-fs-regulation",
    "連結財務諸表規則": "jp-mof-consolidated-fs-regulation",
    "銀行法": "jp-banking-act",
    "金融商品取引法施行令": "jp-fiea-enforcement-order",
    "金融商品取引法": "jp-fiea",
    "資金決済に関する法律": "jp-payment-services-act",
    "最終指定親会社TLAC告示": "jp-tlac-notification",
}

KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}
FULLWIDTH_DIGITS = "０１２３４５６７８９"
ARABIC_DIGITS = "0123456789"
TO_ARABIC = str.maketrans(FULLWIDTH_DIGITS, ARABIC_DIGITS)


def paragraph_number_to_int(number) -> int:
    """Paragraph 'number' fields are full-width-digit strings ('２４') as printed in the
    source, or None for the unnumbered first paragraph (= paragraph 1)."""
    if number is None:
        return 1
    return int(number.translate(TO_ARABIC))


def kanji_to_int(s: str) -> int:
    if not s:
        return 0
    if "十" in s:
        tens_part, _, ones_part = s.partition("十")
        tens = KANJI_DIGITS.get(tens_part, 1) if tens_part else 1
        ones = KANJI_DIGITS.get(ones_part, 0) if ones_part else 0
        return tens * 10 + ones
    return KANJI_DIGITS.get(s, 0)


CITATION_RE = re.compile(
    r"第(?P<art>[一二三四五六七八九十百]+)条"
    r"(の(?P<artsub>[一二三四五六七八九十]+))?(の(?P<artsub2>[一二三四五六七八九十]+))?"
    r"(第(?P<para>[一二三四五六七八九十百]+)項)?"
)


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


_feed_cache = {}


def load_external_feed(feed_id: str):
    if feed_id not in _feed_cache:
        path = FEEDS_DIR / feed_id / "feed.json"
        if not path.exists():
            _feed_cache[feed_id] = None
        else:
            feed = json.loads(path.read_text(encoding="utf-8"))
            articles = [n for n in feed["root"]["children"] if n.get("type") == "article"]
            number_to_id = {a["number"]: a["id"] for a in articles if a.get("number")}
            # Keyed by the paragraph's OWN printed number (not position) — these excerpt
            # feeds are sparse (e.g. only paragraph 24 of an article might be digitized),
            # so "the 24th child" is not the same thing as "paragraph number 24".
            paragraphs_by_article = {
                a["id"]: {
                    paragraph_number_to_int(p.get("number")): p["id"]
                    for p in a["children"] if p.get("type") == "paragraph"
                }
                for a in articles
            }
            _feed_cache[feed_id] = {"number_to_id": number_to_id, "paragraphs_by_article": paragraphs_by_article}
    return _feed_cache[feed_id]


def try_link(ref: dict):
    name = ref.get("external_name")
    if not name:
        return False
    matched_prefix = next((n for n in LAW_NAME_TO_FEED if name == n or ref["raw_text"].startswith(n)), None)
    if not matched_prefix:
        return False
    target_feed_id = LAW_NAME_TO_FEED[matched_prefix]
    ext = load_external_feed(target_feed_id)
    if not ext:
        return False

    remainder = ref["raw_text"][len(matched_prefix):] if ref["raw_text"].startswith(matched_prefix) else ref["raw_text"]
    # search, not match: raw_text sometimes uses a one-character shorthand ("令" for an
    # enforcement order, "法" for the parent Act) instead of the full name we matched on,
    # so the citation itself may not start at position 0 of the remainder.
    m = CITATION_RE.search(remainder)
    if not m:
        return False
    art_number = (
        f"第{m.group('art')}条"
        + (f"の{m.group('artsub')}" if m.group("artsub") else "")
        + (f"の{m.group('artsub2')}" if m.group("artsub2") else "")
    )
    target_article_id = ext["number_to_id"].get(art_number)
    if not target_article_id:
        return False

    if m.group("para"):
        n = kanji_to_int(m.group("para"))
        paras = ext["paragraphs_by_article"].get(target_article_id, {})
        if n in paras:
            ref["target_ids"] = [paras[n]]
        else:
            return False
    else:
        ref["target_ids"] = [target_article_id]

    ref["target_feed"] = target_feed_id
    ref["resolution_status"] = "resolved"
    return True


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id = sys.argv[1:3]

    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)

    linked = 0
    still_unavailable = []
    for art in chapter["children"]:
        for node in walk(art):
            if node.get("type") != "paragraph":
                continue
            for r in node.get("refs", []):
                if r.get("scope") != "external" or r.get("resolution_status") == "resolved":
                    continue
                if try_link(r):
                    linked += 1
                else:
                    still_unavailable.append((node["id"], r["raw_text"], r.get("external_name")))

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Newly linked to already-digitized external content: {linked}")
    print(f"Still not available ({len(still_unavailable)}) — would need new fetching from e-Gov:")
    for node_id, raw_text, name in still_unavailable:
        print(f"  [{node_id}] \"{raw_text}\" (law: {name})")
    print(f"\nWrote {feed_path}")


if __name__ == "__main__":
    main()
