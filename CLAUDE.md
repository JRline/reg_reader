# CLAUDE.md — context for working on this repo

Compressed project memory. Read this before making changes — several of the rules below
exist because skipping them caused real, silent bugs earlier in this project's history.

## What this is

A generic, schema-driven reader for Japanese financial regulation, currently populated
with Chapters 2–7 of the FSA's capital-adequacy notification for **Ultimate Designated Parent
Companies (最終指定親会社)** — not the bank version; don't title it as such — plus seven feeds of the
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
- **`site/`** — **the final deliverable.** A self-contained copy of the reader that opens
  from `file://` with no server. Built by `pipeline/build_site.py` (re-run after any change
  to `app/` or `feeds/`; never hand-edit `site/`). Browsers block `fetch()` on `file://`,
  so the build wraps each feed as `site/data/<feed_id>.js`, which registers it on
  `window.REG_DATA`, and `app.js` loads those via `<script>` tags when `index.html` sets
  `window.REG_STATIC_SITE`.
- **`app/`** — the reader's source: plain HTML/CSS/JS, no framework. Served over HTTP (dev
  mode), `app.js` fetches `feeds/index.json` then whichever feed is selected; the same file
  runs in `site/` in static mode (`loadFeedIndex`/`loadFeedData`).
- **`pipeline/`** — turns a source PDF into feed content. Two kinds of scripts here,
  don't confuse them:
  The original plan was to have an external chat model produce feed content; the project
  has since shifted so the **site itself is the product** — content work can be done
  directly in this repo, and the chatbot scripts are optional tooling.
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

7. **Formulas are images in the PDF, not text.** `extract_chapter.py` (v1) drops them
   silently. `extract_chapter_v2.py` leaves a `{{F:<anchor>}}` token where each image sits.
   Formulas are hand-authored in `feeds/<feed>/formulas.json` (see "Formulas" below).
   - **The PDF is in the repo** (`pipeline/source/saishu1.pdf`). Crop the image
     (`pdftoppm -r 300 -x/-y/-W/-H`) and transcribe it as `source: "transcribed"`.
   - `image_reconstructed` (rendered with a ⚠) is only for a formula written without seeing
     its image. Never present a reconstruction as transcribed.
   - Where a reading needed judgement, say so in `note_ja`/`note_en`.

8. **Browsers cache `feed.json`/`style.css`/`app.js` aggressively even across hard
   reloads**, since a bare `python -m http.server` sends no cache-control headers. Use
   `pipeline/serve_no_cache.py` when actively iterating, and note `app/index.html`
   already cache-busts its own `<link>`/`<script>` tags with a timestamp — don't remove
   that.

## In-clause cues and formulas

- **Cues** (`annotate_cues.py` → `clause.cues: [{type, start, end}]`): finer structure
  INSIDE a clause — conditions/provisos inside list items, and exclusion (を除く) /
  limitation (に限る) / definition (をいう) asides at any paren depth — recorded as ranges
  rather than splits, because splitting there would break an item's box or a paren's
  balance. Ranges are only drawn between points at the same paren depth, so they always
  nest; the renderer (`buildCueTree` in app.js) draws them as stacked underlines. Run it
  after `refine_clauses.py` (which drops cues when it changes a clause list).
- **Formulas**: `formulas.json` (structure against variable ids + variable meanings) and
  `notation.json` (id → display symbol only — swap it to change notation standards). The
  app parses `lines` with a small grammar (numbers, ids, `+ - * /`, parens, max/min,
  `= >= <=`) and draws `/` as a fraction; variables are hover/tap targets showing
  meaning and a link to `defined_at`. `build_site.py` validates both files.

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

- `fsa-basel-cap-jp` Chapters 2–7 (not Chapter 1, 定義, and not the 附則): 470 articles, all with
  real content: ch2 27, ch3 112, ch4 118, ch5 36, ch5-2 (第五章の二, CVA) 45, ch5-3 (第五章の三,
  central counterparties) 4, ch6 108, ch7 20. Chapters 4–7 were built exactly like Chapter 3 (Route A), with
  the translation split into 11 slices written in parallel from `pipeline/translations/AGENT_BRIEF.md`
  and merged by `merge_extras.py` (tables → `tables.json`, `*_formulas.py` → `formulas.json`).
  Extraction repairs for layout artifacts (headings glued to the previous article, a table token
  the extractor lost, etc.) live in `pipeline/fix_extractions.py`; run it before `build_chapter.py`.
  Chapter 7 = 第二百八十一条–第二百九十八条 plus 別表第一/第二, built as article-shaped entries keyed
  `appx1`/`appx2` (the app shows "Appended Table N"; `finish_ch7.py` trims the extraction and merges
  `ch7_appendices.json`). The 附則 (the original supplementary provisions and ~17 amending notices,
  which reuse article numbers) are deliberately NOT included.
  Chapter 3
  has 6 節, 8 款 and 13 目, with 目 as the node type `division`, which was added to the
  schema. Its 3 deleted entries (第四十八条, 第七十一条–第七十五条, 第八十五条–第八十八条)
  read 削除 / "Deleted.". Chapter 3 was built in-repo
  (EXTRACTION_GUIDE "Route A"), with no chatbot:
  - extraction: `extract_chapter_v2.py`
  - translations: `pipeline/translations/ch3/*.json`, all `llm_draft`
  - building: `build_chapter.py`
  - citations: `ja_refs.py`
