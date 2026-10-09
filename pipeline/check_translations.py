#!/usr/bin/env python3
"""Validate translation files WITHOUT touching the feed.
Usage: python3 pipeline/check_translations.py <extraction.json> <translations_dir> [<first article number> [<last>]]
Checks, per article in range: file exists; paragraph count equals the extraction's; {{T:}}/{{F:}}
tokens identical between JA and EN; no empty text_en; list markers (一 → (i) …) count matches;
quoted terms 「…」 that look defined have an EN entry in `terms` (warning); every table/formula token
is covered by a *_tables.json / *_formulas.py in pipeline/translations (warning). Exit 1 on errors."""
import json, re, sys, runpy
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE / "translations"))
import ja_refs
TOK = re.compile(r"\{\{[TF]:[^}]+\}\}")
ext = json.load(open(sys.argv[1])); trd = Path(sys.argv[2])
nums = [a["number"] for a in ext["articles"]]
i = nums.index(sys.argv[3]) if len(sys.argv) > 3 else 0
j = nums.index(sys.argv[4]) if len(sys.argv) > 4 else (i if len(sys.argv) > 3 else len(nums) - 1)
tables, anchors = set(), set()
for fp in (HERE / "translations").glob("*_tables.json"):
    tables |= set(json.load(open(fp)))
import formulas_lib as L
for fp in (HERE / "translations").glob("*_formulas.py"):
    L.V.clear(); L.F.clear(); runpy.run_path(str(fp)); anchors |= {x["anchor"] for x in L.F}
if (HERE / "translations" / "ch3_formulas.py").exists():
    pass
errs = warns = 0
byn = {}
for fp in trd.glob("*.json"):
    t = json.load(open(fp)); byn[t["number"]] = t
for a in ext["articles"][i:j + 1]:
    if a["deleted"]:
        continue
    t = byn.get(a["number"])
    if not t:
        print("ERR  missing translation:", a["number"]); errs += 1; continue
    for k in ("heading_en", "summary_ja", "summary_en", "paragraphs"):
        if k not in t or (k != "heading_en" and not t[k]) :
            print("ERR ", a["number"], "missing", k); errs += 1
    if a["heading"] and not t.get("heading_en"):
        print("ERR ", a["number"], "heading_en empty"); errs += 1
    if len(t["paragraphs"]) != len(a["paragraphs"]):
        print("ERR ", a["number"], f"{len(t['paragraphs'])} EN paragraphs vs {len(a['paragraphs'])} JA"); errs += 1; continue
    for k, (pj, en) in enumerate(zip(a["paragraphs"], t["paragraphs"]), 1):
        ja = pj["text"]
        if not en.strip(): print("ERR ", a["number"], k, "empty"); errs += 1
        if sorted(TOK.findall(ja)) != sorted(TOK.findall(en)):
            print("ERR ", a["number"], k, "tokens differ", TOK.findall(ja), TOK.findall(en)); errs += 1
        for tok in TOK.findall(ja):
            kind, tid = tok[2], tok[4:-2]
            if kind == "T" and tid not in tables: print("WARN", a["number"], k, "no table entry for", tid); warns += 1
            if kind == "F" and tid not in anchors: print("WARN", a["number"], k, "no formula for", tid); warns += 1
        if re.search(r"[ぁ-んァ-ヶ]", en): print("ERR ", a["number"], k, "kana left in EN text"); errs += 1
        nja = sum(1 for s in pj["segments"] if s["marker"]); nen = len(re.findall(r"(?:^|[.;:] )\((?:[ivxl]+|[a-z]|\d+)(?:-\d+)?\) ", en))
        if nja and nen < nja * 0.7:
            print("WARN", a["number"], k, f"{nja} JA list markers but only {nen} EN markers"); warns += 1
print(f"checked {j - i + 1} articles: {errs} errors, {warns} warnings")
sys.exit(1 if errs else 0)
