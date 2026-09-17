# Extraction guide: PDF → structured, translated, cross-referenced feed

This walks through turning a chapter of the source PDF into real content in the app,
end to end. It's written for this regulation (`fsa-basel-cap-jp`, Chapter 2), but every
script takes the chapter/feed as arguments, so the same steps work for the next chapter
or the next regulation entirely.

Prerequisites:
```bash
pip install pypdf jsonschema anthropic
export ANTHROPIC_API_KEY=...   # only needed for step 3
```

---

## Step 1 — Extract the chapter's articles from the PDF

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

## Step 7 — Look at it

```bash
python3 -m http.server 8877        # from the project root
```
Open `http://localhost:8877/app/index.html`.

---

## Doing this for a different chapter or a different regulation entirely

Every script above takes `feed_id` and `chapter_id` as arguments — nothing is hardcoded
to Chapter 2. For a new chapter of the same notification: re-run Step 1 with new
markers, then Steps 2–7 unchanged. For a whole new regulation, also write its
`manifest.json` (see `feeds/fsa-basel-cap-jp/manifest.json` for the shape) and add it to
`feeds/index.json`.

**Known content gap: mathematical formulas are silently dropped.** Several articles say
things like "次の算式により得られる比率について" (the ratio obtained by the following
formula) and then the formula itself is just... absent from `ch2_articles.json`. This
isn't a bug in `extract_chapter.py` — the formulas in the source PDF are embedded as
images/vector graphics, not selectable text, so `pypdf` never sees them at all. Confirmed
by checking the raw PDF page text directly: there's a blank line in the extraction
exactly where Article 2's first formula should be. Since this chapter is literally
titled "算式等" (Formulas, etc.), expect this in multiple articles, not just one.

This means: **don't let the chatbot invent a formula to fill the gap.** Tell it explicitly
that a missing formula is expected and should be marked as omitted, not reconstructed
from context. The real fix is transcribing formulas from the PDF by hand (or screenshotting
the relevant page region and embedding it as an image in that node) — there's no
extraction shortcut for content that was never text in the first place.

Two things this pipeline does **not** yet automate, worth knowing before you hit them:
- **Article-level relative refs** (前条/前二条, "the preceding article/articles") aren't
  resolved yet — only paragraph-level 前項/前二項 are. They'll show up as `unresolved`,
  which is honest but not linked. Add the pattern to `resolve_internal_ref()` in
  `ingest.py` when it starts mattering.
- **Absolute internal refs** (第五条第一項, citing a specific article by number rather
  than relatively) also resolve as `unresolved` right now — worth adding once most of a
  chapter's stubs have been filled in, since only then do the target ids reliably exist
  to resolve against.
