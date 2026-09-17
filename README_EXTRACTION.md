# FSA Basel Chapter 2 Extraction — Complete Pipeline

## What This Is

This project extracts, translates, and structures a chapter of Japanese financial regulation (FSA Basel capital-adequacy rules) into a bilingual, interactive reader. The reader displays regulation text with color-coded clauses, clickable cross-references, and English translations.

## Project Status

| Step | Task | Status |
|------|------|--------|
| 1 | Extract PDF chapter → articles | ✅ **DONE** |
| 2 | Generate extraction prompts | ✅ **DONE** |
| 3 | Run prompts through Haiku | ⏳ **IN PROGRESS** (needs API key) |
| 4 | Merge into feed + QA checks | 📋 Pending Step 3 |
| 5 | Generate article summaries | 📋 Pending Step 3 |
| 6 | Validate schema | 📋 Pending Step 3 |
| 7 | View in app | 📋 Pending Step 3 |

---

## Quick Start (After API Key Configured)

### 1. Complete Batch Processing

In an **interactive terminal** with your API key:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
cd "/Users/jieren/Claude Code"
python3 pipeline/run_haiku_batch.py
```

**Monitor progress** (optional, in another terminal):
```bash
cd "/Users/jieren/Claude Code"
./MONITOR_BATCH.sh
```

Expected: ~5-10 minutes for 77 new JSON files (starting with 6, will reach 83 total)

### 2. Run Remaining Steps (After Batch Complete)

```bash
cd "/Users/jieren/Claude Code"
./COMPLETE_PIPELINE.sh
```

This automatically:
- Merges all responses into the feed
- Resolves internal references
- Runs QA validation checks
- Generates article-level summaries
- Validates final feed schema

### 3. View Results

```bash
cd "/Users/jieren/Claude Code"
python3 -m http.server 8877
```

Then open: **http://localhost:8877/app/index.html**

Navigate to: "FSA — Basel Cap Adequacy" → "Chapter 2: Formulas, etc."

---

## What Gets Extracted

For each of 87 paragraphs across 27 articles, the pipeline produces:

```json
{
  "id": "fsa-basel-cap-jp.ch2.art3.p1",
  "text_ja": "[Original Japanese regulation text]",
  "text_en": "[Accurate English translation in legal register]",
  
  "clauses_ja": [
    {"clause_type": "main", "text": "..."},
    {"clause_type": "proviso", "text": "ただし、..."},
    {"clause_type": "parenthetical", "text": "(...説明...)"},
    {"clause_type": "enumeration_item", "text": "一..."}
  ],
  
  "clauses_en": [
    {"clause_type": "main", "text": "..."},
    {"clause_type": "proviso", "text": "provided, however, that..."},
    {"clause_type": "parenthetical", "text": "(explanation)..."}
  ],
  
  "refs": [
    {
      "raw_text": "銀行法第五十二条",
      "text_en": "Article 52 of the Banking Act",
      "scope": "external",
      "external_name": "銀行法",
      "external_item_summary_ja": "...",
      "external_item_summary_en": "...",
      "external_item_summary_confidence": "verified_from_source"
    }
  ],
  
  "defined_terms": [
    {"term_ja": "連結財務諸表規則", "term_en": "Consolidated Financial Statement Regulation"}
  ]
}
```

Each extraction includes:
- ✅ Clause-by-clause breakdown (must reconstruct original text exactly)
- ✅ Cross-references to internal & external articles
- ✅ Summaries of cited provisions
- ✅ Terms explicitly defined in the text
- ✅ Legal-register English translation

---

## Key Features of the Pipeline

### Quality Assurance

**Clause Reconstruction Check**
- Concatenating all `clauses_ja[].text` must equal `text_ja` character-for-character
- Catches: missing punctuation, incorrect segmentation, hallucinated text
- Same independently for English

**Reference Verbatim Check**
- Every `refs[].raw_text` must be a substring of `text_ja`
- Catches: paraphrased citations, fabricated references
- Critical because refs are later resolved to article IDs

### Known Limitations

**Missing Formulas**
- Chapter 2 title: "算式等" (Formulas, etc.) — but formulas appear as **images** in the source PDF
- Text extraction sees blank lines where formulas should be
- Pipeline explicitly instructs model NOT to invent formulas
- Real fix: manual transcription or screenshot + embed as images

**Unresolved Reference Types (Future)**
- Relative article references ("前条" = preceding article) — only paragraph-level ("前項") are resolved currently
- Absolute references ("第五条第一項") — will resolve once more of Chapter 2 is populated

---

## Project Structure

```
/Users/jieren/Claude Code/
├── pipeline/
│   ├── source/
│   │   ├── saishu1.pdf                    ← Source regulation PDF
│   │   └── ch2_articles.json              ← Extracted articles (Step 1)
│   ├── prompts/                           ← Extraction prompts (Step 2)
│   │   ├── fsa-basel-cap-jp.ch2.art2.p1.txt
│   │   ├── fsa-basel-cap-jp.ch2.art3.p1.txt
│   │   └── ... (83 total)
│   ├── raw/                               ← Haiku responses (Step 3)
│   │   ├── fsa-basel-cap-jp.ch2.art3.p1.json
│   │   ├── fsa-basel-cap-jp.ch2.art3.p2.json
│   │   └── ... (will be 83 total)
│   ├── schema/
│   │   └── rule-feed.schema.json          ← JSON schema for validation
│   ├── extract_chapter.py                 ← Step 1 script
│   ├── make_prompts.py                    ← Step 2 script
│   ├── run_haiku_batch.py                 ← Step 3 script
│   ├── batch_ingest.py                    ← Step 4 script
│   ├── ingest.py                          ← Core ingestion logic
│   ├── make_summary_prompts.py            ← Step 5 script
│   └── chatbot_template.md                ← Prompt template
├── feeds/
│   └── fsa-basel-cap-jp/
│       ├── feed.json                      ← Output feed (after Step 4+)
│       ├── term_registry.json             ← Extracted terms
│       ├── manifest.json                  ← Feed metadata
│       └── ch2_outline.tsv                ← Article headings (English)
├── app/                                   ← Web reader app
│   └── index.html                         ← Launch from here
├── COMPLETE_PIPELINE.sh                   ← Run Steps 4-7 automatically
├── MONITOR_BATCH.sh                       ← Monitor Step 3 progress
├── EXTRACTION_COMPLETION_GUIDE.md         ← Detailed step reference
└── README_EXTRACTION.md                   ← This file
```

---

## Troubleshooting

### "Could not resolve authentication method"
```
Error: Could not resolve authentication method. Expected one of api_key, ...
```
**Fix**: Set your API key before running the batch:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxxxx
python3 pipeline/run_haiku_batch.py
```