- Tables: 101 in `feeds/fsa-basel-cap-jp/tables.json`, which replace `{{T:<id>}}` tokens.
  The app renders colspan/rowspan.
- 7 feeds total: `fsa-basel-cap-jp`, `jp-banking-act`, `jp-fiea`,
  `jp-fiea-enforcement-order`, `jp-mof-consolidated-fs-regulation`,
  `jp-payment-services-act`, `jp-tlac-notification`.
- Cross-references, all chapters: 2850, of which 2190 internal + 21 external are resolved. The rest:
  - 381 are item-level (rule 6)
  - 167 are `external_unavailable` (other institutions' capital/leverage notices and
    statutes). What to fetch is listed in `pipeline/EXTERNAL_INFO_REQUESTS.md`, which goes
    to an agent with web access.
  - 91 are `internal_unavailable`: mostly Chapter 1 (第一条 definitions) plus 「」-quoted
    replacement phrases (読替え) that name provisions of the cited article, not live citations.
  The post-passes may need two runs to settle (one nested-parenthesis paragraph in ch5-2 converges on
  the second pass); from then on they are idempotent.

  In `ja_refs.py`, 法/令 map to 金融商品取引法/施行令 (`DEFINED_NAMES`), and 同法 carries the
  previous law. `reresolve_refs.py` resolves bare 第N款/第N目 inside the enclosing 節/款, and
  前款第N目 inside the previous sibling.
- Chapter 2: 246 cross-references, 226 resolved (193 before later chapters existed). Remainder: item-level refs (see rule
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
- English clause segmentation (`refine_clauses.py`, `normalize_en_markers`): English list
  markers mirror the Japanese levels (一→(i), イ→(a), （１）→(1)). A bare `(n)` right after
  "paragraph(s)/item(s)" is a citation numeral and is folded back into running text; one
  right after a `. `/`: `/`; ` boundary is a real marker and is attached to its item.
  `app.js`'s `detectItemMarker` reads the English markers too (letters sequence-checked
  like イロハ, which also settles `(i)` letter-vs-roman). The renderer groups each list item
  (marker up to next marker) into one `.enum-block`, so an aside inside an item no longer
  splits it into several boxes.
- 16 Chapter 2 paragraphs once had `clauses_en` drifted from `text_en` (a reworded copy,
  breaking rule 1 — and the reader displays clauses, so users saw the drifted wording).
  `refine_clauses.py` now rebuilds such clauses from `text_en` (`resegment_en`), keeping
  cue-typed spans that still match verbatim. `refine_clauses.py` is idempotent — a second
  run must report 0 changes; it used to strip `in_parenthetical` on re-run.
- Article 8 has 14 paragraphs. Paragraphs 10–14 used to be merged into paragraph 9
  because `extract_chapter.py`'s paragraph-number regex only matched ２–９ (fixed: it
  now accepts two-digit numbers); the feed was split accordingly and refs re-resolved.
- Formulas: 234 in total (355 variables), 229 `transcribed` from the PDF images, 5 `text_derived`; 45 carry a
  `note` explaining a judgement (notation the grammar can't draw, an illegible exponent, …). Chapters 4–7's
  variable ids are prefixed per slice (`C4A_`, `C6B_`, `CH7_`, …).
  The first 57 (ch2–3):
  - Chapter 2 has 10. Articles 2 and 2-2 were re-checked against the PDF: the denominator
    is CRWA + MR/8% + OR/8%.
  - Chapter 3 has 47, authored in `pipeline/translations/ch3_formulas.py` and anchored to
    their `{{F:}}` tokens.
  - Two carry an open `note` and are on the external request list:
    - 第四十七条第十四項: the equity add-on exponent is read as 1/2.
    - 第七十六条第三項: the PDF prints N_R − (T_M − 1), where Basel has +.
  - Grammar adds `^`, sqrt/exp/ln/abs/Phi and `sum(i[, n], body)`.
- All 27 Chapter 2 articles have `heading_en` (except 第二条の二/第四条, which have no
  heading in the source either).
- `refine_clauses.py`'s `split_out_proviso` now ends a proviso at its own sentence's
  「。」/". " at depth 0. The text after it returns to the surrounding clause's type,
  recursively, so a second ただし is found too. It is still idempotent (verified:
  refine → annotate → refine = 0 changes).
- Chapter 1 and the 附則 of the source notification are not extracted. To add one: see
  `EXTRACTION_GUIDE.md` Route A — every pipeline script takes `feed_id`/`chapter_id` as
  arguments, nothing is hardcoded to Chapter 2 except the `ARTICLE_META` dict in
  `ingest.py` (only used for the two hand-processed articles; `batch_ingest.py` doesn't
  need it).
