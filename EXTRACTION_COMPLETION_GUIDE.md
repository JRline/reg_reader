# Complete FSA Basel Chapter 2 Extraction Guide

## Current Status

- ✅ **Step 1**: Articles extracted from PDF (27 articles, 87 paragraphs)
- ✅ **Step 2**: Extraction prompts generated (83 files)
- ⏳ **Step 3**: Batch processing in progress (6/83 complete, needs API key)
- 📋 **Steps 4-7**: Pending (will run once Step 3 is complete)

## Immediate Action Required

### Complete the Batch Processing (Step 3)

In an interactive terminal with your Anthropic API key:

```bash
# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Navigate to project
cd "/Users/jieren/Claude Code"

# Run the batch processor (skips existing files, safe to re-run)
python3 pipeline/run_haiku_batch.py
```

Expected output:
- 77 new JSON files generated (already have 6)
- ~5-10 minutes for complete batch on Haiku 4.5
- No failures expected (all prompts are well-formed)

---

## Full Pipeline Steps (Reference)

### Step 1: Extract Chapter from PDF ✅ DONE
```bash
python3 pipeline/extract_chapter.py pipeline/source/saishu1.pdf "第二章 算式等" "第三章 信用リスクの標準的手法" pipeline/source/ch2_articles.json
```
**Result**: `pipeline/source/ch2_articles.json`
- 27 articles with their paragraphs
- Clean text extraction (formulas appear as text gaps—this is expected)

### Step 2: Generate Extraction Prompts ✅ DONE
```bash
python3 pipeline/make_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/source/ch2_articles.json pipeline/prompts
```
**Result**: `pipeline/prompts/` with 83 files
- One `.txt` file per paragraph
- Each contains: source text (Japanese), expected output shape, instructions
- Prompts enforce two hard requirements:
  - Clause concatenation must reconstruct original text exactly
  - All refs must be verbatim substrings from source

### Step 3: Run Prompts Through Haiku ⏳ IN PROGRESS
```bash
python3 pipeline/run_haiku_batch.py
```
**Result**: `pipeline/raw/` with JSON responses
- One `.json` per prompt (skips existing files)
- Includes translation, clause breakdown, cross-references, defined terms
- Failures saved as `.FAILED.txt` for inspection

### Step 4: Merge Responses Into Feed (Pending)
```bash
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```
**Result**: Updated `feeds/fsa-basel-cap-jp/feed.json`
- Merges paragraphs into article structure
- Resolves internal references (前項/前二項 → actual node IDs)
- Runs QA gates: clause reconstruction + ref verbatim checks
- Updates term registry

### Step 5: Generate Article-Level Summaries (Pending)
```bash
python3 pipeline/make_summary_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/prompts
python3 pipeline/run_haiku_batch.py
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
```
**Result**: Article summaries merged into feed
- Whole-article summaries for navigation/preview
- Uses complete article text as context

### Step 6: Validate Feed ✅ Will validate after Step 4
```bash
python3 -c "
import json, jsonschema
schema = json.load(open('pipeline/schema/rule-feed.schema.json'))
feed = json.load(open('feeds/fsa-basel-cap-jp/feed.json'))
jsonschema.validate(instance=feed, schema=schema)
print('✅ VALID')
"
```

### Step 7: View in App (Pending)
```bash
# From project root
python3 -m http.server 8877
# Open: http://localhost:8877/app/index.html
```
Navigate to "FSA — Basel Cap Adequacy" → "Chapter 2: Formulas, etc."

---

## Expected Output Structure

After Step 4, the feed will contain:

```
feeds/fsa-basel-cap-jp/feed.json
├── root
│   └── children: [Chapters]
│       └── ch2: "第二章 算式等"
│           └── children: [Articles]
│               ├── art2: "連結自己資本規制比率の計算方法"
│               │   └── children: [Paragraphs]
│               │       └── p1: (translated, clause breakdown, refs, defined terms)
│               ├── art3: "連結の範囲"
│               │   └── children: [3 paragraphs]
│               └── ... (24 more articles, 84 total paragraphs)
```

Each paragraph node contains:
- **text_ja**: Original Japanese regulation text
- **text_en**: Legal English translation  
- **clauses_ja/en**: Sentence broken into structural clauses
- **refs**: Cross-references (internal/external) with summaries
- **defined_terms**: Terms explicitly defined in this text

---

## Quality Checks Built Into Pipeline

### Clause Reconstruction Check (Step 4)
Concatenating `clauses_ja[].text` must equal `text_ja` exactly:
- Catches: missing punctuation, incorrect segmentation
- Also runs for English (`clauses_en` → `text_en`)

### Reference Verbatim Check (Step 4)
Every `refs[].raw_text` must be a substring of `text_ja`:
- Catches: fabricated citations, paraphrased refs
- Critical because refs are later resolved to article IDs

---

## Known Limitations

### Missing Formulas
- Articles in Chapter 2 contain math formulas as **images** in the PDF
- Text extraction sees blank lines where formulas should be
- Prompts are told to preserve these gaps, not invent formulas
- Real fix: manual transcription or screenshot + embed as images

### Unresolved Reference Types (To-Do)
- **Relative article refs**: "前条" (preceding article)
  - Only paragraph-level "前項" (preceding paragraph) are resolved
  - Add to `resolve_internal_ref()` in `ingest.py` when needed

- **Absolute refs**: "第五条第一項" (Article 5, Paragraph 1)
  - Will resolve once more of Chapter 2 is populated

---

## Monitoring Progress

During Step 3, check progress:
```bash
# Count completed responses
ls pipeline/raw/*.json 2>/dev/null | wc -l

# Check for failures
ls pipeline/raw/*.FAILED.* 2>/dev/null

# Watch the API call log (if you add it)
tail -f /path/to/api.log
```

---

## Troubleshooting

### API Key Not Found
```
Error: Could not resolve authentication method
```
**Solution**: Set `ANTHROPIC_API_KEY` before running:
```bash
export ANTHROPIC_API_KEY=sk-ant-xxxxx
python3 pipeline/run_haiku_batch.py
```

### JSON Parse Error
```
FAILED: fsa-basel-cap-jp.ch2.art2.p1 ("Expecting value" line X)
```
**Solution**: Check `pipeline/raw/fsa-basel-cap-jp.ch2.art2.p1.FAILED.txt`
- Model returned invalid JSON
- Review the prompt and model response
- May need manual fixing

### Validation Failure (Step 6)
```
ValidationError: 'external_name' is a required property
```
**Solution**: Check `ingest.py` — schema and response must match
- Likely a response missing a field
- Review schema at `pipeline/schema/rule-feed.schema.json`

---

## Timeline Estimate

| Step | Estimate | Status |
|------|----------|--------|
| 1: Extract PDF | ~30s | ✅ Done |
| 2: Generate Prompts | ~10s | ✅ Done |
| 3: Batch API calls | 5-10 min | ⏳ Needs key |
| 4: Ingest & QA | ~30s | Pending |
| 5: Summaries | 2-3 min | Pending |
| 6: Validate | ~5s | Pending |
| **Total** | **~10-15 min** | |

---

## Next Steps

1. **Get your API key** from Anthropic (if you don't have one)
2. **Run Step 3** with the API key in an interactive terminal
3. **Run Steps 4-7** after Step 3 completes (can all be done automatically)
4. **Verify** by opening the app and navigating to Chapter 2

