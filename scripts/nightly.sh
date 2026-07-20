#!/bin/bash
# scripts/nightly.sh [batch-name] — the whole pipeline. launchd entry point.
set -uo pipefail
export PATH="/opt/homebrew/bin:/usr/local/bin:$HOME/.local/bin:$PATH"
cd "$(dirname "$0")/.."

DATE=$(date +%F)
BATCH="${1:-$DATE.json}"
LOG="logs/nightly-$DATE.log"
mkdir -p logs work

{
  if ! mkdir work/.lock 2>/dev/null; then
    echo "SKIP: another run holds work/.lock"
    exit 0
  fi
  trap 'rmdir work/.lock 2>/dev/null' EXIT
  rm -f work/survivors.json   # M5: stale survivors from prior runs must not be assembled

  # Category wheel: consecutive trio, rotating per-day for nightly runs and
  # per-run for backfill batches (all same-day backfill runs must differ).
  CATS=(science history space biology engineering geography culture medicine mathematics)
  if [[ "$BATCH" == backfill-* ]]; then
    n="${BATCH#backfill-}"; IDX=$((10#${n%.json}))
  else
    IDX=$((10#$(date +%j)))
  fi
  PICK="${CATS[$((IDX % 9))]}, ${CATS[$(((IDX + 1) % 9))]}, ${CATS[$(((IDX + 2) % 9))]}"

  echo "=== frenetic-content nightly $DATE (batch $BATCH, cats: $PICK) ==="
  if [ -f "content/$BATCH" ] && git ls-files --error-unmatch "content/$BATCH" >/dev/null 2>&1; then
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

  git pull --rebase origin main || { echo "FAILED: pull"; exit 1; }

  git add "content/$BATCH" manifest.json
  git commit -m "content: $BATCH

Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>" || {
    git checkout -- manifest.json 2>/dev/null || true
    rm -f "content/$BATCH"
    echo "FAILED: commit (batch reverted)"
    exit 1
  }
  git push origin main || { echo "FAILED: push (batch committed locally)"; exit 1; }
  echo "OK: published $BATCH"
} >> "$LOG" 2>&1