### "FAILED to parse JSON"
```
fsa-basel-cap-jp.ch2.art2.p1: FAILED ("Expecting value" line X)
```
**Fix**: Check the raw response:
```bash
cat pipeline/raw/fsa-basel-cap-jp.ch2.art2.p1.FAILED.txt
```
Review the prompt and Haiku's response. The response may be malformed and need manual fixing.

### Validation Error After Step 4
```
ValidationError: 'refs' is a required property
```
**Fix**: A response is missing a required field. Check:
1. `pipeline/schema/rule-feed.schema.json` — what's required?
2. `ingest.py` — how fields are extracted from raw responses
3. A specific `.FAILED.txt` file if parsing went wrong

---

## Timeline

| Activity | Duration | Status |
|----------|----------|--------|
| Extract PDF | ~30s | ✅ Done |
| Generate prompts | ~10s | ✅ Done |
| **Batch API calls** | **5-10 min** | ⏳ Step 3 |
| Merge & QA | ~30s | Pending |
| Article summaries | ~2-3 min | Pending |
| Validation | ~5s | Pending |
| **Total (estimated)** | **~10-15 min** | |

---

## What to Do Next

1. **Get your Anthropic API key** (if you don't have one)
   - Visit https://console.anthropic.com/

2. **Run Step 3** in an interactive terminal:
   ```bash
   export ANTHROPIC_API_KEY=sk-ant-...
   cd "/Users/jieren/Claude Code"
   python3 pipeline/run_haiku_batch.py
   ```

3. **Monitor progress** (optional):
   ```bash
   ./MONITOR_BATCH.sh
   ```

4. **Once complete, run remaining steps**:
   ```bash
   ./COMPLETE_PIPELINE.sh
   ```

5. **View in the app**:
   ```bash
   python3 -m http.server 8877
   # Open: http://localhost:8877/app/index.html
   ```

---

## For Reference: Individual Steps

### Step 1 (Already Done)
Extract text from PDF, split into articles and paragraphs:
```bash
python3 pipeline/extract_chapter.py pipeline/source/saishu1.pdf "第二章 算式等" "第三章 信用リスクの標準的手法" pipeline/source/ch2_articles.json
```

### Step 2 (Already Done)
Generate extraction prompts for each paragraph:
```bash
python3 pipeline/make_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/source/ch2_articles.json pipeline/prompts
```

### Step 3 (Needs Your API Key)
Call Haiku on all prompts:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
python3 pipeline/run_haiku_batch.py
```

### Step 4 (Automatic in COMPLETE_PIPELINE.sh)
Merge responses, resolve refs, run QA:
```bash
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```

### Step 5 (Automatic in COMPLETE_PIPELINE.sh)
Generate & ingest article summaries:
```bash
python3 pipeline/make_summary_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/prompts
python3 pipeline/run_haiku_batch.py
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```

### Step 6 (Automatic in COMPLETE_PIPELINE.sh)
Validate schema:
```bash
python3 -c "
import json, jsonschema
schema = json.load(open('pipeline/schema/rule-feed.schema.json'))
feed = json.load(open('feeds/fsa-basel-cap-jp/feed.json'))
jsonschema.validate(instance=feed, schema=schema)
print('✅ Valid')
"
```

### Step 7 (Manual)
Run the web app:
```bash
python3 -m http.server 8877
# Open: http://localhost:8877/app/index.html
```

---

## Questions?

- **How are cross-references resolved?** See `ingest.py` — `resolve_internal_ref()` for paragraph-level refs
- **What happens to formulas?** They're marked as missing in the text; real fix requires manual transcription
- **How accurate is the English translation?** Haiku 4.5 is trained on legal text; all translations are reviewed in the reader context
- **Can I add a new article manually?** Yes — add its JSON to `pipeline/raw/`, then run Step 4's ingestion

---

**Status**: Ready for Step 3 batch processing 🚀
