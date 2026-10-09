#!/usr/bin/env python3
"""Write translation files from a batch module: python3 write_batch.py <batch.py> <out_dir>.
The batch module defines ARTICLES = [ {number, heading_en, summary_ja, summary_en,
paragraphs: [...], terms?: [...], sections_en?: {...}} ]."""
import json, re, runpy, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import ja_refs
mod = runpy.run_path(sys.argv[1])
out = Path(sys.argv[2]); out.mkdir(parents=True, exist_ok=True)
TABLES_PATH = Path(__file__).parent.parent.parent / "feeds" / "fsa-basel-cap-jp" / "tables.json"
if mod.get("TABLES"):
    data = json.loads(TABLES_PATH.read_text(encoding="utf-8")) if TABLES_PATH.exists() else {
        "_comment": "Tables from the source PDF, keyed by the {{T:<id>}} token extract_chapter_v2.py left in the text. Cells hand-checked against the page images; rows_en is the English rendering of the same grid. A cell is a string, or {text, colspan, rowspan}; null marks a cell covered by a neighbour's span. header_rows = how many leading rows are headers.",
        "tables": {}}
    data["tables"].update(mod["TABLES"])
    TABLES_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("tables:", ", ".join(mod["TABLES"]))
for a in mod.get("ARTICLES", []):
    nums = [ja_refs.k2i(x) for x in re.findall(ja_refs.N, a["number"])]
    key = "art" + "-".join(str(n) for n in nums)
    (out / f"{key}.json").write_text(json.dumps(a, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("wrote", key)
