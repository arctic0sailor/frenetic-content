#!/bin/bash
# scripts/backfill.sh <runs> — build the pre-launch pool. Each run publishes
# backfill-<n>.json so names never collide with nightly date batches.
set -euo pipefail
cd "$(dirname "$0")/.."

RUNS="${1:?usage: backfill.sh <runs>}"
for i in $(seq 1 "$RUNS"); do
  n=1
  while [ -f "content/backfill-$(printf '%03d' "$n").json" ]; do n=$((n + 1)); done
  name="backfill-$(printf '%03d' "$n").json"
  echo "=== backfill run $i/$RUNS → $name ==="
  scripts/nightly.sh "$name" || echo "run $i failed; continuing"
  tail -3 "logs/nightly-$(date +%F).log" || true
done
total=$(python3 -c "
import json, pathlib
print(sum(len(json.loads(p.read_text())) for p in pathlib.Path('content').glob('*.json')))")
echo "backfill: pool now holds $total questions"
