#!/usr/bin/env python3
"""
Splits out parenthetical asides (and, where safe, mid-clause ただし/proviso breaks) that
were left embedded inside a coarser clause. Pure post-processing on ALREADY-TRANSLATED
text — never adds, removes, or rewrites a single character, only moves split points — so
the "concatenation reconstructs the original exactly" invariant can't be broken by this
script. No model calls.

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


def refine(clauses: list, lang: str):
    open_ch, close_ch = ("(", ")")
    proviso_re = PROVISO_JA_RE if lang == "ja" else PROVISO_EN_RE
    refined = []
    for c in clauses:
        for ctype, text in split_out_parens(c["clause_type"], c["text"], open_ch, close_ch):
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
                new = refine(old, lang)
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
    if reconstruction_failures:
        print(f"SAFETY ABORT on {len(reconstruction_failures)} node(s) — reconstruction would've broken, left untouched:")
        print(f"  {reconstruction_failures}")
    print(f"\nWrote {feed_path}")


if __name__ == "__main__":
    main()
