#!/usr/bin/env python3
"""
Extracts a chapter's articles from the source PDF into clean per-paragraph text,
ready for make_prompts.py to turn into chatbot_template.md prompts.

This is the mechanical, deterministic half of content prep — no chatbot involved.
Reusable for any chapter of any similarly-formatted regulation, not just this one.

Usage:
    python3 extract_chapter.py <pdf_path> <chapter_start_marker> <chapter_end_marker> <out.json>

Example:
    python3 extract_chapter.py pipeline/source/saishu1.pdf "第二章　算式等" "第三章　信用リスクの標準的手法" pipeline/source/ch2_articles.json

    (Use the exact chapter-heading line as printed at the START of the chapter body —
    not the table-of-contents line, which has an extra "（第二条―第十三条）" suffix and
    will match too early. Pass whatever's on the body heading line, full-width spaces
    included, exactly as pypdf extracts it — check by grepping the raw dump if unsure.)
"""
import json
import re
import sys
from pathlib import Path

from pypdf import PdfReader

ARTICLE_NUM_RE = re.compile(r"^第[一二三四五六七八九十百]+条(の[一二三四五六七八九十]+)?[ 　]")
HEADING_RE = re.compile(r"^\(.+\)$")
PAGE_MARKER_RE = re.compile(r"^=+PAGE \d+=+$")
PAGE_NUM_RE = re.compile(r"^\d+\s*/\s*\d+$")
PARAGRAPH_NUM_RE = re.compile(r"^([２-９](?:[０-９])?)[ 　]")  # e.g. "２　前項の..." -> paragraph 2 starts here

FULLWIDTH_DIGITS = "０１２３４５６７８９"
ARABIC_DIGITS = "0123456789"
TO_ARABIC = str.maketrans(FULLWIDTH_DIGITS, ARABIC_DIGITS)


def extract_full_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def light_clean(line: str) -> str:
    """Strip only leading/trailing whitespace — keep internal spaces, since paragraph/
    article number markers (e.g. '２　前項の...') depend on the space right after the
    number to be detected. Internal spaces get stripped later, once markers are consumed."""
    return line.strip()


def heavy_clean(text: str) -> str:
    """Japanese legal text uses no spaces, so any space remaining after paragraph/item
    splitting is a PDF line-wrap artifact — strip it all."""
    return text.replace(" ", "").replace("　", "")


def split_chapter_into_articles(lines: list, start_idx: int, end_idx: int):
    """Returns [(number, heading_or_None, body_lines)] — body_lines are light-cleaned only."""
    articles = []
    pending_heading = None
    current_number = None
    current_heading = None
    current_body = []

    def flush():
        if current_number is not None:
            articles.append((current_number, current_heading, current_body[:]))

    for raw in lines[start_idx:end_idx]:
        s = light_clean(raw)
        if not s or PAGE_MARKER_RE.match(s) or PAGE_NUM_RE.match(s):
            continue
        if HEADING_RE.match(s):
            pending_heading = s.strip("()")
            continue
        m = ARTICLE_NUM_RE.match(s)
        if m:
            flush()
            current_number = s[: m.end() - 1]  # exclude the trailing separator space
            current_heading = pending_heading
            pending_heading = None
            rest = s[m.end():].strip()
            current_body = [rest] if rest else []
            continue
        if current_number is not None:
            current_body.append(s)
    flush()
    return articles


def split_into_paragraphs(body_lines: list):
    """First paragraph is unnumbered; subsequent ones start where a line begins with a
    full-width-digit paragraph marker followed by a space."""
    paragraphs = []
    current_number = None
    current_lines = []

    def flush():
        text = heavy_clean("".join(current_lines)).strip()
        if text:
            paragraphs.append((current_number, text))

    for line in body_lines:
        m = PARAGRAPH_NUM_RE.match(line)
        if m:
            flush()
            current_number = m.group(1)
            current_lines = [line[m.end():]]
        else:
            current_lines.append(line)
    flush()
    return paragraphs


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    pdf_path, start_marker, end_marker, out_path = sys.argv[1:5]

    full_text = extract_full_text(pdf_path)
    lines = full_text.split("\n")

    # Skip the first occurrence (table of contents) by requiring an exact, bare match —
    # ToC lines carry a "（第二条―第十三条）" style suffix that a bare marker won't equal.
    start_idx = next(i for i, l in enumerate(lines) if l.strip() == start_marker)
    end_idx = next(i for i, l in enumerate(lines) if i > start_idx and l.strip() == end_marker)

    articles = split_chapter_into_articles(lines, start_idx, end_idx)

    out = []
    for number, heading, body_lines in articles:
        paragraphs = split_into_paragraphs(body_lines)
        out.append({
            "number": number,
            "heading": heading,
            "paragraphs": [{"number": n, "text": t} for n, t in paragraphs],
        })

    Path(out_path).write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Extracted {len(out)} articles, {sum(len(a['paragraphs']) for a in out)} paragraphs total.")
    print(f"Wrote {out_path}")


if __name__ == "__main__":
    main()
