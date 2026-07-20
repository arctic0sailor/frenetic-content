#!/usr/bin/env python3
# scripts/verify.py — anchor pre-check, then one adversarial Opus call per
# candidate. Survivors land in work/survivors.json.
import json
import pathlib
import re
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from anchor_check import anchor_present, fetch_plaintext
from validate import validate_batch

ROOT = pathlib.Path(__file__).resolve().parent.parent
VERIFY_PROMPT = (ROOT / "prompts" / "verify.md").read_text()


def structural_ok(candidate):
    """Per-candidate schema check (unique-id check happens at assemble time)."""
    return not validate_batch([candidate], set())


def fetch_article(title):
    """Article plaintext, or None if fetching is persistently broken
    (infrastructure failure — not an editorial verdict)."""
    for attempt in range(2):
        try:
            return fetch_plaintext(title)
        except Exception:
            if attempt == 0:
                time.sleep(30)
    return None


def claude_verdict(candidate):
    """Returns a dict verdict, None (clean exit but unparseable — stays a
    kill), or the string "infra" for a timeout or non-zero exit."""
    prompt = VERIFY_PROMPT.replace("{{CANDIDATE}}", json.dumps(candidate, indent=2))
    try:
        result = subprocess.run(
            ["claude", "-p", prompt,
             "--model", "claude-opus-4-8",
             "--allowedTools", "WebSearch,WebFetch",
             "--max-turns", "25"],
            capture_output=True, text=True, timeout=900,
        )
    except subprocess.TimeoutExpired:
        return "infra"
    if result.returncode != 0:
        return "infra"
    try:
        return json.loads(result.stdout.strip())
    except json.JSONDecodeError:
        pass
    # The reply should be bare JSON; be tolerant of stray prose around it.
    match = re.search(r"\{.*\}", result.stdout, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def verify_one(candidate, label):
    """Returns ("pass"|"kill"|"infra", message-or-None)."""
    if not structural_ok(candidate):
        return "kill", f"KILL (schema): {label}"
    article = fetch_article(candidate["articleTitle"])
    if article is None:
        return "infra", None
    if not anchor_present(candidate["anchorText"], article):
        return "kill", f"KILL (anchor not verbatim): {label}"
    verdict = claude_verdict(candidate)
    if verdict == "infra":
        return "infra", None
    if verdict is None:
        return "kill", f"KILL (verifier failed to answer): {label}"
    if verdict.get("verdict") != "pass":
        return "kill", f"KILL ({'; '.join(verdict.get('reasons', ['no reason']))}): {label}"
    return "pass", f"PASS: {label}"


def main():
    candidates = json.loads((ROOT / "work" / "candidates.json").read_text())
    survivors = []
    consecutive_infra = 0
    for candidate in candidates:
        label = candidate.get("question", "?")[:60]
        result, msg = verify_one(candidate, label)
        if result == "infra":
            time.sleep(90)
            result, msg = verify_one(candidate, label)
        if result == "infra":
            print(f"INFRA: {label}")
            consecutive_infra += 1
            if consecutive_infra >= 3:
                print("verify: aborting after 3 consecutive infrastructure failures")
                sys.exit(1)
            continue
        consecutive_infra = 0
        print(msg)
        if result == "pass":
            survivors.append(candidate)

    (ROOT / "work" / "survivors.json").write_text(json.dumps(survivors, indent=2))
    print(f"verify: {len(survivors)}/{len(candidates)} survived")


if __name__ == "__main__":
    main()
