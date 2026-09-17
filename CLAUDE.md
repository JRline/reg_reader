# CLAUDE.md — context for working on this repo

Compressed project memory. Read this before making changes — several of the rules below
exist because skipping them caused real, silent bugs earlier in this project's history.

## What this is

A generic, schema-driven reader for Japanese financial regulation, currently populated
with Chapter 2 of an FSA Basel capital-adequacy notification plus seven feeds of the
external laws it cites. The app (`app/`) has zero regulation-specific logic — it renders
whatever's in a feed's `feed.json`, so a new regulation is a content problem, not a code
problem. See `README.md` for the user-facing overview.

## Architecture

- **`pipeline/schema/rule-feed.schema.json`** — the data contract. Authoritative. If
  something looks wrong in the app, check whether the *data* violates this schema before
  suspecting the renderer.
- **`feeds/<feed_id>/feed.json`** — a recursive node tree (document → chapter → article →
  paragraph → item), each node carrying `text_ja`/`text_en`, independently-segmented
  `clauses_ja`/`clauses_en` (for visual cues), and `refs` (cross-references).
- **`app/`** — plain HTML/CSS/JS, no build step, no framework. `app.js` fetches
  `feeds/index.json` then whichever feed is selected.
- **`pipeline/`** — turns a source PDF into feed content. Two kinds of scripts here,
  don't confuse them:
  - **Chatbot-dependent** (`make_prompts.py`, `chatbot_template.md`,
    `run_haiku_batch.py`, `batch_ingest.py`): produce and merge translated/segmented
    content. Need a model.
  - **Pure post-processing** (`reresolve_refs.py`, `link_external_refs.py`,
    `refine_clauses.py`): improve already-translated content with zero model calls —
    reference resolution and clause splitting are done with regex/tree-walking, not
    re-translation. Prefer fixing things here over re-running the batch when possible;
    it's dramatically cheaper.

Full pipeline walkthrough: **`pipeline/EXTRACTION_GUIDE.md`**.

## Hard-won rules (things that broke before, don't reintroduce)

1. **`clauses_ja` and `clauses_en` are independent segmentations, not a paired array.**
   English routinely merges or reorders clauses relative to Japanese. Each language's
   clauses must concatenate back to that language's own `text_*` exactly — this is
   checked in `ingest.py`'s `check_reconstruction()`. Never assume `clauses_ja[i]`
   corresponds to `clauses_en[i]`.

2. **Empty `text_en` is not valid content, it's a red flag.** A whole batch of 87
   "processed" paragraphs once went in with real `text_ja` but blank `text_en` and zero
   refs, and it passed silently because an empty translation trivially "reconstructs."
   `ingest.py`'s `check_not_a_placeholder()` and `batch_ingest.py`'s hard rejection exist
   specifically to catch this — don't work around them, fix the underlying content.

3. **A citation's `raw_text` must be a verbatim substring of `text_ja`, parentheses
   included.** Two real fabricated-looking citations in this project's own history came
   from assuming a paren closed sooner than it actually did. `check_refs_present()`
   catches this; take its warnings seriously.

4. **Term expansion vs. translation are different fields, don't conflate them.**
   `expands_to_ja` (a term's fuller Japanese phrase, e.g. a shorthand for an ordinance's
   full name) and `term_en` (its English translation) serve different purposes.
   `resolve_external_name()` in `ingest.py` deliberately never falls back from one to the
   other — doing so once leaked English text into a field the rest of the pipeline reads
   as Japanese.

5. **Single-character marker detection needs sequence validation, not just a character
   class.** A bare "starts with any of the 47 iroha kana" check flags ordinary katakana
   words (リスク, ロット...) as list markers. `app.js`'s `detectItemMarker()` only
   accepts a level-2 (イロハ) marker if it's the next expected character in sequence —
   don't loosen this back to a plain character-class match.

6. **号-items (numbered list items) are not separate nodes** — they're
   `clause_type: "enumeration_item"` entries inside a paragraph's clause list, not
   addressable by id. This means item-level relative citations (前号/次号/同号) can't
   resolve to a precise target with the current data model; they're left `unresolved`
   deliberately, not by oversight. Fixing this for real means promoting items to child
   nodes (the pattern already used for the external law feeds like `jp-banking-act`,
   where items *are* separate `type: "item"` nodes) — a real but substantial refactor,
   not a quick patch.

