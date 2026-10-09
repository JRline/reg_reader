#!/usr/bin/env python3
"""
Splits out parenthetical asides (and, where safe, mid-clause ただし/proviso breaks) that
were left embedded inside a coarser clause, and further analyzes what's INSIDE a
parenthetical aside for its own proviso/conditional substructure (tagged
`in_parenthetical` so the reader renders it as an underline instead of a clashing
background highlight). Pure post-processing on ALREADY-TRANSLATED text — never adds,
removes, or rewrites a single character, only moves split points — so the "concatenation
reconstructs the original exactly" invariant can't be broken by this script. No model calls.

This exists because the batch that populated Chapter 2 was, on the whole, too coarse:
many paragraphs came back as one "main" clause even when they contain a clearly bracketed
定義 aside or an embedded ただし-clause, which is exactly the structure the reader's
visual-cue feature depends on to be useful.

Usage:
    python3 refine_clauses.py <feed_id> <chapter_id>
"""
import json
import re
import sys
from pathlib import Path

FEEDS_DIR = Path(__file__).parent.parent / "feeds"

PROVISO_JA_RE = re.compile(r"(。)(ただし、.*)$", re.DOTALL)
PROVISO_EN_RE = re.compile(r"(; ?)(provided,? however,? that.*)$", re.IGNORECASE | re.DOTALL)

# A 場合/とき condition, anchored at the START of a span (the condition opens it, unlike
# a proviso which trails one) — same category the reader's own legend already defines as
# "condition (場合/とき)", so this reuses an existing, already-displayed definition rather
# than inventing a new rule.
CONDITIONAL_JA_RE = re.compile(r"^(.*?(?:場合には|場合において|場合|ときは|とき)、)", re.DOTALL)

# An exclusion, anchored at the END of a span like a proviso ("...を除く。)"), following a
# 。 boundary. Reuses PROVISO_JA_RE's exact shape/reliability, different trigger phrase.
EXCEPTION_JA_RE = re.compile(r"(。)([^。]*を除く。[)）])$", re.DOTALL)

# A parenthetical that is, in its entirety, a defining phrase for a term used just before
# it (a very standard hourei construction: "(...をいう。以下同じ。)"). Only applied when the
# whole span has no nested paren (see _outer_prefix_end) — with nesting present, "which
# part is being defined" gets ambiguous enough that a whole-clause retag risks mislabeling
# a span that ALSO contains something else (a condition, a cross-reference) as pure definition.
DEFINITION_WHOLE_JA_RE = re.compile(r"^[\(（].*をいう。(?:以下[^。]*。)?[\)）]$", re.DOTALL)

# A '(1)'/'（１）'-style clause is a level-3 list marker, not a real parenthetical aside —
# split_out_parens can't tell the two apart from paren-balance alone, so it mis-tags bare
# numeral markers as "parenthetical". Retag them; text is untouched so reconstruction can't break.
BARE_MARKER_RE = re.compile(r"^[\(（][0-9０-９]+[\)）]$")

# イロハ sub-items are sometimes left bundled inline inside one enumeration_item clause
# (e.g. "...であること。イ...ロ...ハ...") instead of each getting its own clause, because
# the original batch only split at boundaries the model happened to see. Mirrors app.js's
# detectItemMarker: a level-2 marker is only accepted as the next unused character in
# iroha order for the CURRENT nested list — but unlike the renderer (which only checks the
# START of an already-isolated clause), this scans mid-string, so a bare character-class
# match would also fire on a cross-reference like "前号イの確認" (item イ of the prior
# number). Requiring the candidate to immediately follow a 。 (i.e. sit at a real sentence/
# item boundary) rules that out while still catching genuine bundled items, which always
# follow the previous item's closing 。.
IROHA_ORDER = "イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス"
LEVEL1_RE = re.compile(r"^[一二三四五六七八九十]+(?:の[一二三四五六七八九十]+)?")


def reclassify_bare_markers(clauses: list):
    return [
        {"clause_type": "enumeration_item", "text": c["text"]}
        if c["clause_type"] == "parenthetical" and BARE_MARKER_RE.match(c["text"].strip())
        else c
        for c in clauses
    ]


def split_inline_iroha(clauses: list):
    out = []
    iroha_index = -1
    for c in clauses:
        if c["clause_type"] != "enumeration_item" or not c["text"]:
            out.append(c)
            continue
        text = c["text"]
        if LEVEL1_RE.match(text):
            iroha_index = -1
        pieces = []
        start = 0
        for i in range(1, len(text)):
            nxt = iroha_index + 1
            if nxt < len(IROHA_ORDER) and text[i] == IROHA_ORDER[nxt] and text[i - 1] == "。":
                pieces.append(text[start:i])
                start = i
                iroha_index = nxt
        pieces.append(text[start:])
        out.extend({"clause_type": "enumeration_item", "text": p} for p in pieces if p)
    return out


