# Batch extraction agent — feed this file alone, run with tool access, no API needed

You're reading this because you were scheduled/invoked as a fresh session (likely
running Sonnet) with **file read/write and Bash access to this project**, and no memory
of the conversation that built it. That changes what "processing a prompt" means for
you compared to a plain chat model: you don't reply with JSON in a chat message — you
**write files and run scripts yourself**, the same way a human operator would, and you
generate the translation/analysis content directly from your own capability instead of
calling any external API. There is no `ANTHROPIC_API_KEY` in this environment and you
don't need one.

If anything here is ambiguous or you want more detail than this brief gives, the full
source docs are in this repo — read them, you have the tools to:
- `pipeline/EXTRACTION_GUIDE.md` — the step-by-step pipeline walkthrough
- `pipeline/chatbot_template.md` — the canonical per-paragraph instructions this brief condenses
- `pipeline/schema/rule-feed.schema.json` — the full data contract, authoritative over anything paraphrased here

## What this project is

A bilingual (Japanese/English) reader for Japanese financial regulation (an FSA
capital-adequacy notification). It renders long legal sentences with color-coded visual
cues (conditions, provisos, exceptions, enumerated items, parentheticals, defined terms)
and makes cross-references clickable, including ones that jump to other laws that have
been separately digitized as their own feeds. `feeds/fsa-basel-cap-jp/feed.json` is the
live data the app reads; `pipeline/raw/*.json` are the per-paragraph building blocks that
get merged into it.

## Your job, end to end

1. **Figure out the scope.** Default to continuing Chapter 2 of `fsa-basel-cap-jp`
   (`feeds/fsa-basel-cap-jp/ch2_outline.tsv` / `pipeline/source/ch2_articles.json`)
   unless you were told to target something else (a different chapter, a specific list
   of articles, a different regulation entirely). If the target chapter hasn't been
   extracted yet, run `extract_chapter.py` first — see `EXTRACTION_GUIDE.md` Step 1 for
   how to find the right start/end markers in the PDF.

