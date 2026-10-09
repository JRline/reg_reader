#!/usr/bin/env python3
"""Render the PDF region of a {{F:<id>}} formula image or {{T:<id>}} table to a PNG, to read it.
Usage: python3 pipeline/crop_token.py <extraction.json> <id> [<id> ...] [--out DIR] [--dpi 220] [--pad 8]
Writes DIR/<id>.png (default DIR: /tmp/crops) and prints the path — open it with the Read tool.
A formula id looks like p101i8 (page 101, image 8); a table id like p326t0. For a table
that continues over a page break, also crop its continuation (the next page's t0)."""
import json, subprocess, sys
from pathlib import Path
args = sys.argv[1:]
opt = {"--out": "/tmp/crops", "--dpi": "220", "--pad": "8"}
for k in list(opt):
    if k in args:
        i = args.index(k); opt[k] = args[i + 1]; del args[i:i + 2]
ext = json.load(open(args[0])); ids = args[1:]
items = {x["id"]: x for x in ext["images"]}
items.update({x["id"]: x for x in ext["tables"]})
out = Path(opt["--out"]); out.mkdir(parents=True, exist_ok=True)
dpi, pad = float(opt["--dpi"]), float(opt["--pad"])
for i in ids:
    it = items.get(i)
    if not it:
        print("unknown id", i); continue
    x0, y0, x1, y1 = it["bbox"]
    s = dpi / 72
    X, Y = max(0, int((x0 - pad) * s)), max(0, int((y0 - pad) * s))
    W, H = int((x1 - x0 + 2 * pad) * s), int((y1 - y0 + 2 * pad) * s)
    dest = out / i
    subprocess.run(["pdftoppm", "-r", str(int(dpi)), "-f", str(it["page"]), "-l", str(it["page"]), "-x", str(X), "-y", str(Y), "-W", str(W), "-H", str(H), "-png", "-singlefile", "pipeline/source/saishu1.pdf", str(dest)], check=True)
    print(f"{dest}.png  (page {it['page']}, bbox {it['bbox']})")
