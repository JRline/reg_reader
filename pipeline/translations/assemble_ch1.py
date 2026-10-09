#!/usr/bin/env python3
"""Assemble translations/ch1/art1.json (Chapter 1, 第一条) from translations/ch1_parts/p*.json:
one English string per segment of the 216-segment paragraph, joined with single spaces.
Usage: python3 pipeline/translations/assemble_ch1.py"""
import json, re
from pathlib import Path
HERE = Path(__file__).resolve().parent
ext = json.loads((HERE.parent / "source" / "ch1_v2.json").read_text(encoding="utf-8"))
segs = ext["articles"][0]["paragraphs"][0]["segments"]
en, terms = {}, []
for fp in sorted((HERE / "ch1_parts").glob("p*.json")):
    d = json.loads(fp.read_text(encoding="utf-8"))
    en.update({int(k): v for k, v in d["segments"].items()})
    terms += d.get("terms", [])
missing = [i for i in range(len(segs)) if i not in en or not en[i].strip()]
assert not missing, f"missing segments: {missing[:20]}"
seen, uniq = set(), []
for t in terms:
    if t["ja"] not in seen:
        seen.add(t["ja"]); uniq.append(t)
n_items = sum(1 for s in segs if s["level"] == 1)
out = {"number": "第一条", "heading_en": "Definitions",
       "summary_ja": "この告示で用いる用語（子法人等、証券化取引、内部格付手法採用最終指定親会社など）の意義を各号で定める。",
       "summary_en": f"Defines, in {n_items} numbered items (with sub-items), the terms used throughout this Public Notice.",
       "all_terms": True, "terms": uniq, "paragraphs": [" ".join(en[i].strip() for i in range(len(segs)))]}
(HERE / "ch1").mkdir(exist_ok=True)
(HERE / "ch1" / "art1.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(len(segs), "segments,", len(uniq), "terms")
