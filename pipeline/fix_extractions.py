#!/usr/bin/env python3
"""One-off repairs to the Chapter 4-6 extractions (and the matching translation files) for
layout artifacts the v2 extractor could not tell from body text. Idempotent.

 1. A heading wrapped onto the next page/line is glued to the PREVIOUS article's last
    paragraph, leaving the next article without a heading (ch6: 第二百六十三条の四, の五,
    第二百六十八条の二). The heading is moved back onto its article.
 2. ch4 第四節 第九款's heading was cut at a line wrap, and its tail ended up in 第二百十六条.
 3. ch5 第二百三十一条/第二百四十一条 headings carry an image formula token that is not in the
    images list; replaced by the plain-text form (K_{SSFA}(K_{IRB}) / K_{SSFA}(K_{A})).
 4. ch4 第百二十六条 paragraph 3 ends in a second slotting table (p158t0) that the extractor
    merged into paragraph 2's table; its token is restored on paragraph 3 (JA + EN).
Run before build_chapter.py."""
import json, re
from pathlib import Path
SRC = Path(__file__).parent / "source"
TR = Path(__file__).parent / "translations"


def load(c): return json.loads((SRC / f"{c}_v2.json").read_text(encoding="utf-8"))
def save(c, d): (SRC / f"{c}_v2.json").write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")
def art(d, n): return next(a for a in d["articles"] if a["number"] == n)


def last_paren(text):
    """Split trailing '(…)' at depth 0 -> (body, inner) or None."""
    if not text.endswith(")"):
        return None
    depth = 0
    for i in range(len(text) - 1, -1, -1):
        depth += {")": 1, "(": -1}.get(text[i], 0)
        if depth == 0:
            return text[:i], text[i + 1:-1]
    return None


def strip_tail(a, tail_ja):
    p = a["paragraphs"][-1]
    if p["text"].endswith(tail_ja):
        p["text"] = p["text"][: -len(tail_ja)]
        p["segments"][-1]["text"] = p["segments"][-1]["text"][: -len(tail_ja)]


def en_strip_paren(tr_file):
    if not tr_file.exists():
        return
    t = json.loads(tr_file.read_text(encoding="utf-8"))
    lp = last_paren(t["paragraphs"][-1].rstrip())
    if lp:
        t["paragraphs"][-1] = lp[0].rstrip() + " " if t["paragraphs"][-1].endswith(" ") else lp[0].rstrip()
        tr_file.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


# 1. ch6 headings
d = load("ch6")
for prev, nxt, key in (("第二百六十三条の三", "第二百六十三条の四", "art263-4"), ("第二百六十三条の四", "第二百六十三条の五", "art263-5"), ("第二百六十八条", "第二百六十八条の二", "art268-2")):
    a, b = art(d, prev), art(d, nxt)
    lp = last_paren(a["paragraphs"][-1]["text"])
    if lp and not b["heading"]:
        b["heading"] = lp[1]
        strip_tail(a, "(" + lp[1] + ")")
        # the previous article's EN last paragraph ends with the same heading in parentheses
        pk = {"第二百六十三条の三": "art263-3", "第二百六十三条の四": "art263-4", "第二百六十八条": "art268"}[prev]
        en_strip_paren(TR / "ch6" / f"{pk}.json")
save("ch6", d)

# 2 + 4. ch4
d = load("ch4")
FULL = "法的に有効な相対ネッティング契約下にあるレポ形式の取引及び信用取引その他これに類する海外の取引に対するエクスポージャー変動額推計モデルの使用"
for a in d["articles"]:
    for p in a["path"]:
        if p["number"] == "第九款" and p["heading"] == "法的に有効な相対ネッティング契約下にあるレポ形式の取引及び信用":
            p["heading"] = FULL
strip_tail(art(d, "第二百十六条"), "取引その他これに類する海外の取引に対するエクスポージャー変動額推計モデルの使用")
a = art(d, "第百二十六条")
p3 = a["paragraphs"][2]
if "{{T:p158t0}}" not in p3["text"]:
    p3["text"] += "{{T:p158t0}}"
    p3["segments"][-1]["text"] += "{{T:p158t0}}"
    tf = TR / "ch4" / "art126.json"
    t = json.loads(tf.read_text(encoding="utf-8"))
    if "{{T:p158t0}}" not in t["paragraphs"][2]:
        t["paragraphs"][2] = t["paragraphs"][2].rstrip() + " {{T:p158t0}}"
        tf.write_text(json.dumps(t, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
save("ch4", d)

# 3. ch5 headings
d = load("ch5")
for n, old, new in (("第二百三十一条", "K_{IRB}超過部分の所要自己資本率({{F:p237i3}}", "K_{IRB}超過部分の所要自己資本率(K_{SSFA}(K_{IRB}))"),
                    ("第二百四十一条", "K_{A}超過部分の所要自己資本率({{F:p254i0}}", "K_{A}超過部分の所要自己資本率(K_{SSFA}(K_{A}))")):
    a = art(d, n)
    if a["heading"] == old:
        a["heading"] = new
save("ch5", d)
print("ok")
