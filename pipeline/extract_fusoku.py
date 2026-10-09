#!/usr/bin/env python3
"""
Extracts the 附則 (supplementary provisions of the original notification, then of each amending
notice, plus the 改正文 application clauses) that follow Chapter 7 in the source PDF.

Their article numbers repeat from block to block (every notice has a 第一条), so each block
becomes its own group and every entry carries a unique `key` ("s03.art2", "s07.u1" for text with
no article number). build_chapter.py keys translations and node ids on `key`.

Output matches extract_chapter_v2.py's shape, plus `"nested_ids": true` and, per entry,
`key`; a path element is {"level": 1, "number": null, "heading": <block title>, "key": "s03"}.
Usage: python3 pipeline/extract_fusoku.py pipeline/source/saishu1.pdf pipeline/source/fusoku_v2.json
"""
import json
import re
import sys
from pathlib import Path

import pdfplumber

sys.path.insert(0, str(Path(__file__).parent))
import extract_chapter_v2 as X  # noqa: E402
import ja_refs  # noqa: E402

FIRST_PAGE, LAST_PAGE = 428, 449
BLOCK_RE = re.compile(r"^(附則|改正文)(\((?P<n>.+?)\))?(?P<ex>抄)?$")


def para_split(lines, first_numbered):
    paragraphs, cur_num, cur_lines = [], None, []
    for ln in lines:
        m = X.PARAGRAPH_NUM_RE.match(ln) or (first_numbered and not paragraphs and not cur_lines and re.match(r"^(１)[ 　]", ln))
        if m:
            if cur_lines:
                paragraphs.append((cur_num, cur_lines))
            cur_num, cur_lines = m.group(1), [ln[m.end():]]
        else:
            cur_lines.append(ln)
    if cur_lines:
        paragraphs.append((cur_num, cur_lines))
    out = []
    for num, ls in paragraphs:
        segs = X.segment_paragraph(ls)
        text = "".join(s["text"] for s in segs)
        if text:
            out.append({"number": num, "text": text, "segments": segs})
    return out


def main():
    pdf = pdfplumber.open(sys.argv[1])
    tables, images, lines = [], [], []
    for pno in range(FIRST_PAGE, LAST_PAGE + 1):
        for ln in X.page_lines(pdf.pages[pno - 1], pno, tables, images):
            lines.append(ln.strip())
    lines = [l for l in lines if l and not X.PAGE_NUM_RE.match(l)]
    start = next(i for i, l in enumerate(lines) if re.sub(r"\s", "", l) == "附則")
    end = max(i for i, l in enumerate(lines) if l.startswith("別表第一("))
    body = lines[start:end]
    tables, body = X.merge_split_tables(tables, body)

    blocks = []  # {title, kind, ex, entries: [{number, heading, lines, deleted}]}
    pending_heading = None
    i = 0
    while i < len(body):
        s = body[i]
        bm = BLOCK_RE.match(re.sub(r"\s", "", s)) if s[:1] in "附改" else None
        if bm:
            blocks.append({"kind": bm.group(1), "notice": bm.group("n"), "ex": bool(bm.group("ex")), "entries": []})
            pending_heading = None
            i += 1
            continue
        blk = blocks[-1]
        if X.HEADING_RE.match(s):
            pending_heading = s.strip("()（）")
            i += 1
            continue
        if s.startswith("(") and ")" not in s and i + 1 < len(body) and body[i + 1].endswith(")") and "(" not in body[i + 1]:
            pending_heading = (s + body[i + 1]).strip("()（）")
            i += 2
            continue
        am = X.ARTICLE_NUM_RE.match(s)
        if am:
            blk["entries"].append({"number": s[: am.end() - 1], "heading": pending_heading, "lines": [s[am.end():]],
                                   "deleted": s[am.end():].strip() == "削除"})
            pending_heading = None
        elif not blk["entries"] or blk["entries"][-1]["number"] is None and False:
            blk["entries"].append({"number": None, "heading": pending_heading, "lines": [s], "deleted": False})
            pending_heading = None
        else:
            blk["entries"][-1]["lines"].append(s)
        i += 1

    out = []
    for b, blk in enumerate(blocks):
        bkey = f"s{b:02d}"
        if blk["kind"] == "附則" and not blk["notice"]:
            title = "附則"
        else:
            title = f"{blk['kind']}({blk['notice']})" + ("抄" if blk["ex"] else "")
        path = [{"level": 1, "number": None, "heading": title, "key": bkey}]
        u = 0
        for e in blk["entries"]:
            if e["number"] is None:
                u += 1
                key = f"{bkey}.u{u}"
            else:
                nums = [ja_refs.k2i(x) for x in re.findall(ja_refs.N, e["number"])]
                key = f"{bkey}.art" + "-".join(map(str, nums))
            paras = [] if e["deleted"] else para_split(e["lines"], e["number"] is None)
            out.append({"number": e["number"] or "", "key": key, "heading": e["heading"], "path": [dict(p) for p in path],
                        "deleted": e["deleted"], "paragraphs": paras})
    used_t = {m for a in out for p in a["paragraphs"] for m in re.findall(r"\{\{T:([^}]+)\}\}", p["text"])}
    used_f = {m for a in out for p in a["paragraphs"] for m in re.findall(r"\{\{F:([^}]+)\}\}", p["text"])}
    json.dump({"nested_ids": True, "articles": out, "tables": [t for t in tables if t["id"] in used_t],
               "images": [im for im in images if im["id"] in used_f]}, open(sys.argv[2], "w"), ensure_ascii=False, indent=1)
    print(f"{len(blocks)} blocks, {len(out)} entries, {sum(len(a['paragraphs']) for a in out)} paragraphs, {len(used_t)} tables, {len(used_f)} images")


if __name__ == "__main__":
    main()
