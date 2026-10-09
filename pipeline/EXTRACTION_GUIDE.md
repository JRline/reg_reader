# Extraction guide: PDF → structured, translated, cross-referenced feed

This walks through turning a chapter of the source PDF into real content in the app,
end to end. Every script takes the chapter/feed as arguments, so the same steps work for
the next chapter or the next regulation entirely.

There are two routes:

- **Route A: in-repo, no chatbot.** This route was used for Chapter 3 and is the one to
  prefer. A pdfplumber extractor keeps tables, image formulas and sub/superscripts.
  Translations are written as per-article JSON files. Citations are found
  deterministically. See the next section.
- **Route B: chatbot batch.** This route was used for Chapter 2. It is described in
  Steps 1–5 below, and is still valid if an external model does the translation.

Steps 5b–7 (post-processing, formulas, validation, build) are shared by both routes.

---

## Route A — in-repo build (Chapter 3)

```bash
pip install pdfplumber jsonschema
# 1. Extract: articles → paragraphs → 号/イロハ segments, plus tables and image positions.
python3 pipeline/extract_chapter_v2.py pipeline/source/saishu1.pdf \
    "第三章 信用リスクの標準的手法" "第四章 信用リスクの内部格付手法" pipeline/source/ch3_v2.json
python3 pipeline/dump_articles.py pipeline/source/ch3_v2.json 第十四条 第十五条   # read text to translate
#    (a chapter that is too big for one sitting can be split into slices translated in parallel by
#     several agents: see `pipeline/translations/AGENT_BRIEF.md`, `check_translations.py`,
#     `crop_token.py`, `merge_extras.py` — that is how Chapters 4–7 were built)
# 2. Translate: one JSON per article in pipeline/translations/ch3/ (see below).
# 3. Build the chapter's nodes into the feed (sections/款/目, articles, paragraphs, clauses, refs).
python3 pipeline/build_chapter.py fsa-basel-cap-jp fsa-basel-cap-jp.ch3 第三章 \
    "信用リスクの標準的手法" "Standardized Approach for Credit Risk" \
    pipeline/source/ch3_v2.json pipeline/translations/ch3
# 4. Then Step 5b (post-passes), 5c (formulas/tables), 6, 7 as below.
```

What the v2 extractor (`extract_chapter_v2.py`) handles that v1 didn't:

- **Tables.** Tables come out as `{{T:<id>}}` tokens in the text, with the cells in the
  extraction's `tables`. Ruled tables are found by pdfplumber. A table split across a page
  break is merged (`continued_on`). Tables that pdfplumber crops wrongly get a bounding
  box in `pipeline/source/table_region_overrides.json`.
- **Image formulas.** These become `{{F:<anchor>}}` tokens (anchor `p<page>i<n>`), inline
  or display depending on image height. The text around them stays intact.
- **Sub/superscripts.** Small glyphs attach to their line as `X_{i}` / `X^{2}`, instead of
  falling onto separate lines.
- **Structure.** 節/款/目 headings (`division` = 目) are detected, as are two-line article
  headings and 削除 ranges (第N条から第M条まで　削除). A display formula that the PDF
  sorts ahead of its item marker is swapped back.

It reproduces v1's Chapter 2 text exactly, so it can be used for any chapter.

**Check the extraction before translating.** Wrapped headings can end up glued to the previous
article's last paragraph (the next article then has no heading), a table that continues over a
page can swallow a second table, and the last chapter runs on into the 附則/別表. Chapters 4–7's
repairs are in `pipeline/fix_extractions.py` and `finish_ch7.py`; do the same for a new chapter
before building.

**Translation files** (`pipeline/translations/<chapter>/<article>.json`) have this shape:

```json
{"number": "第十四条", "heading_en": "...", "summary_ja": "...", "summary_en": "...",
 "paragraphs": ["English for 項1 (with the same {{T:}}/{{F:}} tokens)", "..."],
 "terms": [{"term_ja": "...", "term_en": "..."}],
 "sections_en": {"第六節 第三款 第一目": "Division 1 ..."}}
```

`build_chapter.py` refuses a paragraph whose `{{T}}`/`{{F}}` tokens differ between JA and
EN. Citations come from `ja_refs.py`. That covers:

- law and notice names, including notices cited by full title or
  "(…告示第…号)" with a 「short name」
- 同告示 / 同法 carry-over
- ranges, e.g. 第一号から第四号まで → "items (i) through (iv)"

Each citation's `text_en` is the English form actually present in the translation.
`ja_refs.py`'s `NOTICES`/`LAWS`/`DEFINED_NAMES` tables are where a new instrument goes.

