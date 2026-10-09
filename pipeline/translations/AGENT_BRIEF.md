# Brief: translating a slice of the notification into per-article files

You translate a slice of articles from 最終指定親会社 capital-adequacy notification (FSA) into
English and author their tables and formulas. Other agents do other slices **in parallel**,
so touch only the files named below. Never edit `feeds/`, `app/`, `site/`, or other agents'
files, and never run git. Working directory: `/home/user/reg_reader`.

## Inputs

- Extraction: `pipeline/source/<ch>_v2.json` (keys `articles`, `tables`, `images`).
- Read your articles with:
  `python3 pipeline/dump_articles.py pipeline/source/<ch>_v2.json <first 第N条> [<last>]`
  Each paragraph (項) prints with its item segments `[marker] text`. The paragraph's text is
  all segments concatenated.
- `{{T:<id>}}` = a table, `{{F:<id>}}` = a formula image (inline if it sits mid-sentence).
  `X_{i}` / `X^{2}` are sub/superscripts already in the text.
- To read a table or formula image: `python3 pipeline/crop_token.py pipeline/source/<ch>_v2.json p326t0 p337i0`
  (default output `/tmp/crops/<id>.png`; then Read the PNG). Page = the number after `p`.
  Read every one of yours; **never guess a formula or a cell**. To see more context, render the page:
  `pdftoppm -r 110 -f <page> -l <page> -png pipeline/source/saishu1.pdf /tmp/pg`.
- Glossary: `pipeline/translations/GLOSSARY.md`. Reuse its renderings. Also `grep` the
  `"terms"` of translation files already written (any `pipeline/translations/*/*.json`) for the
  same term before inventing a translation.
- Style model: `pipeline/translations/ch3/art14.json`, `ch3/art32-2.json`, `ch3/art47.json`.

## Output 1: one translation file per article

`pipeline/translations/<chdir>/art<N>[-<sub>…].json` (`<chdir>` given in your assignment; the key
is the article number with each の-suffix as `-n`: 第二百四十八条の四の十三 → `art248-4-13`).
Write them directly (a short Python script that dumps JSON is fine). Shape:

```json
{"number": "第百十六条",                       // exactly as in the extraction
 "heading_en": "…",                            // required when the article has a heading
 "summary_ja": "…", "summary_en": "…",         // 1–2 sentences each, plain
 "paragraphs": ["EN of paragraph 1", "EN of paragraph 2"],
 "terms": [{"ja": "…", "en": "…"}],            // terms DEFINED by 「…」 in this article
 "sections_en": {"第一節": "General Provisions", "第一節 第二款": "…"}}   // only on the first article of each new 節/款/目
```

Section keys: a 節/款/目 key is its number alone when single level (`"第一節"`), otherwise the
path joined by spaces (`"第一節 第二款"`, `"第一節 第二款 第三目"`). Look at `a["path"]` in
the extraction (`number`, `heading`) for the exact numbers and Japanese headings; give the
English heading for every new level your slice *starts*. If your slice begins mid-section,
you still need the keys for the sections it is in — the build merges them from all files, so
include the first article's whole path.

Hard rules (the build/validator rejects or silently corrupts otherwise):

1. `paragraphs` has **exactly one entry per extracted paragraph**, in order. Each is a single string
   containing the whole paragraph: the lead-in sentence, then its items inline (see art14).
2. Keep every `{{T:…}}` and `{{F:…}}` token **verbatim, in the corresponding place**, same count.
3. English text must be real, complete English — no Japanese left, never empty, never a
   summary of the paragraph. It must be a faithful translation of that paragraph only.
4. **List markers.** Mirror the Japanese levels, written as `(i)`, `(ii)` for 一二…, `(a)`, `(b)` for
   イロハ…, `(1)`, `(2)` for （１）（２）…, each introduced by `. ` / `: ` / `; ` and followed by a
   space and the text, as in art14. Don't invent markers the Japanese lacks.
5. **Citations** follow one convention (the pipeline matches on it): `Article 5`, `Article 43-3-2`,
   `Article 5, paragraph (2)`, `Article 5, paragraph (2), item (i)`, `paragraph (1)`, `the preceding
   paragraph`, `item (iii)`, `items (i) through (iv)`, `the preceding item`, `Chapter 5-2`, `Section 6`,
   `Subsection 3`, `Division 2`. Other instruments: `Article 14-2 of the Banking Act`;
   notices by their short names as used in Chapter 3 (`the Bank Capital Adequacy Notice`, `the
   TLAC Public Notice for Ultimate Designated Parent Companies`, …). Keep a quoted law/notice's
   own title in English as in the glossary or `pipeline/ja_refs.py`'s `NOTICES`/`LAWS` tables.
