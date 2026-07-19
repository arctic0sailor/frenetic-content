# frenetic-content

Daily counter-intuitive quiz questions for the frenetic iOS app.
Generated nightly on godel by a two-pass Claude pipeline (generate → adversarial
verify), schema-gated, and served to the app as static JSON:

- `manifest.json` — `{"batches": [...]}`, the app's sync index
- `content/<name>.json` — one published batch per pipeline run

Question text derives from Wikipedia — CC BY-SA 4.0, attribution in every entry.

Run nightly: `scripts/nightly.sh` (installed via `launchd/…plist`).
Backfill: `scripts/backfill.sh <runs>`. Tests: `python3 -m unittest discover -s tests -v`.
