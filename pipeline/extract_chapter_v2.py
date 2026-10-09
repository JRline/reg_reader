#!/usr/bin/env python3
"""
Layout-aware chapter extractor (pdfplumber). Supersedes extract_chapter.py for chapters
that contain tables, image formulas, or 節/款/目 sections — which pypdf's flat text can't
represent:

  - TABLES are real text in the PDF, but pypdf runs their cells together into the
    paragraph ("信用リスク区分3―13―2…リスク・ウェイト二十三十…"). Here each table is cut out
    of the text stream, kept as rows/cells, and replaced by a {{T:<id>}} token where it
    sat. Tables split across a page break are merged.
  - IMAGE FORMULAS (display formulas, and small inline symbols mid-sentence) are invisible
    to any text extractor. Each image's position is kept as a {{F:<id>}} token, so the
    text shows exactly where a formula belongs instead of silently closing the gap; the
    image itself is listed for transcription into formulas.json (CLAUDE.md rule 7).
  - SECTIONS (第一節 / 第一款 / 第一目) are recorded as a path on each article.
  - ITEMS: each paragraph also gets `segments` split at line-start item markers
    (一 / 二の二 / イ / (１)), which gives a faithful clauses_ja without a model. イロハ
    markers are sequence-checked (CLAUDE.md rule 5).

Concatenating a paragraph's segment texts reproduces its text exactly.

Usage:
    python3 extract_chapter_v2.py <pdf> <chapter_start_marker> <chapter_end_marker> <out.json>
e.g.
    python3 extract_chapter_v2.py pipeline/source/saishu1.pdf "第三章 信用リスクの標準的手法" \
        "第四章 信用リスクの内部格付手法" pipeline/source/ch3_v2.json
"""
import json
import re
import sys

import pdfplumber

ARTICLE_NUM_RE = re.compile(r"^第[一二三四五六七八九十百]+条(の[一二三四五六七八九十]+)*[ 　]")
ARTICLE_RANGE_DELETED_RE = re.compile(r"^第[一二三四五六七八九十百]+条(の[一二三四五六七八九十]+)*から第[一二三四五六七八九十百]+条(の[一二三四五六七八九十]+)*まで[ 　]*削除$")
HEADING_RE = re.compile(r"^\(.+\)$")
SECTION_RE = re.compile(r"^第([一二三四五六七八九十]+)(節|款|目)[ 　]+(.+)$")
PAGE_NUM_RE = re.compile(r"^\d+\s*/\s*\d+$")
PARAGRAPH_NUM_RE = re.compile(r"^([２-９]|[１-９][０-９])[ 　]")
KANJI_ITEM_RE = re.compile(r"^([一二三四五六七八九十]+(?:の[一二三四五六七八九十]+)*)(?:[ 　]|$)")
IROHA = "イロハニホヘトチリヌルヲワカヨタレソツネナラムウヰノオクヤマケフコエテアサキユメミシヱヒモセス"
IROHA_ITEM_RE = re.compile(rf"^([{IROHA}])(?:[ 　]|$)")
PAREN_ITEM_RE = re.compile(r"^([(（][０-９0-9]+[)）])[ 　]")
LEVEL = {"節": 1, "款": 2, "目": 3}
DISPLAY_TOKEN_RE = re.compile(r"\{\{F:[^}]+\}\}")
BARE_MARKER_RE = re.compile(r"[一二三四五六七八九十]+(?:の[一二三四五六七八九十]+)*|[イロハニホヘトチリヌルヲワカヨタレソツネナラム]")
LINE_TOL = 3.0  # chars whose tops differ by less than this sit on one line
_OV = __import__("pathlib").Path(__file__).parent / "source" / "table_region_overrides.json"
OVERRIDES = json.loads(_OV.read_text(encoding="utf-8")) if _OV.exists() else {}


def inside(obj, bbox, pad=1.0):
    x0, top, x1, bottom = bbox
    return obj["x0"] >= x0 - pad and obj["x1"] <= x1 + pad and obj["top"] >= top - pad and obj["bottom"] <= bottom + pad