2. **Generate the prompt files** (if they don't already exist for your scope):
   ```
   python3 pipeline/make_prompts.py <feed_id> <chapter_id> <articles.json> pipeline/prompts
   ```
   This skips anything already merged into `feed.json`, so it's always safe to re-run.

3. **Process every outstanding `pipeline/prompts/*.txt` file yourself.** Each one is a
   fully-specified instruction for exactly one paragraph (or one article summary, for
   `*.summary.txt` files). For each:
   - Read the prompt.
   - Do the actual translation/analysis work described in it, to the same standard
     you'd hold yourself to answering directly — see "Hard requirements" below.
   - Write your result as `pipeline/raw/<same-basename>.json` (e.g.
     `fsa-basel-cap-jp.ch2.art5.p2.txt` → `fsa-basel-cap-jp.ch2.art5.p2.json`).

   **Do not mechanically wrap `text_ja` into one clause with an empty `text_en` to move
   faster.** That exact failure mode already happened once on this project — a batch of
   87 placeholder files got written with real Japanese source text but blank
   translations and zero extracted references, and it slipped past the schema validator
   because an empty translation trivially "reconstructs" against an empty clause list.
   It was caught later by eye, not by tooling at the time. Tooling now rejects it
   automatically (`batch_ingest.py` refuses to merge any chunk with empty `text_en`,
   and warns on suspiciously coarse clause counts or citation-shaped text with no
   extracted refs) — but that means half-done work now fails loudly instead of merging
   silently. Do the real work per file; don't let this become the second time it happens.

4. **Merge a batch once you have raw files for it:**
   ```
   python3 pipeline/batch_ingest.py <feed_id> <chapter_id> <chapter_number> <chapter_heading> <articles.json>
   ```
   Read its output carefully:
   - `REJECTED` articles: your own placeholder-detection gate fired. Go fix the named
     raw file(s) for real and re-run — do not delete the check to make it pass.
   - Other warnings (clause-reconstruction mismatch, a ref not found verbatim in the
     text, a specific-provision citation with no `external_item_summary`): fix the
     specific raw file named, don't ignore them, they've each caught real bugs before.
   - Missing-raw-files reports for articles you haven't gotten to yet are expected and fine.

5. **Once an article's paragraphs are merged, generate and process its summary:**
   ```
   python3 pipeline/make_summary_prompts.py <feed_id> <chapter_id> pipeline/prompts
   ```
   Process the resulting `*.summary.txt` files the same way as step 3, then re-run
   `batch_ingest.py` — it picks up `pipeline/raw/<article_id>.summary.json` automatically.

6. **Validate before considering anything done:**
   ```bash
   python3 -c "
   import json, jsonschema
   schema = json.load(open('pipeline/schema/rule-feed.schema.json'))
   feed = json.load(open('feeds/<feed_id>/feed.json'))
   jsonschema.validate(instance=feed, schema=schema)
   print('PASSED')
   "
   ```

7. **Report back**, even though no one's watching in real time: how many
   articles/paragraphs you completed, every warning you had to resolve and how, and
   anything that needs a human call — most likely a **formula gap** (see below) that
   needs hand-transcription from the PDF, or a clause split you're genuinely unsure about.

## Hard requirements for every JSON you write

1. Concatenating all `clauses_ja[].text` fields in order must reconstruct `text_ja`
   **exactly**, character for character. Same, independently, for `clauses_en` against
   `text_en` — the two are separate segmentations of the same meaning; English may merge
   or reorder clauses relative to Japanese, that's fine, but each language's own
   concatenation must be exact. Check this yourself before writing the file — don't rely
   on `batch_ingest.py` to catch it after the fact.
2. Every `raw_text` in `refs` must be a verbatim substring of `text_ja`, including text
   only found inside parentheses. Don't paraphrase a citation when extracting it — this
   caught two real fabricated-looking citations earlier in this project, both from
   assuming a paren closed sooner than it actually did.
3. `text_en` must be an actual translation. Never leave it empty, and never leave a
   Japanese term untranslated inside an otherwise-English sentence.
4. **Known content gap:** the source PDF has mathematical formulas embedded as images,
   lost during text extraction. You'll sometimes see a sentence like
   "次の算式により得られる比率について" (regarding the ratio obtained by the following
   formula) with nothing after it. This is expected — do not invent, reconstruct, or
   guess at a formula that isn't in the text you were given. Translate faithfully around
   the gap and move on.

## Output shape (per-paragraph prompts — `*.p<N>.txt`)

```
{
  "id": "<given in the prompt>",
  "number": "<given in the prompt>",
  "heading": "<given in the prompt>",
  "text_ja": "<verbatim copy of the source text>",
  "text_en": "<accurate English translation, preserving legal register>",
  "clauses_ja": [
    {"clause_type": "<main|conditional|proviso|exception|enumeration_stem|enumeration_item|parenthetical|definition>",
     "text": "<verbatim substring of text_ja>"}
  ],
  "clauses_en": [
    {"clause_type": "<same enum>", "text": "<verbatim substring of text_en>"}
  ],
  "refs": [
    {"raw_text": "<verbatim citation phrase>",
     "text_en": "<the same citation as it reads in text_en>",
     "scope": "internal | external",
     "external_name": "<law/notification name if external, else null>",
     "external_item_summary_ja": "<one line on what THIS SPECIFIC cited provision says, or null>",
     "external_item_summary_en": "<same in English, or null>",
     "external_item_summary_confidence": "stated_in_text | general_knowledge | null"}
  ],
  "defined_terms": [
    {"term_ja": "<term>", "term_en": "<translation>", "expands_to_ja": "<see below, else null>"}
  ]
}
```

Notes:
- `conditional` = 場合/とき clauses. `proviso` = ただし-clauses. `parenthetical` = kakko
  (　) asides. `enumeration_stem` = the sentence introducing a 一/二/三 list;
  `enumeration_item` = each numbered item in it.
- `external_item_summary_*` describes the SPECIFIC cited provision, never the external
  law as a whole. If the citing sentence already explains it inline (very common — look
  for "...という" / "...をいう" right next to the citation), restate that and set
  confidence `stated_in_text`. Otherwise give your best understanding but set
  `general_knowledge` — this must read as a flagged, unverified guess, not a stated fact.
- `defined_terms`: only a term THIS text explicitly defines (the "...という" pattern),
  not one it merely uses. `expands_to_ja` is set ONLY when the term is shorthand for a
  longer Japanese phrase named earlier in the same sentence (e.g. an ordinance's full
  name) — never put an English translation there, that's what `term_en` is for, and
  mixing the two up previously leaked English text into a field the rest of the
  pipeline treats as Japanese.
- Empty array if a field has nothing to report — never omit a key.

## Output shape (article-summary prompts — `*.summary.txt`)

```
{"summary_ja": "<one sentence, plain Japanese>", "summary_en": "<one sentence, plain English>"}
```

## Self-check before writing each file

- Clauses reconstruct exactly, in both languages? (Concatenate them yourself and compare.)
- Every ref's `raw_text` actually appears in `text_ja`, parens included?
- Is `text_en` a genuine, complete translation — not empty, not a template, not leaving
  a Japanese term embedded untranslated?
- Any citation with a specific article/paragraph/item number has a filled-in
  `external_item_summary_ja`/`_en` (with honest confidence), not nulls?

If you can't confidently answer yes to all four for a given paragraph, don't write the
file yet — take more care on that one rather than moving fast and letting
`batch_ingest.py`'s rejection gate be the first thing to notice.
