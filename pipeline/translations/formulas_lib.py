"""Helpers for a chapter-part formulas file (see ch3_formulas.py for the full example).

A parts file (e.g. ch4a_formulas.py) does:

    from formulas_lib import *
    TAG = "ch4a"                       # unique per file; formula ids become f-<TAG>-<anchor>
    C = "fsa-basel-cap-jp.ch4."
    v("PD", "PD", "デフォルト確率", "Probability of default", C + "art130.p1")   # variable
    f("p160i0", C + "art130.p1", ["K = LGD * (Phi(...) - PD)"])                  # block formula
    inline("p160i1", C + "art130.p1", "PD")                                       # inline symbol

`python3 merge_extras.py` imports every *_formulas.py (except ch3_formulas.py) and merges them
into feeds/fsa-basel-cap-jp/formulas.json + notation.json. Variable ids are GLOBAL across
the feed — prefix yours (e.g. IRB_PD) unless it is the same quantity as an existing one, and
check `formulas.json` first (`python3 -c "import json;print(sorted(json.load(open('feeds/fsa-basel-cap-jp/formulas.json'))['variables']))"`).
"""
V = {}  # id -> (symbol, name_ja, name_en, desc_ja, desc_en, defined_at)
F = []
TAG = "x"


def v(i, sym, nj, ne, at, dj="", de=""):
    V[i] = (sym, nj, ne, dj, de, at)


def f(anchor, node, lines, display="block", lj="", le="", nj="", ne="", source="transcribed"):
    F.append({"id": f"f-{TAG}-{anchor}", "anchor": anchor, "node_id": node, "display": display, "lines": lines,
              "label_ja": lj, "label_en": le, "source": source, "note_ja": nj, "note_en": ne})


def inline(anchor, node, var):
    f(anchor, node, [var], display="inline")