def page_lines(page, pno, tables_out, images_out):
    """The page as text lines, top to bottom, with table/image tokens in place."""
    # A table continued from the previous page has no top rule (and one running onto the
    # next page has no bottom rule), so the line-based finder misses those fragments.
    # Virtual rules at the content area's edges close them.
    settings = {"explicit_horizontal_lines": [62, 786]}
    found = page.find_tables(settings)
    tables = []  # (bbox, rows)
    for t in found:
        bbox = t.bbox
        for o in OVERRIDES.get(str(pno), []):
            if abs(bbox[1] - o["match_top"]) <= 3:
                bbox = (bbox[0], bbox[1], bbox[2], o["bottom"])
        if bbox == t.bbox:
            tables.append((bbox, t.extract()))
        else:
            rows = page.crop(bbox).extract_table({"explicit_horizontal_lines": [bbox[1], bbox[3]]}) or t.extract()
            tables.append((bbox, rows))
    tboxes = [b for b, _ in tables]
    items = []  # (top, x0, text)
    small = []
    for c in page.chars:
        if any(inside(c, b) for b in tboxes):
            continue
        if c["size"] < 9.5:
            small.append(c)  # sub/superscript — placed after the lines are known
        else:
            items.append((c["top"], c["x0"], c["text"]))
    for k, (bbox, rows) in enumerate(tables):
        tid = f"p{pno}t{k}"
        tables_out.append({"id": tid, "page": pno, "bbox": [round(v, 1) for v in bbox], "rows": rows})
        items.append((bbox[1], -1.0, f"\n{{{{T:{tid}}}}}\n"))
    for k, im in enumerate(page.images):
        if any(inside(im, b) for b in tboxes):
            continue
        fid = f"p{pno}i{k}"
        h = im["bottom"] - im["top"]
        images_out.append({"id": fid, "page": pno, "bbox": [round(im["x0"], 1), round(im["top"], 1), round(im["x1"], 1), round(im["bottom"], 1)], "inline": h < 12})
        # An inline symbol sits on a text line; anchor it at that line's top so it sorts
        # into place by x. A display formula gets its own line.
        # Anchor every image at its vertical centre, shifted to a text line's top: an inline
        # symbol then sorts into its line by x, and a display formula sorts after an item
        # marker that sits beside it ("二 [formula]") instead of before it.
        items.append((im["top"] + h / 2 - 5, im["x0"], f"{{{{F:{fid}}}}}" if h < 12 else f"\n{{{{F:{fid}}}}}\n"))
    items.sort(key=lambda it: (it[0], it[1]))
    lines, cur, cur_top = [], [], None
    for top, x0, text in items:
        if cur_top is None or abs(top - cur_top) > LINE_TOL:
            if cur:
                lines.append(cur)
            cur, cur_top = [], top
        cur.append((top, x0, text))
    if cur:
        lines.append(cur)
    # Sub/superscripts (7pt, e.g. the "collect" in C_MA,collect) sit a few points off the
    # baseline; clustering them with the full-size text by top alone split them onto lines
    # of their own. Attach each to the nearest full-size line and mark it _{…} / ^{…} (the
    # same markup notation.json uses), grouping a run of adjacent small chars into one.
    centers = []
    for line in lines:
        tops = [t for t, _x, txt in line if not txt.startswith("\n")]
        centers.append(min(tops) + 5.3 if tops else None)
    for c in small:
        mid = (c["top"] + c["bottom"]) / 2
        best = min((k for k, cen in enumerate(centers) if cen is not None), key=lambda k: abs(centers[k] - mid), default=None)
        if best is None or abs(centers[best] - mid) > 10:
            continue
        kind = "_" if mid > centers[best] else "^"
        lines[best].append((c["top"], c["x0"], (kind, c["text"])))
    out = []
    for line in lines:
        parts, run_kind, run = [], None, []
        for _t, _x, txt in sorted(line, key=lambda p: p[1]):
            if isinstance(txt, tuple):
                if run and run_kind != txt[0]:
                    parts.append(f"{run_kind}{{{''.join(run)}}}")
                    run = []
                run_kind = txt[0]
                run.append(txt[1])
                continue
            if run:
                parts.append(f"{run_kind}{{{''.join(run)}}}")
                run = []
            parts.append(txt)
        if run:
            parts.append(f"{run_kind}{{{''.join(run)}}}")
        out.extend("".join(parts).split("\n"))
    return out


