#!/usr/bin/env python3
"""
Merges every article in a chapter whose paragraph raw files are all present into
feed.json, reusing ingest.py's resolution/QA logic for each one. Articles missing
one or more raw files are reported and skipped (safe to re-run once you have more).

Usage:
    python3 batch_ingest.py <feed_id> <chapter_id> <chapter_number> <chapter_heading> <articles.json>

Example:
    python3 batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
"""
import json
import sys
from pathlib import Path

import ingest  # reuse build_article_node / merge_into_feed / registries / validate

PIPELINE_DIR = Path(__file__).parent


def main():
    if len(sys.argv) != 6:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id, chapter_number, chapter_heading, articles_json = sys.argv[1:6]

    articles = json.loads(Path(articles_json).read_text(encoding="utf-8"))
    schema = ingest.load_schema()
    term_registry, term_registry_path = ingest.load_term_registry(feed_id)
    external_refs_registry = ingest.load_external_refs_registry()

    # Preserve heading_en already set by build_skeleton.py (from ch2_outline.tsv) — this
    # script only ever adds real content, it doesn't have its own English-heading data.
    feed_path = ingest.FEEDS_DIR / feed_id / "feed.json"
    existing_heading_en = {}
    if feed_path.exists():
        existing_feed = json.loads(feed_path.read_text(encoding="utf-8"))
        chapter = next((c for c in existing_feed["root"]["children"] if c["id"] == chapter_id), None)
        if chapter:
            existing_heading_en = {a["id"]: a.get("heading_en") for a in chapter["children"]}

    merged, skipped, rejected, all_warnings = [], [], [], []
    for art in articles:
        slug = ingest_article_slug(art["number"])
        article_id = f"{chapter_id}.{slug}"
        expected = [ingest.RAW_DIR / f"{article_id}.p{i+1}.json" for i in range(len(art["paragraphs"]))]
        missing = [p.name for p in expected if not p.exists()]
        if missing:
            skipped.append((article_id, missing))
            continue

        ingest.ARTICLE_META[article_id] = {
            "number": art["number"],
            "heading": art["heading"],
            "heading_en": existing_heading_en.get(article_id),
        }
        article_node, warnings = ingest.build_article_node(article_id, feed_id, term_registry, external_refs_registry)

        # A placeholder/never-translated chunk is not a "flag for review" situation —
        # it's actively wrong content. Never let it into feed.json, even with a warning.
        blocking = [w for w in warnings if "was never actually translated" in w]
        if blocking:
            rejected.append((article_id, blocking))
            all_warnings.extend(w for w in warnings if w not in blocking)
            continue

        ingest.merge_into_feed(feed_id, chapter_id, chapter_number, chapter_heading, article_node)
        merged.append(article_id)
        all_warnings.extend(warnings)

    ingest.save_term_registry(term_registry, term_registry_path)

    print(f"Merged {len(merged)} articles: {merged}")
    if skipped:
        print(f"\nSkipped {len(skipped)} articles (missing raw files):")
        for aid, missing in skipped:
            print(f"  {aid}: missing {missing}")
    if rejected:
        print(f"\nREJECTED {len(rejected)} articles (placeholder/untranslated content — NOT merged):")
        for aid, reasons in rejected:
            print(f"  {aid}:")
            for r in reasons:
                print(f"    - {r}")
        print("  Delete these articles' raw files and re-run them through the chatbot properly.")
    if all_warnings:
        print(f"\n{len(all_warnings)} other warnings across merged articles:")
        for w in all_warnings:
            print(f"  - {w}")
    else:
        print("\nNo other warnings.")

    feed_path = ingest.FEEDS_DIR / feed_id / "feed.json"
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    ingest.validate(feed, schema)


def ingest_article_slug(number: str) -> str:
    # Local import to avoid a circular concept — same logic as build_skeleton.py's slug fn.
    import re
    KANJI = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

    def k2i(s):
        if not s:
            return 0
        if "十" in s:
            t, _, o = s.partition("十")
            return (KANJI.get(t, 1) if t else 1) * 10 + (KANJI.get(o, 0) if o else 0)
        return KANJI.get(s, 0)

    m = re.match(r"第([一二三四五六七八九十百]+)条(の([一二三四五六七八九十]+))?", number)
    main = k2i(m.group(1))
    sub = k2i(m.group(3)) if m.group(3) else None
    return f"art{main}" + (f"-{sub}" if sub else "")


if __name__ == "__main__":
    main()