# English list markers mirror the Japanese three levels — 一 -> (i), イ -> (a), （１） -> (1)
# (optionally with a branch suffix like "(ii-2)") — and split_out_parens tags every one of
# them "parenthetical", same as it does for a CITATION numeral like "paragraph (1)" or
# "item (iv)". Those two need opposite treatment: a citation numeral belongs back inside
# the running text (it's part of the reference, and splitting it out also breaks ref
# matching on text_en), while a real marker belongs on the front of the item it opens so
# the reader can render it as one list entry. Context tells them apart: a citation numeral
# directly follows a citation word (or a chain like "paragraphs (1) and "), a real marker
# directly follows a sentence/list boundary (". ", ": ", "; ") or opens the paragraph.
EN_MARKER_RE = re.compile(r"^\((?:[ivxl]+|[a-z]|\d+)(?:-\d+)?\)$")
EN_CITATION_TAIL_RE = re.compile(
    r"\b(?:paragraphs?|items?|sub-items?)"
    r"(?:\s*\([^()\s]{1,8}\)(?:,|\s+and|\s+or|\s+through|\s+to)?)*\s*$",
    re.IGNORECASE,
)
EN_ITEM_BOUNDARY_RE = re.compile(r"(?:^|[.:;])\s*$")


def _is_bare_en_marker(c: dict) -> bool:
    return (
        c["clause_type"] in ("parenthetical", "enumeration_item")
        and not c.get("in_parenthetical")
        and bool(EN_MARKER_RE.match(c["text"]))
    )


def normalize_en_markers(clauses: list):
    # Pass 1: fold citation numerals back into the clause they were cut out of, re-joining
    # the continuation that split_out_parens separated from it ("paragraph " + "(1)" +
    # " of the Banking Act" -> one clause).
    merged = []
    rejoin_next = False
    for c in clauses:
        prev = merged[-1] if merged else None
        if prev and _is_bare_en_marker(c) and EN_CITATION_TAIL_RE.search(prev["text"]):
            merged[-1] = {**prev, "text": prev["text"] + c["text"]}
            rejoin_next = True
            continue
        if (
            rejoin_next and prev
            and c["clause_type"] == prev["clause_type"]
            and bool(c.get("in_parenthetical")) == bool(prev.get("in_parenthetical"))
        ):
            merged[-1] = {**prev, "text": prev["text"] + c["text"]}
            rejoin_next = False
            continue
        rejoin_next = False
        merged.append(c)

    # Pass 2: attach a real list marker to the item text right after it.
    out = []
    i = 0
    while i < len(merged):
        c = merged[i]
        at_boundary = not out or EN_ITEM_BOUNDARY_RE.search(out[-1]["text"])
        if _is_bare_en_marker(c) and at_boundary:
            nxt = merged[i + 1] if i + 1 < len(merged) else None
            if nxt and nxt["clause_type"] == "enumeration_item" and not nxt.get("in_parenthetical"):
                out.append({**nxt, "text": c["text"] + nxt["text"]})
                i += 2
                continue
            out.append({"clause_type": "enumeration_item", "text": c["text"]})
            i += 1
            continue
        out.append(c)
        i += 1
    return out


# Some clauses_en in Chapter 2 were produced from a DIFFERENT English rendering than the
# paragraph's own text_en (reordered for the cue structure, abbreviated, occasionally
# reworded — e.g. "an amount not exceeding" where text_en says "the amount"), so they fail
# the reconstruction invariant (CLAUDE.md rule 1) and the reader — which renders clauses,
# not text_en — showed the drifted wording. text_en is the reviewed translation, so the
# clauses are rebuilt from it: split at list-item boundaries, then keep any original
# cue-typed span (condition/exception/proviso/definition) that still occurs verbatim and
# uniquely in text_en, so those cues survive where the wording didn't drift.
EN_ITEM_SPLIT_RE = re.compile(r"(?<=[.:;] )(?=\((?:[ivxl]+|[a-z]|\d+)(?:-\d+)?\) )")
SALVAGE_TYPES = ("conditional", "exception", "proviso", "definition")