**Tables:** add curated cells to `feeds/<feed>/tables.json` under the token id
(`header_rows`, `rows` of `{ja, en, colspan, rowspan}`; `null` = covered by a span).
`build_site.py` lists any `{{T:}}`/`{{F:}}` token with no entry.

Prerequisites:
```bash
pip install pypdf jsonschema anthropic
export ANTHROPIC_API_KEY=...   # only needed for step 3
```

---

## Step 1 — Extract the chapter's articles from the PDF (Route B)

This is the mechanical half: no chatbot involved, fully deterministic, and it's already
been validated to reproduce the exact hand-verified text from Article 3 character-for-character.

```bash
python3 pipeline/extract_chapter.py pipeline/source/saishu1.pdf "第二章 算式等" "第三章 信用リスクの標準的手法" pipeline/source/ch2_articles.json
```

- Arg 1: the source PDF (already copied into `pipeline/source/`)
- Arg 2/3: the chapter's start and end markers — **use the body heading line, not the
  table-of-contents line.** The ToC line for this chapter has a `（第二条―第十三条）`
  suffix that won't match; the body heading doesn't. If you're not sure what the exact
  body heading string is for a new chapter, check it first:
  ```bash
  python3 -c "
  from pypdf import PdfReader
  r = PdfReader('pipeline/source/saishu1.pdf')
  full = '\n'.join((p.extract_text() or '') for p in r.pages)
  for i, l in enumerate(full.split('\n')):
      if l.strip().startswith('第三章'):   # whatever chapter you're after
          print(i, repr(l.strip()))
  "
  ```
  This prints every line starting with that chapter number — the **second** match
  (first is always the ToC) is your end marker. Same logic for the start marker of
  whatever chapter you're extracting.
- Output: `pipeline/source/ch2_articles.json` — every article's number, heading, and
  paragraphs (already split and cleaned of PDF line-wrap artifacts).

**Sanity check before moving on** — spot-check a couple of articles against the PDF by eye:
```bash
python3 -c "
import json
data = json.load(open('pipeline/source/ch2_articles.json'))
for a in data[:3]:
    print(a['number'], a['heading'], len(a['paragraphs']), 'paragraphs')
"
```

---

## Step 2 — Generate the chatbot prompts

```bash
python3 pipeline/make_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/source/ch2_articles.json pipeline/prompts
```

This fills `chatbot_template.md`'s prompt for every paragraph and writes one `.txt` file
per paragraph to `pipeline/prompts/`, e.g. `fsa-basel-cap-jp.ch2.art5.p2.txt`. It **skips
any article that already has real content** in `feeds/fsa-basel-cap-jp/feed.json`, so
re-running this after a partial batch only regenerates what's still outstanding.

---

## Step 3 — Run the prompts through a model

Two ways to do this — pick whichever fits how you have access:

**A. Automated (if you have `ANTHROPIC_API_KEY`):**
```bash
python3 pipeline/run_haiku_batch.py
```
Calls `claude-haiku-4-5-20251001` on every prompt in `pipeline/prompts/`, saves each
reply as the matching file in `pipeline/raw/`. Skips files that already have output, so
it's safe to stop and resume. If a reply fails to parse as JSON, it's saved as
`<name>.FAILED.txt` for you to inspect instead of silently dropping it.

**B. Manual (company chatbot, no API access):**
Paste each `pipeline/prompts/*.txt` file into the chatbot one at a time, and save its
JSON reply as `pipeline/raw/<same-filename-but-.json>`. Tedious for 80+ files by hand —
worth it only if the Selenium bridge to the internal chatbot isn't built yet.

---

## Step 4 — Merge everything into the feed

```bash
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```