def merge_split_tables(tables, lines):
    """A table ending at the bottom of a page and one starting at the top of the next with
    the same column count are one table; drop the second token and append its rows."""
    by_id = {t["id"]: t for t in tables}
    order = [t["id"] for t in tables]
    merged_into = {}
    for a, b in zip(order, order[1:]):
        ta, tb = by_id[a], by_id[b]
        root = merged_into.get(a, a)
        if tb["page"] == ta["page"] + 1 and ta["bbox"][3] > 700 and tb["bbox"][1] < 70:
            # Starts at the very top of the next page: a continuation. A row cut by the
            # page break arrives as two partial rows; that, and any column-count mismatch
            # (a final row with merged cells), is left for curation in tables.json.
            width = len(by_id[root]["rows"][0])
            by_id[root]["rows"].extend([r + [None] * (width - len(r)) if len(r) < width else r for r in tb["rows"]])
            by_id[root].setdefault("continued_on", []).append(tb["page"])
            merged_into[b] = root
    keep = [t for t in tables if t["id"] not in merged_into]
    lines = [l for l in lines if not any(l.strip() == f"{{{{T:{m}}}}}" for m in merged_into)]
    return keep, lines


def clean(text):
    """Japanese legal text has no spaces; any left after marker detection is a layout
    artifact. Tokens are kept intact."""
    return re.sub(r"[ 　]", "", text)


def segment_paragraph(lines):
    """[(marker_or_None, level, text)] — split at line-start item markers."""
    segs = []
    cur_marker, cur_level, cur = None, 0, []
    iroha_next = 0

    def flush():
        t = clean("".join(cur))
        if t:
            segs.append({"marker": cur_marker, "level": cur_level, "text": t})

    # An item whose body is a display formula ("二 [formula]") can come out as the formula
    # line first, then the bare marker — the image's box starts a few points above the
    # marker's text line. Put the marker back in front of it.
    lines = list(lines)
    for k in range(len(lines) - 1):
        if DISPLAY_TOKEN_RE.fullmatch(lines[k]) and BARE_MARKER_RE.fullmatch(lines[k + 1]):
            lines[k], lines[k + 1] = lines[k + 1], lines[k]
    for k, ln in enumerate(lines):
        m1, m2, m3 = KANJI_ITEM_RE.match(ln), IROHA_ITEM_RE.match(ln), PAREN_ITEM_RE.match(ln)
        if BARE_MARKER_RE.fullmatch(ln) and not (k + 1 < len(lines) and DISPLAY_TOKEN_RE.fullmatch(lines[k + 1])):
            # a lone numeral/kana on its own line is a wrapped value ("…上昇するもの" / "一"),
            # not a marker — unless a display formula (the item's body) follows it
            m1 = m2 = None
        if m1:
            flush()
            cur_marker, cur_level, cur = m1.group(1), 1, [ln]
            iroha_next = 0
        elif m2 and iroha_next < len(IROHA) and m2.group(1) == IROHA[iroha_next]:
            flush()
            cur_marker, cur_level, cur = m2.group(1), 2, [ln]
            iroha_next += 1
        elif m3:
            flush()
            cur_marker, cur_level, cur = m3.group(1), 3, [ln]
        else:
            cur.append(ln)
    flush()
    return segs