def resegment_en(text_en: str, old_clauses: list):
    bounds = {0, len(text_en)}
    item_starts = [m.start() for m in EN_ITEM_SPLIT_RE.finditer(text_en)]
    bounds.update(item_starts)
    typed = []  # (start, end, type)
    for c in old_clauses:
        if c["clause_type"] not in SALVAGE_TYPES or c.get("in_parenthetical"):
            continue
        needle = c["text"].strip().rstrip(",;.").strip()
        if len(needle) < 15 or text_en.count(needle) != 1:
            continue
        start = text_en.index(needle)
        end = start + len(needle)
        while end < len(text_en) and text_en[end] in ",;. ":
            end += 1
        if any(start < e and end > s for s, e, _ in typed) or any(start < b < end for b in item_starts):
            continue
        typed.append((start, end, c["clause_type"]))
        bounds.update((start, end))
    cuts = sorted(bounds)
    first_item = item_starts[0] if item_starts else len(text_en)
    out = []
    for a, b in zip(cuts, cuts[1:]):
        t = next((ty for s, e, ty in typed if s <= a and b <= e), None)
        out.append({"clause_type": t or ("enumeration_item" if a >= first_item else "main"), "text": text_en[a:b]})
    return out


def find_balanced_parens(text: str, open_ch: str, close_ch: str):
    """Top-level (not nested) balanced spans — a paren containing another paren is
    returned as ONE span covering both, matching how this reader treats nested asides."""
    spans = []
    depth = 0
    start = None
    for i, ch in enumerate(text):
        if ch == open_ch:
            if depth == 0:
                start = i
            depth += 1
        elif ch == close_ch:
            if depth > 0:
                depth -= 1
                if depth == 0 and start is not None:
                    spans.append((start, i + 1))
                    start = None
    return spans


def split_out_parens(clause_type: str, text: str, open_ch: str, close_ch: str):
    if clause_type == "parenthetical" or not text:
        return [(clause_type, text)]
    spans = find_balanced_parens(text, open_ch, close_ch)
    if not spans:
        return [(clause_type, text)]
    pieces = []
    pos = 0
    for start, end in spans:
        if start > pos:
            pieces.append((clause_type, text[pos:start]))
        pieces.append(("parenthetical", text[start:end]))
        pos = end
    if pos < len(text):
        pieces.append((clause_type, text[pos:]))
    return [(t, s) for t, s in pieces if s]  # drop empty slivers from adjacent parens


def split_out_proviso(clause_type: str, text: str, pattern: re.Pattern):
    if clause_type == "proviso":
        return [(clause_type, text)]
    m = pattern.search(text)
    if not m:
        return [(clause_type, text)]
    split_at = m.end(1)
    return [(clause_type, text[:split_at]), ("proviso", text[split_at:])]


def _outer_prefix_end(text: str) -> int:
    """Index of the first NESTED paren inside a parenthetical span's own outer wrapper
    (the span's leading '(' doesn't count as nesting). A condition/proviso search is
    bounded to end here so a non-greedy match can't stretch across an unrelated nested
    aside just because the real trigger phrase happens to sit past it — without this,
    e.g. "(...を保有している場合(...)...零を下回る場合には、Y)" would grab everything up
    to the SECOND "場合には、" as the "condition", swallowing the nested aside in between."""
    depth = 0
    for i, ch in enumerate(text):
        if ch in "(（":
            depth += 1
            if depth == 2:
                return i
        elif ch in ")）":
            depth -= 1
    return len(text)


def _depth_at(text: str, idx: int) -> int:
    """Paren depth right after processing text[:idx] — 1 means back at the parenthetical
    span's own outer level (only its own wrapping paren still open), >1 means still inside
    a nested aside. Used to reject a trailing-pattern split point that a regex found INSIDE
    a nested paren (e.g. a "。" that ends a nested definition, not the outer span) — taking
    it anyway would produce a piece with an unmatched "(", displaced from its own ")"."""
    depth = 0
    for ch in text[:idx]:
        if ch in "(（":
            depth += 1
        elif ch in ")）":
            depth -= 1
    return depth


