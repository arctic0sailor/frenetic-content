#!/bin/bash
# scripts/generate.sh <date> <categories>
# Pass 1: one Opus run researches and writes work/candidates.json.
set -euo pipefail
cd "$(dirname "$0")/.."

DATE="${1:?usage: generate.sh <YYYY-MM-DD> <categories>}"
CATEGORIES="${2:?usage: generate.sh <YYYY-MM-DD> <categories>}"

mkdir -p work
rm -f work/candidates.json

PROMPT=$(sed -e "s/{{DATE}}/$DATE/g" -e "s/{{CATEGORIES}}/$CATEGORIES/g" prompts/generate.md)

claude -p "$PROMPT" \
  --model claude-opus-4-8 \
  --allowedTools "WebSearch,WebFetch,Write" \
  --max-turns 60

test -s work/candidates.json || { echo "generate: no candidates written" >&2; exit 1; }
python3 -c "import json; json.load(open('work/candidates.json'))" \
  || { echo "generate: candidates.json is not valid JSON" >&2; exit 1; }
echo "generate: $(python3 -c "import json; print(len(json.load(open('work/candidates.json'))))") candidates"
