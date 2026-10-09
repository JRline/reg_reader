#!/usr/bin/env python3
"""Print numbered item segments of an extraction's single big paragraph (Chapter 1's 第一条).
Usage: python3 pipeline/dump_segments.py pipeline/source/ch1_v2.json <first idx> <last idx>"""
import json, sys
d = json.load(open(sys.argv[1]))
segs = d["articles"][0]["paragraphs"][0]["segments"]
for i in range(int(sys.argv[2]), int(sys.argv[3]) + 1):
    s = segs[i]
    print(f"[{i}] (L{s['level']} {s['marker'] or '-'}) {s['text']}")
