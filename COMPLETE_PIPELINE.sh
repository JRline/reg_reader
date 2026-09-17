#!/bin/bash
# Complete extraction pipeline for Chapter 2
# Run this after Step 3 (batch processing) is done

set -e
cd "$(dirname "$0")"

echo "════════════════════════════════════════════════════════════════"
echo "  FSA Basel Chapter 2 — Complete Extraction Pipeline"
echo "════════════════════════════════════════════════════════════════"
echo ""

# Verify prerequisites
if [ ! -f "pipeline/run_haiku_batch.py" ]; then
  echo "❌ Error: Not in project root (missing pipeline/)"
  exit 1
fi

json_count=$(ls -1 pipeline/raw/*.json 2>/dev/null | wc -l)
echo "📊 Current status: $json_count/83 response files ready"
echo ""

# Check if Step 3 is complete
if [ "$json_count" -lt 83 ]; then
  echo "⚠️  Step 3 (Batch Processing) is not complete."
  echo ""
  echo "Complete it first with:"
  echo "  export ANTHROPIC_API_KEY=sk-ant-..."
  echo "  python3 pipeline/run_haiku_batch.py"
  echo ""
  exit 1
fi

echo "✅ Step 3 complete — proceeding with Steps 4-7"
echo ""

# Step 4: Merge into feed
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 4: Merge responses into feed (with QA checks)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
echo ""

# Step 5: Article summaries
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 5: Generate article-level summaries"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Generating summary prompts..."
python3 pipeline/make_summary_prompts.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 pipeline/prompts
echo "Calling Haiku for summaries (this runs the same batch script)..."
python3 pipeline/run_haiku_batch.py
echo "Merging summaries into feed..."
python3 pipeline/batch_ingest.py fsa-basel-cap-jp fsa-basel-cap-jp.ch2 第二章 算式等 pipeline/source/ch2_articles.json
echo ""

# Step 6: Validate
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Step 6: Validate feed schema"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
python3 -c "
import json, jsonschema
try:
    schema = json.load(open('pipeline/schema/rule-feed.schema.json'))
    feed = json.load(open('feeds/fsa-basel-cap-jp/feed.json'))
    jsonschema.validate(instance=feed, schema=schema)
    print('✅ Feed validation PASSED')
except jsonschema.ValidationError as e:
    print(f'❌ Validation failed: {e.message}')
    exit(1)
"
echo ""

# Summary
echo "════════════════════════════════════════════════════════════════"
echo "  ✅ EXTRACTION COMPLETE"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "Feed location: feeds/fsa-basel-cap-jp/feed.json"
echo ""
echo "To view in the app:"
echo "  python3 -m http.server 8877"
echo "  # Then open: http://localhost:8877/app/index.html"
echo ""
echo "Next steps:"
echo "  1. Open the web app at localhost:8877/app/index.html"
echo "  2. Navigate to: FSA — Basel Cap Adequacy → Chapter 2"
echo "  3. Click through articles to verify translations and cross-references"
echo ""