def main():
    pdf_path, start_marker, end_marker, out_path = sys.argv[1:5]
    pdf = pdfplumber.open(pdf_path)
    tables, images, all_lines = [], [], []
    for pno, page in enumerate(pdf.pages, start=1):
        for ln in page_lines(page, pno, tables, images):
            all_lines.append((pno, ln.strip()))
    texts = [l for _, l in all_lines]
    end_idx = max(i for i, l in enumerate(texts) if l == end_marker)
    start_idx = max(i for i, l in enumerate(texts) if i < end_idx and l == start_marker)
    first_page, last_page = all_lines[start_idx][0], all_lines[end_idx][0]
    tables = [t for t in tables if first_page <= t["page"] <= last_page]
    images = [im for im in images if first_page <= im["page"] <= last_page]
    body = [l for l in texts[start_idx + 1:end_idx] if l and not PAGE_NUM_RE.match(l)]
    tables, body = merge_split_tables(tables, body)

    articles, path = [], []
    pending_heading, cur = None, None
    i = 0
    while i < len(body):
        s = body[i]
        sm = SECTION_RE.match(s)
        if sm and len(s) < 60:
            level = LEVEL[sm.group(2)]
            heading = sm.group(3)
            # A long section heading wraps; the continuation is the next line, before the
            # "(…)" article heading or an article start.
            nxt = body[i + 1] if i + 1 < len(body) else ""
            if nxt and not HEADING_RE.match(nxt) and not ARTICLE_NUM_RE.match(nxt) and not SECTION_RE.match(nxt) \
                    and not ARTICLE_RANGE_DELETED_RE.match(nxt) and len(nxt) < 30:
                heading += nxt
                i += 1
            path = [p for p in path if p["level"] < level] + [{"level": level, "number": f"第{sm.group(1)}{sm.group(2)}", "heading": clean(heading)}]
            i += 1
            continue
        if HEADING_RE.match(s):
            pending_heading = s.strip("()（）")
            i += 1
            continue
        # A long heading wraps onto a second line: "(株式会社…及び" / "…エクスポージャー)",
        # immediately followed by the article it heads.
        if s.startswith("(") and ")" not in s and i + 2 < len(body) and body[i + 1].endswith(")") \
                and "(" not in body[i + 1] and ARTICLE_NUM_RE.match(body[i + 2]):
            pending_heading = (s + body[i + 1]).strip("()（）")
            i += 2
            continue
        dm = ARTICLE_RANGE_DELETED_RE.match(s)
        am = ARTICLE_NUM_RE.match(s)
        if dm or am:
            if cur:
                articles.append(cur)
            number = clean(s.split("削除")[0]) if dm else s[: am.end() - 1]
            cur = {"number": number, "heading": pending_heading, "path": [dict(p) for p in path], "lines": [] if dm else [s[am.end():]],
                   "deleted": bool(dm) or s[am.end():].strip() == "削除"}
            pending_heading = None
            i += 1
            continue
        if cur:
            cur["lines"].append(s)
        i += 1
    if cur:
        articles.append(cur)

    out = []
    for a in articles:
        paragraphs, cur_num, cur_lines = [], None, []
        for ln in a["lines"]:
            m = PARAGRAPH_NUM_RE.match(ln)
            if m:
                if cur_lines:
                    paragraphs.append((cur_num, cur_lines))
                cur_num, cur_lines = m.group(1), [ln[m.end():]]
            else:
                cur_lines.append(ln)
        if cur_lines:
            paragraphs.append((cur_num, cur_lines))
        paras = []
        for num, lines in paragraphs:
            segs = segment_paragraph(lines)
            text = "".join(sg["text"] for sg in segs)
            if text:
                paras.append({"number": num, "text": text, "segments": segs})
        out.append({"number": a["number"], "heading": a["heading"], "path": a["path"], "deleted": a["deleted"], "paragraphs": paras})

    used_t = {m for a in out for p in a["paragraphs"] for m in re.findall(r"\{\{T:([^}]+)\}\}", p["text"])}
    used_f = {m for a in out for p in a["paragraphs"] for m in re.findall(r"\{\{F:([^}]+)\}\}", p["text"])}
    json.dump({"articles": out, "tables": [t for t in tables if t["id"] in used_t],
               "images": [im for im in images if im["id"] in used_f]},
              open(out_path, "w"), ensure_ascii=False, indent=1)
    print(f"{len(out)} articles, {sum(len(a['paragraphs']) for a in out)} paragraphs, "
          f"{len(used_t)} tables, {len(used_f)} formula images -> {out_path}")


if __name__ == "__main__":
    main()