6. Deleted articles (削除): the extraction marks `deleted`; **no file needed**.
7. Terminology: the entity is "Ultimate Designated Parent Company" (UDPC; with `等` → "Ultimate
   Designated Parent Company, etc."); "adopting the standardized approach" / "adopting the
   internal ratings-based approach" as in Chapter 3; "risk-weighted assets", "exposure", "obligor",
   "Tier 1 Capital". Quote defined terms in `"…"` on first definition, as Chapter 3 does.

Run the validator as you go (it never touches the feed):
`python3 pipeline/check_translations.py pipeline/source/<ch>_v2.json pipeline/translations/<chdir> <first> <last>`
It must end with `0 errors`; fix every WARN about a token with no table/formula entry.

## Output 2: tables → `pipeline/translations/<TAG>_tables.json`

One JSON object, key = table id (`p326t0`), as in `feeds/fsa-basel-cap-jp/tables.json`:

```json
{"p326t0": {"node_id": "fsa-basel-cap-jp.ch6.art253.p1", "header_rows": 1,
  "rows_ja": [["満期", "リスク・バケット"], ["零年以上〇・七五年未満", "A1"]],
  "rows_en": [["Maturity", "Risk bucket"], ["0 years or more and less than 0.75 years", "A1"]]}}
```

`node_id` = the paragraph containing the token. A cell is a string, or
`{"text": "…", "colspan": 2, "rowspan": 3}`; a cell covered by a neighbour's span is `null`.
`rows_ja` and `rows_en` must have identical shape. **Check the cells against the cropped image**
(the auto-extracted `rows` in the extraction are a starting point and can be wrong: merged cells,
split lines, wrong columns). Numbers stay as printed in Japanese (`二十` → `20` in English).
A table continuing over a page break is already merged; if the extraction's `continued_on` shows
otherwise, fix it. Nodes ids are `fsa-basel-cap-jp.<chdir>.art<key>.p<k>` (k = 1-based paragraph index).

## Output 3: formulas → `pipeline/translations/<TAG>_formulas.py`

```python
from formulas_lib import *      # v, f, inline, TAG, V, F
import formulas_lib
formulas_lib.TAG = "<TAG>"
C = "fsa-basel-cap-jp.<chdir>."
v("C6_DRC_LGD", "LGD", "損失率", "Loss given default", C + "art253.p2")           # id, display symbol, name_ja, name_en, defined_at node
f("p337i0", C + "art253.p2", ["rho_s = cov(R_HPL, R_RTPL) / (sigma_RHPL * sigma_RRTPL)"])
inline("p337i1", C + "art253.p2", "C6_DRC_LGD")                                 # a lone symbol/number in running text
```

- One `f(...)`/`inline(...)` per `{{F:…}}` anchor of yours — every anchor must be covered (the validator
  warns). Read the image, transcribe exactly what is printed. Use `source="transcribed"` (default).
  If a reading needed judgement (blurry exponent, a printed sign that differs from the usual
  formulation) set `nj=`/`ne=` notes saying exactly what and why — never silently "fix" the
  notification.
- **Grammar** (the app parses `lines`): numbers (`4.5%`, `0.05`), variable ids, `+ - * /`, `^`,
  parentheses, `max(a,b,…)`, `min`, `sqrt(x)`, `exp`, `ln`, `abs`, `Phi(x)`,
  `sum(i, body)` or `sum(i, upper, body)` (lowercase single-letter indexes or `idx_…`), and
  `= >= <=`. `a / b` is drawn as a fraction — parenthesise numerators/denominators. A variable
  id is `[A-Za-z][A-Za-z0-9_]*`. Display text for a variable (`ρ_{s}`, `AddOn^{(IR)}`) comes
  from `v(id, symbol, …)`'s second argument, not from the id. Multi-line formulas = several
  strings in the list. The left side of a defining equation is itself a variable (declare it).
- Every id used in a formula must be declared with `v(...)`, and declared **once**, in your file.
  **Prefix all ids with your TAG in capitals plus underscore (`C6A_LGD`)** so slices never collide.
  Give each a name (JA/EN) copied from what the article says it means, and `defined_at` = the node
  where the article defines it (a paragraph node id; if unsure, the formula's own paragraph). If
  the article gives a short explanation (「…は、…をいう」), put it in `dj`/`de`.
- Test that your file runs: `cd pipeline/translations && python3 -c "import formulas_lib, runpy; runpy.run_path('<TAG>_formulas.py'); print(len(formulas_lib.F), len(formulas_lib.V))"`.
  Do **not** run `merge_extras.py` (the coordinator merges everything at the end).

## Finish

Reply with: files written, counts (articles, tables, formulas), validator result, and a list of any
judgement calls, doubtful readings, or things you could not resolve (be specific: article, paragraph).
Do not paste the translations into the reply.
