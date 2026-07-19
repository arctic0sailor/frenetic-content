"""Schema gate for question batches. The single source of truth for validity —
mirrors Question.decodeBatch in the iOS app (frenetic repo). Keep in sync."""
import json
import pathlib
import re
import sys

REQUIRED = ["id", "date", "format", "question", "choices", "correctIndex",
            "articleTitle", "articleURL", "anchorText", "thumbnailURL", "attribution"]
CHOICE_COUNT = {"two": 2, "four": 4, "tf": 2}
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
WIKI_PREFIX = "https://en.wikipedia.org/wiki/"


def validate_batch(questions, existing_ids):
    """Return a list of error strings; empty means the batch is valid."""
    errors = []
    if not isinstance(questions, list) or not questions:
        return ["batch must be a non-empty JSON array"]
    seen = set()
    for i, q in enumerate(questions):
        where = f"question[{i}]"
        if not isinstance(q, dict):
            errors.append(f"{where}: not an object")
            continue
        missing = [f for f in REQUIRED if f not in q]
        if missing:
            errors.append(f"{where}: missing {missing}")
            continue
        for field in ["id", "date", "question", "articleTitle", "articleURL",
                      "anchorText", "attribution"]:
            if not isinstance(q[field], str) or not q[field].strip():
                errors.append(f"{where}: {field} must be a non-empty string")
        fmt = q["format"]
        if fmt not in CHOICE_COUNT:
            errors.append(f"{where}: format {fmt!r} not in {sorted(CHOICE_COUNT)}")
            continue
        choices = q["choices"]
        if (not isinstance(choices, list)
                or len(choices) != CHOICE_COUNT[fmt]
                or not all(isinstance(c, str) and c.strip() for c in choices)):
            errors.append(f"{where}: format {fmt!r} needs exactly "
                          f"{CHOICE_COUNT[fmt]} non-empty string choices")
            continue
        if fmt == "tf" and choices != ["True", "False"]:
            errors.append(f"{where}: tf choices must be exactly ['True', 'False']")
        if not isinstance(q["correctIndex"], int) or not 0 <= q["correctIndex"] < len(choices):
            errors.append(f"{where}: correctIndex out of bounds")
        if isinstance(q["date"], str) and not DATE_RE.match(q["date"]):
            errors.append(f"{where}: date must be YYYY-MM-DD")
        if isinstance(q["articleURL"], str) and not q["articleURL"].startswith(WIKI_PREFIX):
            errors.append(f"{where}: articleURL must start with {WIKI_PREFIX}")
        if isinstance(q["anchorText"], str):
            words = len(q["anchorText"].split())
            if not 3 <= words <= 20:
                errors.append(f"{where}: anchorText must be 3-20 words (got {words})")
        if q["thumbnailURL"] is not None and (
                not isinstance(q["thumbnailURL"], str)
                or not q["thumbnailURL"].startswith("https://")):
            errors.append(f"{where}: thumbnailURL must be null or an https URL")
        qid = q["id"]
        if isinstance(qid, str):
            if qid in seen:
                errors.append(f"{where}: duplicate id {qid} within batch")
            if qid in existing_ids:
                errors.append(f"{where}: id {qid} already published")
            seen.add(qid)
    return errors


def existing_ids_in(content_dir):
    ids = set()
    for path in pathlib.Path(content_dir).glob("*.json"):
        try:
            for q in json.loads(path.read_text()):
                ids.add(q.get("id"))
        except (json.JSONDecodeError, AttributeError, TypeError):
            print(f"warning: unreadable published batch {path}", file=sys.stderr)
    return ids


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: validate.py <batch.json> [content_dir]")
    batch = json.loads(pathlib.Path(sys.argv[1]).read_text())
    existing = existing_ids_in(sys.argv[2]) if len(sys.argv) > 2 else set()
    problems = validate_batch(batch, existing)
    for p in problems:
        print(f"INVALID: {p}", file=sys.stderr)
    sys.exit(1 if problems else 0)
