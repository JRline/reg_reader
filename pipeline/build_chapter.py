#!/usr/bin/env python3
"""
Builds (or rebuilds) one chapter of a feed from an extract_chapter_v2.py extraction plus
in-repo translation files — the no-chatbot path used from Chapter 3 onward.

Inputs:
  - <extraction.json>  from extract_chapter_v2.py (articles, 節/款/目 paths, segments,
                       {{T:}}/{{F:}} tokens)
  - <translations_dir>/<article key>.json, one per article:
        {
          "number": "第十四条",
          "heading_en": "...",
          "summary_ja": "...", "summary_en": "...",
          "paragraphs": ["<text_en of paragraph 1>", "<text_en of paragraph 2>", ...],
          "terms": [{"ja": "...", "en": "..."}]          # optional: terms defined here
          "sections_en": {"第一節": "General Provisions"}  # optional: group headings
        }
    text_en keeps every {{T:…}}/{{F:…}} token of its Japanese paragraph, at the
    corresponding place.

Per paragraph it derives — without a model — clauses_ja (from the extraction's item
segments), clauses_en (refine_clauses.resegment_en), and refs (ja_refs.extract, with
text_en filled where the conventional English citation appears in text_en). Articles
without a translation file are still created (so the contents list is complete) but get
no paragraphs; the reader shows them as "not yet processed" (never an empty text_en —
CLAUDE.md rule 2).

Run afterwards, as for any chapter:
  reresolve_refs.py → link_external_refs.py → refine_clauses.py → annotate_cues.py

Usage:
    python3 build_chapter.py <feed_id> <chapter_id> <chapter_number> <chapter_heading> \
        <chapter_heading_en> <extraction.json> <translations_dir>
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import ja_refs  # noqa: E402
from refine_clauses import resegment_en  # noqa: E402

FEEDS_DIR = Path(__file__).parent.parent / "feeds"
TOKEN_RE = re.compile(r"\{\{[TF]:[^}]+\}\}")


def article_key(number):
    """第四十三条の三の二 -> art43-3-2; 第七十一条から第七十五条まで -> art71-75-deleted."""
    nums = [ja_refs.k2i(x) for x in re.findall(ja_refs.N, number)]
    if "から" in number:
        return f"art{nums[0]}to{nums[-1]}"
    return "art" + "-".join(str(n) for n in nums)


def section_key(path):
    return ".".join({1: "sec", 2: "sub", 3: "div"}[p["level"]] + str(ja_refs.k2i(re.findall(ja_refs.N, p["number"])[0])) for p in path)


def clauses_ja_from_segments(segments):
    return [{"clause_type": "enumeration_item" if sg["marker"] else "main", "text": sg["text"]} for sg in segments]


def en_candidates(r):
    """English forms a citation may take, most specific first. Grouped citations ("Article 2
    and Article 14 of the X Notice") and "the same Notice" make the fully-qualified form
    absent even when the translation is faithful, so the bare citation is the fallback —
    used only when the instrument's own name (or "the same Notice/Act") is in the paragraph."""
    raw = r["raw_text"]
    law = r["external_name"]
    out = []
    if raw.startswith("同告示"):
        bare = ja_refs.to_en(raw[3:])
        if bare:
            out += [f"{bare} of the same Notice", bare]
        return out
    full = ja_refs.to_en(raw)
    if not full:
        return out
    if law in ja_refs.NOTICE_EN:
        out.append(f"{full} of {ja_refs.NOTICE_EN[law]}")
        out.append(full)
    else:
        out.append(full)
        m = ja_refs.REF_RE.fullmatch(raw)
        if m and m.group("law"):
            bare = ja_refs.to_en(m.group("cite"))
            if bare:
                out.append(bare)
    return out


def refs_for(text_ja, text_en):
    refs = []
    for r in ja_refs.extract(text_ja):
        cands = en_candidates(r)
        law_named = not r["external_name"] or (r.get("external_name_en") and r["external_name_en"][4:] in (text_en or "")) \
            or "the same Notice" in (text_en or "") or "the same Act" in (text_en or "")
        en = next((c for i, c in enumerate(cands) if text_en and c in text_en and (i == 0 or law_named)), None)
        refs.append({
            "raw_text": r["raw_text"],
            "text_en": en,
            "scope": r["scope"],
            "external_name": r["external_name"],
            "external_name_en": r.get("external_name_en"),
            "external_item_summary_ja": None,
            "external_item_summary_en": None,
            "external_item_summary_confidence": None,
            "resolution_status": "unresolved",
            "target_ids": [],
            "target_feed": None,
        })
    return refs


def main():
    if len(sys.argv) != 8:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id, ch_number, ch_heading, ch_heading_en, extraction_path, tr_dir = sys.argv[1:8]
    feed_path = FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    ext = json.loads(Path(extraction_path).read_text(encoding="utf-8"))
    tr_dir = Path(tr_dir)

    translations = {}
    sections_en = {}
    for fp in sorted(tr_dir.glob("*.json")):
        t = json.loads(fp.read_text(encoding="utf-8"))
        translations[t["number"]] = t
        sections_en.update(t.get("sections_en", {}))

    chapter = {"id": chapter_id, "type": "chapter", "number": ch_number, "heading": ch_heading, "heading_en": ch_heading_en,
               "text_ja": None, "text_en": None, "clauses_ja": [], "clauses_en": [], "refs": [], "defined_terms": [], "children": []}
    groups = {}  # section path key -> node
    problems, built, pending = [], 0, []

    for a in ext["articles"]:
        parent = chapter
        for depth in range(1, len(a["path"]) + 1):
            sub = a["path"][:depth]
            key = section_key(sub)
            if key not in groups:
                p = sub[-1]
                node = {"id": f"{chapter_id}.{key}", "type": {1: "section", 2: "subsection", 3: "division"}[p["level"]],
                        "number": p["number"], "heading": p["heading"],
                        "heading_en": sections_en.get(" ".join(x["number"] for x in sub)) or sections_en.get(p["number"] + " " + p["heading"]),
                        "text_ja": None, "text_en": None, "clauses_ja": [], "clauses_en": [], "refs": [], "defined_terms": [], "children": []}
                groups[key] = node
                parent["children"].append(node)
            parent = groups[key]

        art_id = f"{chapter_id}.{article_key(a['number'])}"
        tr = translations.get(a["number"])
        art = {"id": art_id, "type": "article", "number": a["number"], "heading": a["heading"],
               "heading_en": tr.get("heading_en") if tr else None,
               "text_ja": None, "text_en": None,
               "summary_ja": tr.get("summary_ja") if tr else None, "summary_en": tr.get("summary_en") if tr else None,
               "translation_status": "llm_draft" if tr else "pending",
               "clauses_ja": [], "clauses_en": [], "refs": [], "defined_terms": [], "children": []}
        parent["children"].append(art)

        if a["deleted"]:
            art["children"].append({"id": f"{art_id}.p1", "type": "paragraph", "number": None, "heading": None,
                                    "text_ja": "削除", "text_en": "Deleted.", "translation_status": "reviewed",
                                    "clauses_ja": [{"clause_type": "main", "text": "削除"}], "clauses_en": [{"clause_type": "main", "text": "Deleted."}],
                                    "refs": [], "defined_terms": [], "children": []})
            art["heading_en"] = art["heading_en"] or None
            art["translation_status"] = "reviewed"
            built += 1
            continue
        if not tr:
            pending.append(a["number"])
            continue
        if len(tr["paragraphs"]) != len(a["paragraphs"]):
            problems.append(f"{a['number']}: {len(tr['paragraphs'])} translated paragraphs vs {len(a['paragraphs'])} in the source")
            continue
        terms = tr.get("terms", [])
        for k, (pj, ten) in enumerate(zip(a["paragraphs"], tr["paragraphs"]), start=1):
            tja = pj["text"]
            if sorted(TOKEN_RE.findall(tja)) != sorted(TOKEN_RE.findall(ten)):
                problems.append(f"{a['number']} p{k}: table/formula tokens differ between ja and en")
            if not ten.strip():
                problems.append(f"{a['number']} p{k}: empty text_en")
            defined = [{"term_ja": t["ja"], "term_en": t.get("en"), "expands_to_ja": t.get("expands_to_ja"), "definition_node_id": f"{art_id}.p{k}"}
                       for t in terms if f"「{t['ja']}」" in tja]
            art["children"].append({
                "id": f"{art_id}.p{k}", "type": "paragraph", "number": pj["number"], "heading": None,
                "text_ja": tja, "text_en": ten, "translation_status": "llm_draft",
                "clauses_ja": clauses_ja_from_segments(pj["segments"]),
                "clauses_en": resegment_en(ten, []),
                "refs": refs_for(tja, ten),
                "defined_terms": defined, "children": [],
            })
        built += 1

    existing = [i for i, c in enumerate(feed["root"]["children"]) if c["id"] == chapter_id]
    if existing:
        feed["root"]["children"][existing[0]] = chapter
    else:
        feed["root"]["children"].append(chapter)
        feed["root"]["children"].sort(key=lambda c: ja_refs.k2i(re.findall(ja_refs.N, c.get("number") or "第零章")[0]) if c.get("number") else 0)
    feed_path.write_text(json.dumps(feed, ensure_ascii=False, indent=2), encoding="utf-8")

    n_refs = sum(len(p.get("refs", [])) for p in _walk(chapter) if p.get("type") == "paragraph")
    n_en = sum(1 for p in _walk(chapter) if p.get("type") == "paragraph" for r in p.get("refs", []) if r.get("text_en"))
    print(f"{chapter_id}: {built} articles built, {len(pending)} pending translation, {len(groups)} section nodes, "
          f"{n_refs} refs ({n_en} matched in English)")
    for p in problems:
        print("  PROBLEM:", p)
    if pending:
        print("  pending:", " ".join(pending[:12]), "…" if len(pending) > 12 else "")


def _walk(n):
    yield n
    for c in n.get("children", []):
        yield from _walk(c)


if __name__ == "__main__":
    main()
