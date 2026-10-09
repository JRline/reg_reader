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
    if "百" in s:  # Article 128 etc. (Chapter 3 onward cites three-digit articles)
        hundreds, _, rest = s.partition("百")
        return (KANJI_DIGITS.get(hundreds, 1) if hundreds else 1) * 100 + kanji_to_int(rest)
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
REL_PARAGRAPH_RE = re.compile(r"^前([二三四五六七八九]|各)?項")
NEXT_PARAGRAPH_RE = re.compile(r"^次(二)?項")
REL_ARTICLE_RE = re.compile(r"^前([二三四五六七八九十]?)条")
NEXT_ARTICLE_RE = re.compile(r"^次([二三四五六七八九十]?)条")
SAME_ARTICLE_RE = re.compile(r"^同条(第(?P<para>[一二三四五六七八九十百]+)項)?")
ABS_CITATION_RE = re.compile(
    r"^第(?P<art>[一二三四五六七八九十百]+)条(?P<artsub>(?:の[一二三四五六七八九十]+)*)"
    r"(第(?P<para>[一二三四五六七八九十百]+)項)?"
)
ABS_PARAGRAPH_ONLY_RE = re.compile(r"^第(?P<para>[一二三四五六七八九十百]+)項")
SAME_PARAGRAPH_RE = re.compile(r"^同項")
CHAPTER_RE = re.compile(r"^第[一二三四五六七八九十百]+章(?:の[一二三四五六七八九十]+)*")
# 第六節 / 第六節第三款 / 第三款第二目 … (a section path, optionally after a chapter)
UNIT_PATH_RE = re.compile(r"(第[一二三四五六七八九十]+[節款目])")


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


def build_context(root: dict):
    """Context over the WHOLE feed: article numbers are unique across a notification, so a
    Chapter 3 citation to 第二条 resolves into Chapter 2, and articles inside 節/款/目
    groupings are found wherever they sit."""
    article_ids_ordered, article_number_to_id = [], {}
    paragraphs_by_article, parent_article_of, chapter_of = {}, {}, {}
    chapter_by_number = {}
    parent_of = {}
    for n in walk(root):
        for c in n.get("children", []):
            parent_of[c["id"]] = n
    for chapter in root.get("children", []):
        if chapter.get("type") == "chapter" and chapter.get("number"):
            chapter_by_number[chapter["number"]] = chapter
        for art in walk(chapter):
            if art.get("type") != "article":
                continue
            article_ids_ordered.append(art["id"])
            # 附則 blocks (a chapter with no number) repeat article numbers; they never
            # answer a bare 第N条 citation.
            if art.get("number") and chapter.get("number"):
                article_number_to_id[art["number"]] = art["id"]
            chapter_of[art["id"]] = chapter
            para_ids = [p["id"] for p in art.get("children", []) if p.get("type") == "paragraph"]
            paragraphs_by_article[art["id"]] = para_ids
            for pid in para_ids:
                parent_article_of[pid] = art["id"]
    return {
        "article_ids_ordered": article_ids_ordered,
        "article_number_to_id": article_number_to_id,
        "paragraphs_by_article": paragraphs_by_article,
        "parent_article_of": parent_article_of,
        "chapter_of": chapter_of,
        "chapter_by_number": chapter_by_number,
        "parent_of": parent_of,
    }


UNIT_LEVEL = {"節": "section", "款": "subsection", "目": "division"}
UNIT_PARENT_LEVEL = {"節": "chapter", "款": "section", "目": "subsection"}
# 前款第七目 / 次節 …: the unit path is relative to a sibling of the enclosing unit.
UNIT_PREFIX_RE = re.compile(r"(前|次|同)([節款目])$")


