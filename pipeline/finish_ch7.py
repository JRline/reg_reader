#!/usr/bin/env python3
"""Chapter 7's extraction runs on past 第二百九十八条 into the 附則 (supplementary provisions of the
original notification and ~17 amending notices — repeated article numbers, out of scope here)
and the two 別表 (appended tables). This keeps 第二百八十一条–第二百九十八条, strips the stray
"附則" heading off the last paragraph, and appends the 別表 as article-shaped entries from
pipeline/source/ch7_appendices.json (hand-authored: {"articles": [{number, heading, path: [],
deleted: false, paragraphs: [{number: null, text, segments: [{marker, level, text}]}]}]}).
Idempotent. Usage: python3 pipeline/finish_ch7.py"""
import json
from pathlib import Path
SRC = Path(__file__).parent / "source"
d = json.loads((SRC / "ch7_v2.json").read_text(encoding="utf-8"))
if "_trimmed" not in d:
    arts, out = d["articles"], []
    for a in arts:
        out.append(a)
        if a["number"] == "第二百九十八条":
            break
    last = out[-1]["paragraphs"][-1]
    assert last["text"].endswith("附則"), last["text"][-10:]
    last["text"] = last["text"][:-2]
    last["segments"][-1]["text"] = last["segments"][-1]["text"][:-2]
    d["articles"] = out
    d["_trimmed"] = True
else:
    d["articles"] = [a for a in d["articles"] if not a["number"].startswith("別表")]
ap = SRC / "ch7_appendices.json"
if ap.exists():
    d["articles"] += json.loads(ap.read_text(encoding="utf-8"))["articles"]
(SRC / "ch7_v2.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(d["articles"]), "entries; last:", d["articles"][-1]["number"])
