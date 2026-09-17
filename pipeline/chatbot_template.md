# Chatbot content-population template

Reusable for any regulation, not just this one. Paste the block below into the internal
chatbot, replacing `{{ANCHOR_ID}}`, `{{CONTEXT}}` and `{{SOURCE_TEXT}}`. One Article (条) per
request — process it together with its own paragraphs/items, since translating a list item
in isolation from its stem sentence produces bad translations.

Save the chatbot's raw JSON reply as `pipeline/raw/{{ANCHOR_ID}}.json`. `ingest.py` reads
everything in that folder, resolves cross-references, and merges it into `feed.json`. Never
hand-edit `feed.json` directly — re-run the chunk through the chatbot and re-ingest instead,
so the pipeline stays repeatable for the next regulation.

---

## Prompt to paste

```
You are populating structured data for a Japanese regulatory text reader. You will be given
one Article of Japanese legal/regulatory text. Output ONLY a single JSON object — no prose,
no markdown fences, no explanation before or after.

Known issue in the source text: mathematical formulas in the original PDF were embedded
as images, not text, so they were lost during extraction. You may see a sentence like
"次の算式により得られる比率について" (regarding the ratio obtained by the following
formula) with nothing after it. This is expected — do NOT invent, reconstruct, or guess
at a formula that isn't present in the source text given to you. Translate faithfully
around the gap and move on; its absence is not an error for you to fix.

Context (do not translate, for your reference only): {{CONTEXT}}

Source text (Japanese, verbatim, id={{ANCHOR_ID}}):
"""
{{SOURCE_TEXT}}
"""

Produce JSON with exactly this shape:

{
  "id": "{{ANCHOR_ID}}",
  "number": "<the article/paragraph number as printed, e.g. 第十条>",
  "heading": "<title in parentheses attached to this article, or null>",
  "text_ja": "<verbatim copy of the source text>",
  "text_en": "<accurate English translation, preserving legal register>",
  "clauses_ja": [
    {"clause_type": "<one of: main, conditional, proviso, exception,
                      enumeration_stem, enumeration_item, parenthetical, definition>",
     "text": "<verbatim substring of text_ja>"}
    // Break text_ja into ordered clauses covering the whole sentence.
    // Concatenating all "text" fields in order must reconstruct the original text_ja exactly.
    // Use "conditional" for 場合/とき clauses, "proviso" for ただし-clauses,
    // "parenthetical" for kakko (　) asides, "enumeration_stem" for the sentence introducing
    // a 一/二/三 list and "enumeration_item" for each numbered item.
  ],
  "clauses_en": [
    {"clause_type": "<same enum as above>", "text": "<verbatim substring of text_en>"}
    // Independently break text_en into ordered clauses covering the whole English sentence.
    // Concatenating all "text" fields in order must reconstruct text_en exactly. This does NOT
    // need the same number of clauses as clauses_ja — English often merges or reorders clauses
    // relative to Japanese — but the sequence of clause_types should tell the same structural
    // story (a proviso in the Japanese should still show up as a proviso clause in English,
    // even if it moved position in the sentence).
  ],
  "refs": [
    {"raw_text": "<verbatim citation phrase, e.g. 前条第二項>",
     "text_en": "<the corresponding phrase as it appears in text_en, e.g. 'the preceding paragraph'>",
     "scope": "internal | external",
     "external_name": "<law/notification name if scope=external, else null>",
     "external_item_summary_ja": "<see below, else null>",
     "external_item_summary_en": "<see below, else null>",
     "external_item_summary_confidence": "<stated_in_text | general_knowledge | null>"}
    // List every cross-reference found in text_ja, INCLUDING ones that appear only inside a
    // parenthetical/kakko aside — do not skip a citation just because it's inside brackets.
    // Do not attempt to resolve a target id — just extract the citation phrase exactly as
    // written, in both languages.
    //
    // For scope=external refs ONLY, also fill in external_item_summary_*: a one-line
    // description of what THAT SPECIFIC cited article/paragraph/item says — NOT a summary of
    // the external law as a whole. Two cases:
    //   1. The citing sentence already explains the cited provision inline (very common in
    //      Japanese legal drafting: "...第二条第一号に規定する連結財務諸表提出会社をいう"
    //      tells you Article 2 item 1 defines "a company required to submit consolidated
    //      financial statements" — you don't need outside knowledge, just restate it).
    //      Set external_item_summary_confidence: "stated_in_text".
    //   2. The citing sentence does NOT explain it (e.g. "...銀行法第五十二条の二十三...に
    //      掲げる会社..." just cites a list without spelling it out). Give your best
    //      general-knowledge understanding of what that specific provision covers, but set
    //      external_item_summary_confidence: "general_knowledge" — this must be visibly
    //      flagged as unverified in the reader, never presented as fact.
    // Never write a summary of the external law in general (e.g. "the Banking Act regulates
    // bank licensing") — that's not what was asked; pin it to the exact citation.
  ],
  "defined_terms": [
    {"term_ja": "<term>", "term_en": "<your translation of the term>",
     "expands_to_ja": "<see below, else null>"}
    // Only terms explicitly defined in THIS text (e.g. "...という。" pattern), not terms
    // merely used.
    // Set expands_to_ja ONLY when this term is a shorthand for a longer Japanese phrase
    // named earlier in the same sentence (e.g. "連結財務諸表の用語、様式及び作成方法に
    // 関する規則(...以下「連結財務諸表規則」という。)" — here 連結財務諸表規則's
    // expands_to_ja is the full ordinance name it's short for). Leave null for a term
    // that's being coined/glossed rather than abbreviating something — e.g. "金融子会社"
    // isn't short for some other Japanese phrase, it just gets a plain English gloss.
    // Never put an English translation in this field — it must be Japanese or null.
  ]
}

If a field has nothing to report, use an empty array — never omit a key.
```

