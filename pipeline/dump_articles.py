#!/usr/bin/env python3
"""Print an extraction's articles (paragraphs, item segments, tokens) for translation.
Usage: python3 dump_articles.py <extraction.json> <first article number> [<last>]"""
import json, sys
d = json.load(open(sys.argv[1]))
nums = [a.get("key") or a["number"] for a in d["articles"]]
i = nums.index(sys.argv[2]); j = nums.index(sys.argv[3]) if len(sys.argv) > 3 else i
for a in d["articles"][i:j + 1]:
    print(f"=== {a.get('key') or a['number']} {a['number']} ({a['heading']}) {' / '.join(p['number'] + ' ' + p['heading'] for p in a['path'])}{' [DELETED]' if a['deleted'] else ''}")
    for p in a["paragraphs"]:
        print(f"-- p{p['number'] or '1'}")
        for s in p["segments"]:
            print(f"   [{s['marker'] or '·'}] {s['text']}")
