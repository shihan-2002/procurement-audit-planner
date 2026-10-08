# spend-analyst memory (how-to only; never evidence)

- 2026-10-08 · Header row moves between workbooks (row 1 in P02, row 2 in P03/P04). Read with header=None and find the row whose first cell is `Service`; sheet_row = raw index + 1 matches the Excel row (verified with openpyxl).
- 2026-10-08 · Appendix B row A (one quote above £1,000) is not competition; treat a threshold as competition-triggering only when the rule asks for three or more quotes or tenders, else high_value_suppliers would include almost every supplier.
- 2026-10-08 · Never hard-code rule IDs in analyse.py; look them up by clause from rules.json (a typed ID pointed at the wrong rule once).
- 2026-10-08 · pandas warns on regexes with capture groups in str.contains; use non-capturing groups.