---

## Worked example (for your own calibration, not part of the paste)

Input `text_ja`:
> 銀行は、前条第一項各号に掲げる資本調達手段のほか、内閣総理大臣が定める場合には、
> その他の資本調達手段（第三項において「特定資本調達手段」という。）を発行することができる。
> ただし、当該手段が第五条の要件を満たさない場合は、この限りでない。

Expected `clauses_ja`:
1. `main` → "銀行は、前条第一項各号に掲げる資本調達手段のほか、"
2. `conditional` → "内閣総理大臣が定める場合には、"
3. `main` → "その他の資本調達手段"
4. `parenthetical` → "（第三項において「特定資本調達手段」という。）"
5. `main` → "を発行することができる。"
6. `proviso` → "ただし、当該手段が第五条の要件を満たさない場合は、この限りでない。"

`clauses_en` does not need to match this 1:1 — e.g. English might render as
`main` ("A bank may issue other capital-raising instruments... beyond those listed in the
items of Article 29-4, paragraph (1)") → `conditional` ("where specified by the Prime
Minister") → `parenthetical` (the "specified capital-raising instrument" gloss) →
`proviso` ("provided, however, that this does not apply if..."). Same story, different join points.

Expected `refs`:
- `{"raw_text": "前条第一項各号", "scope": "internal", "external_name": null}`
- `{"raw_text": "第五条", "scope": "internal", "external_name": null}`

Expected `defined_terms`:
- `{"term_ja": "特定資本調達手段", "term_en": "specified capital-raising instrument"}`

---

## Second-stage template: article summary

Run this only after every paragraph of an Article has been ingested (`ingest.py` needs the
whole article's text, not one paragraph, to write a summary that isn't misleading). Paste
the assembled `text_ja`/`text_en` of the full article (all paragraphs concatenated) in place
of `{{ARTICLE_TEXT_JA}}` / `{{ARTICLE_TEXT_EN}}`. Save the reply as
`pipeline/raw/{{ANCHOR_ID}}.summary.json`.

```
You will be given the full text of one Article of Japanese regulatory text, with its
official English translation. Write a one-sentence, plain-language summary of what this
Article actually requires or establishes — the kind of line a compliance officer would
want as a preview before deciding whether to read the full text. Do not just restate the
heading. Output ONLY this JSON object, no prose:

{"summary_ja": "<one sentence, plain Japanese>", "summary_en": "<one sentence, plain English>"}

Japanese text: """{{ARTICLE_TEXT_JA}}"""
English text: """{{ARTICLE_TEXT_EN}}"""
```