def _unit_scope(current_article_id: str, first_unit: str, prefix: str, ctx: dict):
    """The node whose children a bare 款/目-led path (no chapter named) is numbered among:
    the enclosing 節 for 第N款, the enclosing 款 for 第N目 — or, after 前款/前節, the
    previous sibling of that enclosing unit (次 = next, 同 = the enclosing one itself)."""
    level = UNIT_PARENT_LEVEL[first_unit]
    parent_of = ctx["parent_of"]
    node = parent_of.get(current_article_id)
    if prefix:
        rel, rel_unit = prefix[0], prefix[1]
        # The prefix names the unit the path starts in (前款第七目: 款), so climb to that.
        level = UNIT_LEVEL[rel_unit]
    while node is not None and node.get("type") != level:
        node = parent_of.get(node["id"])
    if node is None or not prefix or prefix[0] == "同":
        return node
    siblings = [c for c in parent_of[node["id"]].get("children", []) if c.get("type") == level]
    i = siblings.index(node) + (-1 if prefix[0] == "前" else 1)
    return siblings[i] if 0 <= i < len(siblings) else None


def resolve(raw_text: str, current_paragraph_id: str, ctx: dict, last_para_target: list,
            unit_prefix: str | None = None):
    """Returns (status, target_ids). status in resolved/internal_unavailable/None(=leave as-is)."""
    current_article_id = ctx["parent_article_of"][current_paragraph_id]
    para_siblings = ctx["paragraphs_by_article"][current_article_id]
    para_index = para_siblings.index(current_paragraph_id)

    m = REL_PARAGRAPH_RE.match(raw_text)
    if m:
        count = para_index if m.group(1) == "各" else (kanji_to_int(m.group(1)) if m.group(1) else 1)
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
        last_para_target[1] = ctx["article_ids_ordered"][art_index - 1]
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
        # 同条 = the article cited most recently in this paragraph (drafting convention), else
        # the article the text is in. If that earlier citation was to another law, or to an
        # article we don't have, we can't say what 同条 is.
        same_id = last_para_target[1] or current_article_id
        if same_id in ("EXTERNAL", "UNAVAILABLE"):
            return "internal_unavailable", []
        same_paras = ctx["paragraphs_by_article"].get(same_id, [])
        if m.group("para"):
            n = kanji_to_int(m.group("para"))
            if 1 <= n <= len(same_paras):
                last_para_target[0] = same_paras[n - 1]
                return "resolved", [same_paras[n - 1]]
            return "internal_unavailable", []
        return "resolved", [same_id]  # bare 同条, or 同条+item with no paragraph — best available granularity

    m = ABS_CITATION_RE.match(raw_text)
    if m:
        art_number_str = f"第{m.group('art')}条" + (m.group("artsub") or "")
        target_article_id = ctx["article_number_to_id"].get(art_number_str)
        if not target_article_id:
            last_para_target[1] = "UNAVAILABLE"
            return "internal_unavailable", []
        last_para_target[1] = target_article_id
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

    m = CHAPTER_RE.match(raw_text)
    if m or UNIT_PATH_RE.match(raw_text):
        # 第三章 / 第六節第三款第二目: resolve to that structural node if it's loaded —
        # a chapter by number across the feed, a section path inside the cited chapter
        # (or the current one when no chapter is named).
        units = UNIT_PATH_RE.findall(raw_text[m.end():] if m else raw_text)
        if m:
            scope = ctx["chapter_by_number"].get(m.group(0))
        elif units and (units[0][-1] != "節" or unit_prefix):
            if unit_prefix == "":
                # The same raw_text occurs both bare and after 前/次 — can't tell which
                # occurrence this ref is; don't guess.
                return "internal_unavailable", []
            scope = _unit_scope(current_article_id, units[0][-1], unit_prefix, ctx)
        else:
            scope = ctx["chapter_of"].get(current_article_id)
        if scope is None:
            return "internal_unavailable", []
        node = scope
        for unit in units:
            node = next((c for c in node.get("children", []) if c.get("number") == unit and c.get("type") in ("section", "subsection", "division")), None)
            if node is None:
                return "internal_unavailable", []
        return "resolved", [node["id"]]

    return None, None  # unparseable with current patterns — leave whatever it had


def _block_of(node_id: str, ctx: dict):
    n = ctx["parent_of"].get(node_id)
    while n is not None and n.get("type") != "section":
        n = ctx["parent_of"].get(n["id"])
    return n


