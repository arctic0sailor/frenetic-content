#!/bin/bash
# scripts/nightly.sh [batch-name] — the whole pipeline. launchd entry point.
set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
cd "$(dirname "$0")/.."

DATE=$(date +%F)
BATCH="${1:-$DATE.json}"
LOG="logs/nightly-$DATE.log"
mkdir -p logs work

# Category wheel: 3 of 9 per night, rotating by day-of-year.
CATS=(science history space biology engineering geography culture medicine mathematics)
DOY=$((10#$(date +%j)))
PICK="${CATS[$((DOY % 9))]}, ${CATS[$(((DOY + 3) % 9))]}, ${CATS[$(((DOY + 6) % 9))]}"

{
  echo "=== frenetic-content nightly $DATE (batch $BATCH, cats: $PICK) ==="
  if [ -f "content/$BATCH" ]; then
    echo "SKIP: content/$BATCH already published"
    exit 0
  fi

  scripts/generate.sh "$DATE" "$PICK" || { echo "FAILED: generate"; exit 1; }
  python3 scripts/verify.py           || { echo "FAILED: verify"; exit 1; }

  python3 scripts/assemble.py "$BATCH"
  status=$?
  if [ "$status" -eq 3 ]; then
    echo "OK: zero survivors tonight, nothing published"
    exit 0
  elif [ "$status" -ne 0 ]; then
    echo "FAILED: assemble (validation)"
    exit 1
  fi

  git add "content/$BATCH" manifest.json
  git commit -m "content: $BATCH

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" || { echo "FAILED: commit"; exit 1; }
  git push origin main || { echo "FAILED: push (batch committed locally)"; exit 1; }
  echo "OK: published $BATCH"
} >> "$LOG" 2>&1