7. **Formulas are missing from extracted text, not lost by a bug.** The source PDF
   embeds mathematical formulas as images; `extract_chapter.py` (and any model
   processing its output) never sees them. Don't try to reconstruct a formula from
   context — flag the gap.

8. **Browsers cache `feed.json`/`style.css`/`app.js` aggressively even across hard
   reloads**, since a bare `python -m http.server` sends no cache-control headers. Use
   `pipeline/serve_no_cache.py` when actively iterating, and note `app/index.html`
   already cache-busts its own `<link>`/`<script>` tags with a timestamp — don't remove
   that.

## Reference resolution model

Three layers, run in this order after content is ingested:
1. `ingest.py` (per-article, during merge) — only relative refs within the same article
   (前項/前二項), since it doesn't have chapter-wide context.
2. `reresolve_refs.py` (whole-chapter pass) — absolute and relative citations within the
   same document (第五条第二項, 前条, 同項, chapter-level citations to unloaded
   chapters → `internal_unavailable`).
3. `link_external_refs.py` (cross-feed pass) — connects external citations to content
   already digitized in another feed, keyed by a `LAW_NAME_TO_FEED` table at the top of
   that script. Extend that table when adding a new external feed.

`resolution_status` values: `resolved`, `unresolved` (couldn't parse/no known target),
`external_unavailable` (external law recognized, not digitized), `internal_unavailable`
(citation understood, target not in currently-loaded content), `ambiguous` (unused so far).

## Current state (update this section as it changes)

- `fsa-basel-cap-jp` Chapter 2: all 27 articles have real content.
- 7 feeds total: `fsa-basel-cap-jp`, `jp-banking-act`, `jp-fiea`,
  `jp-fiea-enforcement-order`, `jp-mof-consolidated-fs-regulation`,
  `jp-payment-services-act`, `jp-tlac-notification`.
- ~246 cross-references in Chapter 2; 190 resolved. Remainder: item-level refs (see rule
  6 above), a couple of not-yet-digitized sibling FSA notifications, and one bare
  law-name mention with no specific target.
- `refine_clauses.py` now also reclassifies bare `(1)`/`（１）`-style parenthetical
  clauses as level-3 `enumeration_item`s (they're list markers, not asides — a
  paren-balance split alone can't tell them apart) and splits inline イロハ bundling
  (`split_inline_iroha`) when a sub-item marker directly follows a 。, mirroring
  `app.js`'s `detectItemMarker` sequence check. Remaining known open item: a level-2
  marker that starts immediately after the parent item's own text with **no** 。
  in between (e.g. "一次に掲げる額の合計額イ次に掲げる...", seen in 第五条第二項) isn't
  split — there's no reliable boundary signal to split on without more context, so it's
  intentionally left bundled rather than guessed at.
- `refine_clauses.py`'s `analyze_parenthetical()` further classifies what's INSIDE a
  parenthetical aside — a nested proviso, exclusion, or condition gets its own
  `clause_type` plus `in_parenthetical: true` (schema field), which `app.js`/`style.css`
  render as a colored underline instead of that type's usual background highlight (a
  highlight box there would clash with the aside's own dimmed styling). A whole-clause
  `(...をいう。以下同じ。)`-style definition is retagged outright via
  `reclassify_whole_definitions()`. All of this is regex-based, bounded to reject a match
  that would cut through a nested paren (`_outer_prefix_end`/`_depth_at`) rather than risk
  a corrupted split — exception detection in particular hasn't fired on any Chapter 2
  content yet under that conservative bound, which is expected, not broken.
- Other chapters of the source notification are not extracted. To add one: see
  `EXTRACTION_GUIDE.md` Step 1 — every pipeline script takes `feed_id`/`chapter_id` as
  arguments, nothing is hardcoded to Chapter 2 except the `ARTICLE_META` dict in
  `ingest.py` (only used for the two hand-processed articles; `batch_ingest.py` doesn't
  need it).