def occurrence_before(raw_text: str, text_ja: str, nth: int, width: int = 3) -> str:
    """The `width` characters just before the nth occurrence of raw_text in text_ja."""
    pos = -1
    for _ in range(nth + 1):
        pos = text_ja.find(raw_text, pos + 1)
        if pos == -1:
            return ""
    return text_ja[max(0, pos - width):pos]


def resolve_fusoku(raw_text, node, before, ctx, last_para_target):
    """Citations inside a 附則 block. Article numbers repeat from block to block and the
    amending notices' own bare citations (第五条の規定による改正後の…) point into notices that
    are not in this feed, so only the unambiguous cases resolve:
      附則第N条…      -> that article of the SAME block
      新告示第N条…    -> the notification's body (新告示 = the notification as amended)
      前条/同項 …     -> only if the target is in the same block
      bare 第N条…     -> the body, but only in the notification's own original 附則 (block s00)
      旧告示 / other bare citations in amending blocks -> left unresolved."""
    block = _block_of(node["id"], ctx)
    if before.endswith("附則"):
        m = ABS_CITATION_RE.match(raw_text)
        if not m or block is None:
            return "internal_unavailable", []
        number = f"第{m.group('art')}条" + (m.group("artsub") or "")
        art = next((c for c in block.get("children", []) if c.get("number") == number), None)
        if not art:
            last_para_target[1] = "UNAVAILABLE"
            return "internal_unavailable", []
        last_para_target[1] = art["id"]
        paras = [c for c in art.get("children", []) if c.get("type") == "paragraph"]
        if m.group("para"):
            n = kanji_to_int(m.group("para"))
            if 1 <= n <= len(paras):
                return "resolved", [paras[n - 1]["id"]]
            return "internal_unavailable", [art["id"]]
        return "resolved", [art["id"]]
    if before.endswith("旧告示"):
        return "unresolved", []
    relative = raw_text[:1] in "前次同"
    is_new = before.endswith("新告示")
    if not (relative or is_new or (block and block["id"].endswith(".s00"))):
        return "unresolved", []
    status, targets = resolve(raw_text, node["id"], ctx, last_para_target)
    if status is None:
        return None, None
    if relative and status == "resolved":
        if any(_block_of(t, ctx) is not block for t in targets):
            return "internal_unavailable", []
    return status, targets


def unit_prefix_of(raw_text: str, text_ja: str):
    """For a 節/款/目-led citation: the 前款/次節/同款-style word right before it in the text
    (None = every occurrence is bare; "" = occurrences disagree)."""
    if not UNIT_PATH_RE.match(raw_text):
        return None
    prefixes = set()
    start = text_ja.find(raw_text)
    while start != -1:
        pm = UNIT_PREFIX_RE.search(text_ja[max(0, start - 2):start])
        prefixes.add(pm.group(0) if pm else None)
        start = text_ja.find(raw_text, start + 1)
    if len(prefixes) > 1:
        return ""
    return prefixes.pop() if prefixes else None


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id = sys.argv[1:3]

    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)
    ctx = build_context(feed["root"])

    stats = {"newly_resolved": 0, "internal_unavailable": 0, "still_unresolved": 0, "left_alone": 0}
    still_unresolved_samples = []

    for art in [n for n in walk(chapter) if n.get("type") == "article"]:
        for node in walk(art):
            if node.get("type") != "paragraph":
                continue
            last_para_target = [None, None]  # [last paragraph cited, last article cited]
            seen = {}
            for r in node.get("refs", []):
                if r.get("scope") != "internal":
                    last_para_target[1] = "EXTERNAL"  # a following 同条/同項 would mean that law's article
                    last_para_target[0] = None
                    continue
                nth = seen.get(r["raw_text"], 0)
                seen[r["raw_text"]] = nth + 1
                if chapter.get("number") is None:
                    before = occurrence_before(r["raw_text"], node.get("text_ja", ""), nth)
                    status, target_ids = resolve_fusoku(r["raw_text"], node, before, ctx, last_para_target)
                else:
                    status, target_ids = resolve(r["raw_text"], node["id"], ctx, last_para_target,
                                                 unit_prefix_of(r["raw_text"], node.get("text_ja", "")))
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
