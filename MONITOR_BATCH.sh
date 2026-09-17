#!/bin/bash
# Monitor batch processing progress in real-time

cd "$(dirname "$0")"
expected=83

echo "Monitoring batch processing..."
echo "Press Ctrl+C to stop monitoring"
echo ""

while true; do
  json_count=$(ls -1 pipeline/raw/*.json 2>/dev/null | wc -l)
  failed_count=$(ls -1 pipeline/raw/*.FAILED.* 2>/dev/null | wc -l || echo 0)
  pct=$((json_count * 100 / expected))
  
  clear
  echo "╔════════════════════════════════════════════════════════════════╗"
  echo "║         FSA Basel Chapter 2 — Batch Processing Progress        ║"
  echo "╚════════════════════════════════════════════════════════════════╝"
  echo ""
  echo "Status: $json_count / $expected completed ($pct%)"
  echo ""
  
  # Progress bar
  filled=$((pct / 5))
  empty=$((20 - filled))
  bar="["
  for ((i=0; i<filled; i++)); do bar+="█"; done
  for ((i=0; i<empty; i++)); do bar+="░"; done
  bar+="]"
  echo "$bar"
  echo ""
  
  if [ "$failed_count" -gt 0 ]; then
    echo "⚠️  Failures: $failed_count"
    ls -1 pipeline/raw/*.FAILED.* 2>/dev/null | head -3
  fi
  echo ""
  
  if [ "$json_count" -ge "$expected" ]; then
    echo "✅ BATCH PROCESSING COMPLETE!"
    echo ""
    echo "Next step: run ./COMPLETE_PIPELINE.sh"
    break
  fi
  
  echo "Last updated: $(date '+%H:%M:%S')"
  sleep 5
done
