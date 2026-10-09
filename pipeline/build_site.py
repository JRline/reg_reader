#!/usr/bin/env python3
"""
Build the final, self-contained reader site into `site/` (or a given output dir).

The output opens directly from disk — double-click `site/index.html`, no Python or web
server needed. Browsers refuse fetch() on file:// URLs, so instead of copying the feed
JSON as-is, each feed is wrapped in a small .js file that registers its data on
`window.REG_DATA`; app.js loads those with <script> tags when `window.REG_STATIC_SITE`
is set (see loadFeedIndex/loadFeedData in app/app.js).

Pure post-processing: no model calls. Re-run after any change to app/ or feeds/.

Usage: python3 pipeline/build_site.py [out_dir]   (default: <repo>/site)
"""
import json
import re
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
APP = REPO / "app"
FEEDS = REPO / "feeds"


def js_assign(key, value):
    # ensure_ascii=False keeps Japanese readable in the output; escape "</" so a feed string
    # can never terminate the surrounding <script> context, and U+2028/2029 which are valid
    # in JSON but were line terminators in older JS engines.
    payload = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
    payload = payload.replace("</", "<\\/").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    return f"(window.REG_DATA=window.REG_DATA||{{}})[{json.dumps(key)}]={payload};\n"


FORMULA_TOKEN_RE = re.compile(r"\s*(?:(\d+(?:\.\d+)?%?)|([A-Za-z_][A-Za-z0-9_]*)|(>=|<=|[-+*/(),=^]))")
FORMULA_FUNCS = {"max", "min", "sqrt", "exp", "ln", "abs", "sum", "Phi"}
FORMULA_INDEX_RE = re.compile(r"^[a-z]$")  # summation index (sum(j, ...)) — not a variable


def load_formulas(src, feed):
    """Optional formulas.json + notation.json beside a feed. Validated here so a typo in a
    hand-written formula fails the build instead of rendering a broken expression."""
    fpath, npath = src / "formulas.json", src / "notation.json"
    if not fpath.exists():
        return None, None
    formulas = json.loads(fpath.read_text(encoding="utf-8"))
    notation = json.loads(npath.read_text(encoding="utf-8")) if npath.exists() else {"symbols": {}}
    node_ids = set()
    stack = [feed["root"]]
    while stack:
        n = stack.pop()
        node_ids.add(n["id"])
        stack.extend(n.get("children", []))
    variables = formulas.get("variables", {})
    errors = []
    for vid, v in variables.items():
        if v.get("defined_at") and v["defined_at"] not in node_ids:
            errors.append(f"variable {vid}: defined_at {v['defined_at']} is not a node in the feed")
    for f in formulas.get("formulas", []):
        if f["node_id"] not in node_ids:
            errors.append(f"formula {f['id']}: node_id {f['node_id']} is not a node in the feed")
        for line in f["lines"]:
            pos, depth = 0, 0
            while pos < len(line):
                m = FORMULA_TOKEN_RE.match(line, pos)
                if not m or m.end() == pos:
                    if line[pos:].strip():
                        errors.append(f"formula {f['id']}: can't parse {line[pos:]!r}")
                    break
                ident, op = m.group(2), m.group(3)
                if ident and ident not in FORMULA_FUNCS and ident not in variables and not FORMULA_INDEX_RE.match(ident):
                    errors.append(f"formula {f['id']}: unknown variable {ident!r}")
                if op == "(":
                    depth += 1
                elif op == ")":
                    depth -= 1
                pos = m.end()
            if depth != 0:
                errors.append(f"formula {f['id']}: unbalanced parentheses in {line!r}")
    missing = sorted(set(variables) - set(notation.get("symbols", {})))
    if missing:
        print(f"  note: {src.name}: no notation symbol for {missing} (the id is shown instead)")
    if errors:
        sys.exit("build_site: formula errors:\n  " + "\n  ".join(errors))
    return formulas, notation