def analyze_parenthetical(text: str, proviso_re: re.Pattern, exception_re, conditional_re):
    """A parenthetical aside can itself contain a proviso, an exclusion, or a condition
    (e.g. an aside that reads "(...but if X, then Y)"). Splitting those out lets the
    reader apply the same semantic cue it would outside the parens — but tagged
    `in_parenthetical` so the renderer draws it as a colored UNDERLINE rather than the
    type's usual background highlight, since a highlight box nested inside the
    parenthetical's own underline styling would visually clash rather than read as
    "a proviso inside an aside"."""
    # (pattern, resulting type, does the matched span become the FIRST piece?) — a
    # proviso/exception trails the text it qualifies ("X. ただし、Y" -> [X., proviso Y]),
    # while a condition opens it ("Xの場合には、Y" -> [conditional Xの場合には、, Y]).
    # Only the prefix-establishing (condition) search is bounded to before the first
    # nested paren — a non-greedy START match can otherwise stretch past an unrelated
    # nested aside to reach a later trigger phrase. A trailing ($-anchored) search has no
    # such risk: it can only ever match the span's own final sentence, wherever that is.
    detectors = ((proviso_re, "proviso", False), (exception_re, "exception", False), (conditional_re, "conditional", True))
    pieces = [("parenthetical", text)]
    for pattern, target_type, target_first in detectors:
        if pattern is None:
            continue
        next_pieces = []
        for ctype, t in pieces:
            if ctype != "parenthetical" or not t:
                next_pieces.append((ctype, t))
                continue
            search_text = t[:_outer_prefix_end(t)] if target_first else t
            m = pattern.search(search_text)
            if not m or (not target_first and _depth_at(t, m.end(1)) != 1):
                next_pieces.append((ctype, t))
                continue
            split_at = m.end(1)
            if target_first:
                next_pieces.extend([(target_type, t[:split_at]), (ctype, t[split_at:])])
            else:
                next_pieces.extend([(ctype, t[:split_at]), (target_type, t[split_at:])])
        pieces = next_pieces
    return [
        {"clause_type": t, "text": s, **({"in_parenthetical": True} if t != "parenthetical" else {})}
        for t, s in pieces if s
    ]


def reclassify_whole_definitions(clauses: list):
    out = []
    for c in clauses:
        if (
            c["clause_type"] == "parenthetical"
            and _outer_prefix_end(c["text"]) == len(c["text"])
            and DEFINITION_WHOLE_JA_RE.match(c["text"])
        ):
            out.append({"clause_type": "definition", "text": c["text"], "in_parenthetical": True})
        else:
            out.append(c)
    return out


def refine(clauses: list, lang: str):
    open_ch, close_ch = ("(", ")")
    proviso_re = PROVISO_JA_RE if lang == "ja" else PROVISO_EN_RE
    exception_re = EXCEPTION_JA_RE if lang == "ja" else None
    conditional_re = CONDITIONAL_JA_RE if lang == "ja" else None
    refined = []
    for c in clauses:
        # Already the output of analyze_parenthetical on an earlier run (e.g. a condition
        # piece "(...場合には、" whose closing paren lives in the next clause) — re-splitting
        # it can't find a balanced span, and rebuilding the dict would drop the flag, so a
        # re-run silently un-did the previous run's nested-cue tagging. Pass it through.
        if c.get("in_parenthetical"):
            refined.append(c)
            continue
        for ctype, text in split_out_parens(c["clause_type"], c["text"], open_ch, close_ch):
            if ctype == "parenthetical":
                refined.extend(analyze_parenthetical(text, proviso_re, exception_re, conditional_re))
            else:
                refined.extend(
                    {"clause_type": t, "text": s}
                    for t, s in split_out_proviso(ctype, text, proviso_re)
                )
    return refined


def walk(node):
    yield node
    for c in node.get("children", []):
        yield from walk(c)


def main():
    if len(sys.argv) != 3:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id = sys.argv[1:3]

    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)

    paragraphs_touched = 0
    clauses_before = clauses_after = 0
    reconstruction_failures = []
    resegmented = []

    for art in chapter["children"]:
        for node in walk(art):
            if node.get("type") != "paragraph":
                continue
            for lang in ("ja", "en"):
                key = f"clauses_{lang}"
                text_key = f"text_{lang}"
                old = node.get(key, [])
                if not old:
                    continue
                if lang == "en" and "".join(c["text"] for c in old) != node.get(text_key, ""):
                    old_for_refine = resegment_en(node[text_key], old)
                    resegmented.append(node["id"])
                else:
                    old_for_refine = old
                new = reclassify_bare_markers(refine(old_for_refine, lang))
                if lang == "en":
                    new = normalize_en_markers(new)
                if lang == "ja":
                    new = split_inline_iroha(new)
                    new = reclassify_whole_definitions(new)
                if new == old:
                    continue
                # Safety check before committing: must still reconstruct exactly.
                if "".join(c["text"] for c in new) != node.get(text_key, ""):
                    reconstruction_failures.append(node["id"])
                    continue
                clauses_before += len(old)
                clauses_after += len(new)
                node[key] = new
                paragraphs_touched += 1

    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Refined {paragraphs_touched} clause lists across the chapter.")
    print(f"Clause count: {clauses_before} -> {clauses_after}")
    if resegmented:
        print(f"Rebuilt clauses_en from text_en on {len(resegmented)} node(s) whose clauses had drifted from it:")
        print(f"  {resegmented}")
    if reconstruction_failures:
        print(f"SAFETY ABORT on {len(reconstruction_failures)} node(s) — reconstruction would've broken, left untouched:")
        print(f"  {reconstruction_failures}")
    print(f"\nWrote {feed_path}")


if __name__ == "__main__":
    main()
