# findings-analyst memory (how-to only; never evidence)

- 2026-10-08 · Impact table (strategy p.14), appetite table (pp.16-17) and the 5x5 matrix (p.18) garble in plain text; read cells from `pdftotext -layout`, quote only contiguous plain-text runs such as "5 Critical > 1% annual WBC budget >£2m".
- 2026-10-08 · Completed-work appendices: title and opinion are often split in plain text; quote "<title> <opinion>" only where contiguous, else quote the title and note the layout reconstruction.
- 2026-10-08 · verify_history.py replaces hyphens with spaces on both sides; en dashes are unified first, so quotes with "–" verify.
