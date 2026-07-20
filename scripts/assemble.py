#!/usr/bin/env python3
# scripts/assemble.py <batch-name> — survivors → published batch + manifest.
import json
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from validate import validate_batch, existing_ids_in, existing_urls_in


def assemble(batch_name, root=None):
    root = pathlib.Path(root or pathlib.Path(__file__).resolve().parent.parent)
    survivors = json.loads((root / "work" / "survivors.json").read_text())
    if not survivors:
        print("assemble: zero survivors — nothing to publish")
        return 3

    published_urls = existing_urls_in(root / "content")
    deduped = []
    for q in survivors:
        if q.get("articleURL") in published_urls:
            print(f"DEDUPE (article already published): {q.get('articleTitle')}")
            continue
        deduped.append(q)
    survivors = deduped
    if not survivors:
        print("assemble: zero survivors after dedupe — nothing to publish")
        return 3

    problems = validate_batch(survivors, existing_ids_in(root / "content"))
    if problems:
        for p in problems:
            print(f"assemble: INVALID: {p}", file=sys.stderr)
        return 1

    (root / "content" / batch_name).write_text(json.dumps(survivors, indent=2))

    manifest_path = root / "manifest.json"
    manifest = (json.loads(manifest_path.read_text())
                if manifest_path.exists() else {"batches": []})
    if batch_name not in manifest["batches"]:
        manifest["batches"].append(batch_name)
    manifest_path.write_text(json.dumps(manifest, indent=2))
    print(f"assemble: published content/{batch_name} ({len(survivors)} questions)")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: assemble.py <batch-name.json>")
    sys.exit(assemble(sys.argv[1]))