def load_tables(src, feed):
    """Optional tables.json: {tables: {<token id>: {node_id, header_rows, rows_ja, rows_en, …}}}.
    Every {{T:id}} token in the feed text should have an entry (a missing one renders as a
    visible "not yet transcribed" placeholder, so it's a warning, not an error)."""
    tpath = src / "tables.json"
    text = json.dumps(feed, ensure_ascii=False)
    tokens = set(re.findall(r"\{\{T:([^}]+)\}\}", text))
    ftokens = set(re.findall(r"\{\{F:([^}]+)\}\}", text))
    fpath = src / "formulas.json"
    anchors = {f.get("anchor") for f in json.loads(fpath.read_text(encoding="utf-8")).get("formulas", [])} if fpath.exists() else set()
    if ftokens - anchors:
        print(f"  note: {src.name}: {len(ftokens - anchors)} formula image(s) not yet transcribed: {sorted(ftokens - anchors)[:8]}…")
    if not tpath.exists():
        if tokens:
            print(f"  note: {src.name}: {len(tokens)} table token(s) but no tables.json")
        return None
    tables = json.loads(tpath.read_text(encoding="utf-8"))
    entries = tables.get("tables", {})
    errors = []
    for tid, t in entries.items():
        for key in ("rows_ja", "rows_en"):
            if key in t and t[key] is not None and t.get("rows_ja") and len(t[key]) != len(t["rows_ja"]):
                errors.append(f"table {tid}: {key} has {len(t[key])} rows, rows_ja has {len(t['rows_ja'])}")
    if tokens - set(entries):
        print(f"  note: {src.name}: {len(tokens - set(entries))} table(s) not yet transcribed: {sorted(tokens - set(entries))}")
    if errors:
        sys.exit("build_site: table errors:\n  " + "\n  ".join(errors))
    return tables


def build_index_html():
    html = (APP / "index.html").read_text(encoding="utf-8")
    # The dev index.html cache-busts via document.write + Date.now() (CLAUDE.md rule 8).
    # Opened from file:// there's no HTTP cache to fight, so swap in plain static tags.
    html, n_css = re.subn(
        r"<script>\s*(?://[^\n]*\n\s*)*document\.write\('<link rel=\"stylesheet\" href=\"style\.css\?v=' \+ Date\.now\(\) \+ '\">'\);\s*</script>",
        '<link rel="stylesheet" href="style.css">',
        html,
    )
    html, n_js = re.subn(
        r"<script>\s*document\.write\('<scr' \+ 'ipt src=\"app\.js\?v=' \+ Date\.now\(\) \+ '\"></scr' \+ 'ipt>'\);\s*</script>",
        '<script>window.REG_STATIC_SITE = true;</script>\n  <script src="app.js"></script>',
        html,
    )
    if n_css != 1 or n_js != 1:
        sys.exit(f"build_site: app/index.html no longer matches the expected cache-bust tags "
                 f"(css={n_css}, js={n_js}); update build_index_html().")
    return html


def main():
    out = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else REPO / "site"
    if out.exists():
        shutil.rmtree(out)
    (out / "data").mkdir(parents=True)

    (out / "index.html").write_text(build_index_html(), encoding="utf-8")
    for name in ("app.js", "style.css"):
        shutil.copy2(APP / name, out / name)

    index = json.loads((FEEDS / "index.json").read_text(encoding="utf-8"))
    site_index = {"feeds": []}
    for entry in index["feeds"]:
        feed_id = entry["feed_id"]
        src = FEEDS / entry.get("path", feed_id)
        manifest = json.loads((src / "manifest.json").read_text(encoding="utf-8"))
        feed = json.loads((src / "feed.json").read_text(encoding="utf-8"))
        if feed.get("feed_id") not in (None, feed_id):
            sys.exit(f"build_site: {src}/feed.json says feed_id={feed.get('feed_id')!r}, index says {feed_id!r}")
        formulas, notation = load_formulas(src, feed)
        bundle = {"manifest": manifest, "feed": feed}
        if formulas:
            bundle["formulas"] = formulas
            bundle["notation"] = notation
        tables = load_tables(src, feed)
        if tables:
            bundle["tables"] = tables
        (out / "data" / f"{feed_id}.js").write_text(js_assign(f"feed:{feed_id}", bundle), encoding="utf-8")
        site_index["feeds"].append({
            "feed_id": feed_id,
            "title_ja": manifest.get("title_ja"),
            "title_en": manifest.get("title_en"),
        })
    (out / "data" / "index.js").write_text(js_assign("index", site_index), encoding="utf-8")

    print(f"Built {len(site_index['feeds'])} feeds into {out}")
    print(f"Open {out / 'index.html'} directly in a browser.")


if __name__ == "__main__":
    main()
