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
        (out / "data" / f"{feed_id}.js").write_text(
            js_assign(f"feed:{feed_id}", {"manifest": manifest, "feed": feed}), encoding="utf-8")
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