For every article whose paragraph files are **all** present in `pipeline/raw/`, this:
- resolves internal refs (前項/前二項 → actual node ids)
- resolves external law names via the shorthand-term registry
- runs the QA gates: clause-reconstruction check (catches a chatbot response that
  doesn't tile back to the original text) and ref-verbatim check (catches a fabricated
  citation — this caught two real bugs in my own Article 3 draft, so **read the
  warnings**, don't just check the exit code)
- merges the result into `feeds/fsa-basel-cap-jp/feed.json`

Articles missing one or more raw files are reported and skipped — safe to re-run as
more of the batch completes.

---

## Step 5 — Generate and run the summary prompts

Summaries need the *whole* article's assembled text, so this only makes sense after
Step 4 has real paragraph content in the feed:

```bash
python3 pipeline/make_summary_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/prompts
python3 pipeline/run_haiku_batch.py                      # picks up the new *.summary.txt files
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```
That last `batch_ingest.py` re-run is what actually attaches the summaries — it checks
for `pipeline/raw/<article_id>.summary.json` automatically.

---

## Step 5b — Deterministic post-processing (no model calls)

Run in this order after any content change; each is idempotent (a second run changes
nothing):

```bash
python3 pipeline/reresolve_refs.py     fsa-basel-cap-jp fsa-basel-cap-jp.ch2   # internal citations
python3 pipeline/link_external_refs.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2   # cross-feed citations
python3 pipeline/refine_clauses.py     fsa-basel-cap-jp fsa-basel-cap-jp.ch2   # clause splitting
python3 pipeline/annotate_cues.py      fsa-basel-cap-jp fsa-basel-cap-jp.ch2   # in-clause cues (after refine)
```

## Step 5c — Formulas (hand-authored)

The source PDF prints its formulas as images, which extraction can't see. Formulas live
beside the feed in two files, kept apart so the notation can be swapped wholesale:

- `feeds/<feed>/formulas.json` holds:
  - each formula's structure (`lines`, written against variable ids, e.g.
    `"CET1_ratio = CET1 / CRWA >= 4.5%"`)
  - the paragraph it belongs to (`node_id`) and its `source`
  - every variable's meaning (`name_*`, `desc_*`, `defined_at`)

  Grammar:
  - numbers (`4.5%`, `12.5`) and ids
  - `+ - * / ^` and parentheses
  - `max min sqrt exp ln abs Phi`, and `sum(index[, upper], body)`
  - `=`/`>=`/`<=`

  `/` is drawn as a stacked fraction. A formula with an `anchor` (`p101i8`) replaces the
  `{{F:p101i8}}` token at its image's spot in the text (`display: block|inline`).
  Otherwise it is shown under its paragraph. Chapter 3's 47 formulas are authored in
  `pipeline/translations/ch3_formulas.py`, which merges them in.
- `feeds/<feed>/notation.json` — display only: id → symbol, with `X_{sub}`/`X^{sup}`.
  Replace this file to adopt a different notation standard.

`source` is one of:

- `transcribed`: read off the PDF image. Crop it with
  `pdftoppm -r 300 -f N -l N -x … -y …` and compare.
- `text_derived`: written from the article's own wording.
- `image_reconstructed`: an image formula rebuilt from wording elsewhere, shown with a ⚠.
  Never use it when the PDF is at hand, because the PDF is in `pipeline/source/`.

A transcription that needed judgement carries `note_ja`/`note_en`, and the reader shows it. `build_site.py` rejects unknown variables,
unbalanced parentheses and dangling `node_id`/`defined_at`.

---

## Step 6 — Validate

```bash
python3 -c "
import json, jsonschema
schema = json.load(open('pipeline/schema/rule-feed.schema.json'))
feed = json.load(open('feeds/fsa-basel-cap-jp/feed.json'))
jsonschema.validate(instance=feed, schema=schema)
print('PASSED')
"
```
`batch_ingest.py` already runs this at the end of every call — this is just for
checking the feed on its own, e.g. after hand-editing something.

---

## Step 7 — Build the site and look at it

```bash
python3 pipeline/build_site.py     # writes site/
```
Open `site/index.html` directly in a browser — no server needed. (For live work on
`app/`, `python3 pipeline/serve_no_cache.py 8877` and `http://localhost:8877/app/index.html`
still work and skip the rebuild.)

---

## Doing this for a different chapter or a different regulation entirely

Every script above takes `feed_id` and `chapter_id` as arguments — nothing is hardcoded
to Chapter 2. For a new chapter of the same notification: re-run Step 1 with new
markers, then Steps 2–7 unchanged. For a whole new regulation, also write its
`manifest.json` (see `feeds/fsa-basel-cap-jp/manifest.json` for the shape) and add it to
`feeds/index.json`.

**Formulas and tables in v1 output.** `extract_chapter.py` (v1, pypdf) drops image
formulas silently and flattens tables into running text. That is why Route A uses
`extract_chapter_v2.py`, which leaves `{{F:}}`/`{{T:}}` tokens in their place. If you do use
v1 or a chatbot, tell the model that a missing formula is expected and must not be
invented.

**Resolution limits worth knowing:**

- Item-level relative refs (前号/次号/同号, or a bare 第N号) stay `unresolved` by design
  (CLAUDE.md rule 6). They are most of what's left.
- 前二項 inside a 「」 replacement phrase (「…中「前二項」とあるのは…」) is quoted text, not a
  live citation. It shows as `internal_unavailable`.
- A citation to an instrument with no feed is `external_unavailable`.
  `pipeline/EXTERNAL_INFO_REQUESTS.md` lists what to fetch.
