# Addendum to AGENT_BRIEF.md: Chapter 1 (定義) and the 附則

Read `pipeline/translations/AGENT_BRIEF.md` first; everything there applies (tokens, glossary,
citation convention, no touching other files, no git, no `merge_extras.py`). This addendum covers
the two inputs whose shape differs.

## A. Chapter 1: 第一条 (definitions), translated in segment ranges

`pipeline/source/ch1_v2.json` holds one article, 第一条, with one 216-segment paragraph: segment 0
is the lead-in ("この告示において、次の各号に掲げる用語の意義は…"), then 119 numbered items (level 1:
一, 二, 二の二 …), 79 イロハ sub-items (level 2) and 17 （１）（２） sub-sub-items (level 3). Each
item *defines a term* and the term is written right after the marker with no space and no 「」:
`一子法人等金融商品取引法(…)に規定する子法人等をいう。` = item 一 defines 子法人等. Read your range with

    python3 pipeline/dump_segments.py pipeline/source/ch1_v2.json <first idx> <last idx>

**Output: `pipeline/translations/ch1_parts/p<N>.json`** (N given in your assignment), not an article file:

```json
{"segments": {"0": "In this Public Notice, the meanings of the terms set out in the following items are as prescribed in those items.",
              "1": "(i) \"Subsidiary, etc.\" means a subsidiary, etc. prescribed in Article 57-2, paragraph (9) of the Financial Instruments and Exchange Act (hereinafter referred to as the \"Act\").",
              "2": "…"},
 "terms": [{"ja": "子法人等", "en": "Subsidiary, etc."}]}
```

- One entry per segment index in your range, **every index**, key = the index as a string.
  The English string for a segment is its complete translation *including its own marker*:
  level 1 kanji → `(i)`, `(ii)`, `(ii-2)` for 二の二, `(ii-3)` for 二の三 …; level 2 イロハ → `(a)`, `(b)` …;
  level 3 （１）（２） → `(1)`, `(2)`. The lead-in (segment 0, only in part 1) has no marker.
  The pipeline joins the strings with single spaces, so each must be a complete sentence ending with
  its final stop, and must not contain the next item's marker.
- Quote the defined term in the English as `"Term"` where it is defined, and use the same rendering
  whenever that term is used later (grep earlier parts in `pipeline/translations/ch1_parts/` and the
  glossary; Chapters 2–7 already use many of these terms, see `GLOSSARY.md` and
  `grep -h '"terms"' -A2 pipeline/translations/ch*/art*.json`). Reuse those renderings.
- `terms`: one `{ja, en}` per term the item defines (some items define several, some
  items - ロ, ハ… sub-items - define none). `ja` is the exact term text as it appears after the marker.
- Citations: standard convention. Instruments cited by short name inside the item (「法」 = the Act
  (the Financial Instruments and Exchange Act), 「令」 = its Enforcement Order, 「府令」, 「単体自己資本規制比率告示」
  …) keep the short name in `"…"` as the Japanese defines it.
- Run `python3 pipeline/check_translations.py` is **not** applicable here. Self-check instead:
  `python3 -c "import json;d=json.load(open('pipeline/translations/ch1_parts/p1.json'));print(len(d['segments']),'segments',len(d['terms']),'terms')"`.
  The coordinator assembles `art1.json` from the three parts.

## B. 附則 (supplementary provisions): block-keyed entries

`pipeline/source/fusoku_v2.json` holds 32 blocks (first the notification's own 附則, then the 附則 of
each amending notice and the 改正文 application clauses) as 75 entries. **Article numbers repeat from
block to block** (every notice has a 第一条), so every entry has a unique `key` like `s03.art3`
(block 3, 第三条) or `s07.u1` (text with no article number). Use the **key** wherever the brief says
"article number":

- dump: `python3 pipeline/dump_articles.py pipeline/source/fusoku_v2.json <first key> <last key>`
  (e.g. `s00.art1 s10.art10`; the key is printed first on each header line, then the Japanese number).
- translation file: `pipeline/translations/fusoku/<key>.json` (e.g. `s03.art3.json`), with
  `"number": "<key>"` (the key itself, not 第三条). Deleted entries (削除) need no file.
- validate: `python3 pipeline/check_translations.py pipeline/source/fusoku_v2.json pipeline/translations/fusoku <first key> <last key>`.
- `heading_en`: translate the article's marginal heading (e.g. 適用時期 → "Effective Date"); for entries
  with no heading give `""`.
- `sections_en`: each *block* is a section whose Japanese title is on the entry's `path[0]`
  (e.g. `附則(平成二三年五月二七日金融庁告示第六一号)`, `改正文(…)抄`). Put on **the first entry of each block**:
  `"sections_en": {"s01": "Supplementary Provisions (FSA Public Notice No. 61 of May 27, 2011)"}` (key = the block
  key, `s00`…). Title style: `Supplementary Provisions` alone for s00 ("original" provisions of the
  notification), `Supplementary Provisions (FSA Public Notice No. N of <Month D, YYYY>)` for 附則 blocks,
  `Amending Provision (FSA Public Notice No. N of <date>)` for 改正文; append ` (excerpt)` when the Japanese says 抄.
  Convert eras: 昭和N = 1925+N, 平成N = 1988+N, 令和N = 2018+N. Dates in running text become
  "March 31, 2023"; keep kanji-numbered fiscal/year counts as ordinary numbers.
- Instruments: 「新告示」 = "the New Public Notice" and 「旧告示」 = "the Former Public Notice" (they are defined in
  the text; follow that definition). 「この告示」 = "this Public Notice". Citations of a provision of the
  supplementary provisions themselves ("附則第五条") → "Article 5 of the Supplementary Provisions".
  Article citations without 附則 keep the standard form (`Article 116`).
- Tables in these blocks (ids `p432t0`, `p434t0`, `p435t0`, `p438t0`): `pipeline/translations/<TAG>_tables.json`
  as in the brief; node ids look like `fsa-basel-cap-jp.fusoku.s03.art3.p1` (block node = `fusoku.<block key>`,
  then `.art3` / `.u1`, then `.p<k>`). Crop them with `crop_token.py pipeline/source/fusoku_v2.json <id>`.
- The extractor dropped the marginal heading of a second paragraph in unnumbered entries (e.g. the
  (経過措置) before ２ in `s26.u1`): ignore it.
- No formulas in the 附則.
- Report any text that looks mis-extracted (wrapped headings, merged paragraphs).
