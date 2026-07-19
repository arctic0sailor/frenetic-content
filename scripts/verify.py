#!/usr/bin/env python3
# scripts/verify.py — anchor pre-check, then one adversarial Opus call per
# candidate. Survivors land in work/survivors.json.
import json
import pathlib
import re
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anchor_check import anchor_present, fetch_plaintext
from validate import validate_batch

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERIFY_PROMPT = (ROOT / "prompts" / "verify.md").read_text()


def structural_ok(candidate):
    """Per-candidate schema check (unique-id check happens at assemble time)."""
    return not validate_batch([candidate], set())


def claude_verdict(candidate):
    prompt = VERIFY_PROMPT.replace("{{CANDIDATE}}", json.dumps(candidate, indent=2))
    result = subprocess.run(
        ["claude", "-p", prompt,
         "--model", "claude-opus-4-8",
         "--allowedTools", "WebSearch,WebFetch",
         "--max-turns", "25"],
        capture_output=True, text=True, timeout=900,
    )
    if result.returncode != 0:
        return None
    # The reply should be bare JSON; be tolerant of stray prose around it.
    match = re.search(r"\{.*\}", result.stdout, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def main():
    candidates = json.loads((ROOT / "work" / "candidates.json").read_text())
    survivors = []
    for candidate in candidates:
        label = candidate.get("question", "?")[:60]
        if not structural_ok(candidate):
            print(f"KILL (schema): {label}")
            continue
        article = fetch_plaintext(candidate["articleTitle"])
        if not anchor_present(candidate["anchorText"], article):
            print(f"KILL (anchor not verbatim): {label}")
            continue
        verdict = claude_verdict(candidate)
        if verdict is None:
            print(f"KILL (verifier failed to answer): {label}")
            continue
        if verdict.get("verdict") != "pass":
            print(f"KILL ({'; '.join(verdict.get('reasons', ['no reason']))}): {label}")
            continue
        print(f"PASS: {label}")
        survivors.append(candidate)

    (ROOT / "work" / "survivors.json").write_text(json.dumps(survivors, indent=2))
    print(f"verify: {len(survivors)}/{len(candidates)} survived")


if __name__ == "__main__":
    main()
