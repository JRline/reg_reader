#!/usr/bin/env python3
"""Merge every chapter-part extra into the feed's data files (idempotent):
  *_tables.json   {"<table id>": {...}}      -> feeds/fsa-basel-cap-jp/tables.json
  *_formulas.py   (formulas_lib)             -> formulas.json + notation.json
Usage: python3 pipeline/translations/merge_extras.py"""
import json, runpy, sys
from pathlib import Path
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
FEED = HERE.parent.parent / "feeds" / "fsa-basel-cap-jp"

tp = FEED / "tables.json"
tables = json.loads(tp.read_text(encoding="utf-8"))
n = 0
for fp in sorted(HERE.glob("*_tables.json")):
    d = json.loads(fp.read_text(encoding="utf-8"))
    tables["tables"].update(d); n += len(d)
tp.write_text(json.dumps(tables, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
print(f"tables: merged {n}, total {len(tables['tables'])}")

fpath, npath = FEED / "formulas.json", FEED / "notation.json"
formulas = json.loads(fpath.read_text(encoding="utf-8")); notation = json.loads(npath.read_text(encoding="utf-8"))
nf = nv = 0
for fp in sorted(HERE.glob("*_formulas.py")):
    if fp.name == "ch3_formulas.py":
        continue
    import formulas_lib as L
    L.V.clear(); L.F.clear()
    runpy.run_path(str(fp))
    tags = {x["id"].split("-")[1] for x in L.F}
    for vid, (sym, nj, ne, dj, de, at) in L.V.items():
        formulas["variables"][vid] = {"name_ja": nj, "name_en": ne, "desc_ja": dj, "desc_en": de, "defined_at": at}
        notation["symbols"][vid] = sym
    formulas["formulas"] = [x for x in formulas["formulas"] if x["id"].split("-")[1] not in tags] + list(L.F)
    nf += len(L.F); nv += len(L.V)
fpath.write_text(json.dumps(formulas, ensure_ascii=False, indent=2), encoding="utf-8")
npath.write_text(json.dumps(notation, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"formulas: merged {nf}, variables {nv}; total {len(formulas['formulas'])}")
