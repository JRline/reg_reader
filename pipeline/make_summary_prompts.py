#!/usr/bin/env python3
"""
Generates the second-stage "article summary" prompt (see chatbot_template.md) for every
article in a chapter that has real paragraph content but no summary yet. Run this AFTER
batch_ingest.py, since it needs the assembled text_ja/text_en that step produces.

Usage:
    python3 make_summary_prompts.py <feed_id> <chapter_id> <out_dir>
"""
import json
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent
FEEDS_DIR = PIPELINE_DIR.parent / "feeds"

TEMPLATE = '''You will be given the full text of one Article of Japanese regulatory text, with its
official English translation. Write a one-sentence, plain-language summary of what this
Article actually requires or establishes — the kind of line a compliance officer would
want as a preview before deciding whether to read the full text. Do not just restate the
heading. Output ONLY this JSON object, no prose:

{{"summary_ja": "<one sentence, plain Japanese>", "summary_en": "<one sentence, plain English>"}}

Japanese text: """{ja}"""
English text: """{en}"""'''


def collect_text(node, lang_key):
    parts = [node[lang_key]] if node.get(lang_key) else []
    for child in node.get("children", []):
        parts.extend(collect_text(child, lang_key))
    return parts


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id, out_dir = sys.argv[1:4]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    feed = json.loads((FEEDS_DIR / feed_id / "feed.json").read_text(encoding="utf-8"))
    chapter = next(c for c in feed["root"]["children"] if c["id"] == chapter_id)

    written, skipped = 0, 0
    for article in chapter["children"]:
        if article.get("summary_ja"):
            skipped += 1
            continue
        ja_parts = collect_text(article, "text_ja")
        en_parts = collect_text(article, "text_en")
        if not ja_parts:
            skipped += 1  # still a stub, no content to summarize yet
            continue
        prompt = TEMPLATE.format(ja="".join(ja_parts), en="".join(en_parts))
        (out_path / f"{article['id']}.summary.txt").write_text(prompt, encoding="utf-8")
        written += 1

    print(f"Wrote {written} summary prompts to {out_path}/, skipped {skipped} (no content yet or already summarized).")
    print("Run these through Haiku, save replies as pipeline/raw/<article_id>.summary.json,")
    print("then re-run batch_ingest.py — it picks up summary files automatically.")


if __name__ == "__main__":
    main()
