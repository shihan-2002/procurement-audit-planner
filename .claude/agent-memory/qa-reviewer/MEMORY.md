# qa-reviewer memory (how-to only)

- 2026-10-08 · run_checks.py needs `pdftotext` on PATH; without it verify_quotes.py falls back to pypdf and reports false quote failures. Report as QA BLOCKED ON INPUT, do not soften.
- 2026-10-08 · The trace check fails until challenges.md exists; wait for CHALLENGER DONE before writing review.md.
