#!/usr/bin/env python3
"""
Fills chatbot_template.md's prompt for every paragraph of every article in a chapter,
writing one ready-to-paste .txt file per paragraph. Skips articles already fully
processed (present with real content in feed.json), so re-running after ingesting a
batch only regenerates what's still outstanding.

Usage:
    python3 make_prompts.py <feed_id> <chapter_id> <articles.json> <out_dir>

Example:
    python3 make_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/source/ch2_articles.json pipeline/prompts
"""
import json
import re
import sys
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent
FEEDS_DIR = PIPELINE_DIR.parent / "feeds"

KANJI_DIGITS = {"〇": 0, "一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}


def kanji_to_int(s: str) -> int:
    if not s:
        return 0
    if "十" in s:
        tens_part, _, ones_part = s.partition("十")
        tens = KANJI_DIGITS.get(tens_part, 1) if tens_part else 1
        ones = KANJI_DIGITS.get(ones_part, 0) if ones_part else 0
        return tens * 10 + ones
    return KANJI_DIGITS.get(s, 0)


def article_number_to_slug(number: str) -> str:
    m = re.match(r"第([一二三四五六七八九十百]+)条(の([一二三四五六七八九十]+))?", number)
    main = kanji_to_int(m.group(1))
    sub = kanji_to_int(m.group(3)) if m.group(3) else None
    return f"art{main}" + (f"-{sub}" if sub else "")


PROMPT_TEMPLATE = '''You are populating structured data for a Japanese regulatory text reader. You will be given
one Article of Japanese legal/regulatory text. Output ONLY a single JSON object — no prose,
no markdown fences, no explanation before or after.

Known issue in the source text: mathematical formulas in the original PDF were embedded
as images, not text, so they were lost during extraction. You may see a sentence like
"次の算式により得られる比率について" (regarding the ratio obtained by the following
formula) with nothing after it. This is expected — do NOT invent, reconstruct, or guess
at a formula that isn't present in the source text given to you. Translate faithfully
around the gap and move on; its absence is not an error for you to fix.

Context (do not translate, for your reference only): {context}

Source text (Japanese, verbatim, id={anchor_id}):
"""
{source_text}
"""

Produce JSON with exactly this shape:

{{
  "id": "{anchor_id}",
  "number": {number_json},
  "heading": {heading_json},
  "text_ja": "<verbatim copy of the source text>",
  "text_en": "<accurate English translation, preserving legal register>",
  "clauses_ja": [
    {{"clause_type": "<one of: main, conditional, proviso, exception,
                      enumeration_stem, enumeration_item, parenthetical, definition>",
     "text": "<verbatim substring of text_ja>"}}
    // Break text_ja into ordered clauses covering the whole sentence.
    // Concatenating all "text" fields in order must reconstruct the original text_ja exactly.
    // Use "conditional" for 場合/とき clauses, "proviso" for ただし-clauses,
    // "parenthetical" for kakko (　) asides, "enumeration_stem" for the sentence introducing
    // a 一/二/三 list and "enumeration_item" for each numbered item.
  ],
  "clauses_en": [
    {{"clause_type": "<same enum as above>", "text": "<verbatim substring of text_en>"}}
    // Independently break text_en into ordered clauses covering the whole English sentence.
    // Concatenating all "text" fields in order must reconstruct text_en exactly. Does NOT need
    // the same clause count as clauses_ja, but the clause_type sequence should tell the same
    // structural story.
  ],
  "refs": [
    {{"raw_text": "<verbatim citation phrase, e.g. 前条第二項>",
     "text_en": "<the corresponding phrase as it appears in text_en>",
     "scope": "internal | external",
     "external_name": "<law/notification name if scope=external, else null>",
     "external_item_summary_ja": "<see below, else null>",
     "external_item_summary_en": "<see below, else null>",
     "external_item_summary_confidence": "<stated_in_text | general_knowledge | null>"}}
    // List every cross-reference found in text_ja, INCLUDING ones that appear only inside a
    // parenthetical/kakko aside — do not skip a citation just because it's inside brackets.
    // Do not attempt to resolve a target id — just extract the citation phrase exactly as
    // written, in both languages.
    //
    // For scope=external refs ONLY, also fill in external_item_summary_*: a one-line
    // description of what THAT SPECIFIC cited article/paragraph/item says — NOT a summary of
    // the external law as a whole. If the citing sentence already explains the cited provision
    // inline (e.g. "...をいう"), restate that and set confidence "stated_in_text". Otherwise
    // give your best general-knowledge understanding and set confidence "general_knowledge" —
    // this must be visibly flagged as unverified in the reader, never presented as fact.
  ],
  "defined_terms": [
    {{"term_ja": "<term>", "term_en": "<your translation of the term>",
     "expands_to_ja": "<see below, else null>"}}
    // Only terms explicitly defined in THIS text (e.g. "...という。" pattern), not terms
    // merely used.
    // Set expands_to_ja ONLY when this term is a shorthand for a longer Japanese phrase
    // named earlier in the same sentence (e.g. a term standing in for an ordinance's
    // full name). Leave null for a term that's being coined/glossed rather than
    // abbreviating something. Never put an English translation in this field.
  ]
}}

If a field has nothing to report, use an empty array — never omit a key.'''


def load_already_processed(feed_id: str, chapter_id: str) -> set:
    feed_path = FEEDS_DIR / feed_id / "feed.json"
    if not feed_path.exists():
        return set()
    feed = json.loads(feed_path.read_text(encoding="utf-8"))
    chapter = next((c for c in feed["root"]["children"] if c["id"] == chapter_id), None)
    if not chapter:
        return set()
    return {a["id"] for a in chapter["children"] if a.get("text_ja") or a.get("children")}


def main():
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)
    feed_id, chapter_id, articles_json, out_dir = sys.argv[1:5]
    out_path = Path(out_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    articles = json.loads(Path(articles_json).read_text(encoding="utf-8"))
    already_processed = load_already_processed(feed_id, chapter_id)

    written, skipped = 0, 0
    for art in articles:
        slug = article_number_to_slug(art["number"])
        article_id = f"{chapter_id}.{slug}"
        if article_id in already_processed:
            skipped += 1
            continue
        n_paragraphs = len(art["paragraphs"])
        for i, para in enumerate(art["paragraphs"]):
            anchor_id = f"{article_id}.p{i+1}"
            context_parts = [f"Article {art['number']}"]
            if art["heading"]:
                context_parts.append(f"({art['heading']})")
            if n_paragraphs > 1:
                context_parts.append(f"— this is paragraph {i+1} of {n_paragraphs}")
            context = " ".join(context_parts)

            prompt = PROMPT_TEMPLATE.format(
                context=context,
                anchor_id=anchor_id,
                source_text=para["text"],
                number_json=json.dumps(para["number"], ensure_ascii=False),
                heading_json=json.dumps(art["heading"] if i == 0 else None, ensure_ascii=False),
            )
            (out_path / f"{anchor_id}.txt").write_text(prompt, encoding="utf-8")
            written += 1

    print(f"Wrote {written} prompt files to {out_path}/")
    print(f"Skipped {skipped} articles already processed: {sorted(already_processed)}")


if __name__ == "__main__":
    main()
