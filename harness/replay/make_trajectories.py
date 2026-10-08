#!/usr/bin/env python3
"""Write the replay trajectories: the recorded steps of the Part A run, one JSONL per stage.

These are the tool calls, messages and reports of the recorded run (shortened). The
replay shows them, copies that run's judgment files, and then the harness runs every
script and check for real against this run's workspace.
"""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def tc(agent, tool, inp):
    return {"type": "tool_call", "agent": agent, "tool": tool, "input": inp}


def res(agent, tool, text):
    return {"type": "tool_result", "agent": agent, "tool": tool, "text": text}


def txt(agent, text):
    return {"type": "text", "agent": agent, "text": text}


def msg(frm, to, text):
    return {"type": "message", "agent": frm, "to": to, "text": text}


T = {}
T["extract_rules"] = [
    {"type": "agent_turn", "agent": "main", "text": "/extract-rules"},
    txt("main", "Checking preconditions, then extracting the text twice."),
    tc("main", "Bash", "pdfinfo data/contract-rules.pdf | head -20"),
    res("main", "Bash", "[exit 0]\nPages:           15"),
    tc("main", "Bash", "pdftotext data/contract-rules.pdf .scratch/contract-rules.txt && pdftotext -layout data/contract-rules.pdf .scratch/contract-rules-layout.txt"),
    tc("main", "Read", '{"file_path": ".scratch/contract-rules.txt"}'),
    tc("main", "Read", '{"file_path": ".scratch/contract-rules-layout.txt", "offset": 640}'),
    txt("main", "Walking every clause and appendix row: 66 testable rules, 104 excluded, and 4 thresholds the PDF names but never states."),
    tc("main", "Write", "outputs/rules.json (66 rules, 104 excluded, 4 null parameters)"),
    tc("main", "Bash", ".venv/bin/python .claude/skills/extract-rules/verify_quotes.py outputs/rules.json data/contract-rules.pdf"),
    res("main", "Bash", "[exit 0]\nrules.json: 66 rules, 104 excluded, 4 parameters\n\nALL CHECKS PASSED (66 rules, 104 excluded, 0 warning(s))"),
    {"type": "report", "agent": "main", "text": "66 rules (5 threshold, 24 approver, 36 required-action, 1 anti-avoidance), 104 excluded clauses. "
     "Four statutory Threshold parameters are null: the PDF names them but never gives the figures. Notes include the VAT "
     "contradiction between 6.15 and Appendix B and the blank 'Part []' placeholders. Spot-check suggestion: 6.16, App B row B1, App C row D."},
]
T["analysts"] = [
    {"type": "agent_turn", "agent": "spend-analyst", "text": "Run the spend-analyst."},
    {"type": "agent_turn", "agent": "findings-analyst", "text": "Run the findings-analyst."},
    tc("spend-analyst", "Read", '{"file_path": "outputs/rules.json"}'),
    tc("findings-analyst", "Bash", "ls data/committee && for f in data/committee/*.pdf; do pdfinfo \"$f\" | grep Pages; done"),
    txt("spend-analyst", "Thresholds from rules.json: £1,000 (one quote), £25,000 and £500,000 (competition), £2.5m (Executive approval). Statutory tiers skipped: parameters null."),
    tc("spend-analyst", "Bash", ".venv/bin/python -c 'profile each workbook with .head() and .info()'"),
    res("spend-analyst", "Bash", "[exit 0]\n3 workbooks · sheet 'Data to publish' · header on row 1 in one file, row 2 in the others · 10,607 rows"),
    tc("findings-analyst", "Bash", "pdftotext data/committee/<each>.pdf .scratch/committee/<each>.txt && pdftotext -layout ..."),
    tc("spend-analyst", "Write", "scripts/common.py"),
    tc("spend-analyst", "Write", "scripts/clean.py"),
    tc("findings-analyst", "Read", '{"file_path": ".scratch/committee/risk-management-strategy-2024-27.layout.txt", "offset": 560}'),
    tc("spend-analyst", "Write", "scripts/analyse.py"),
    tc("spend-analyst", "Bash", ".venv/bin/python scripts/clean.py && .venv/bin/python scripts/analyse.py"),
    res("spend-analyst", "Bash", "[exit 0]\nspend: 10607 rows raw, 8534 kept, 3 months\nsplit_purchases T=25000: 251 windows; general procurement 64 windows / 42 suppliers\nhigh_value_suppliers: 674 (general procurement 228)\nexpired_notice_spend: 7 suppliers\nspend_vs_award: 8 of 19 flagged"),
    tc("findings-analyst", "Write", "outputs/history.json (20 audits, scoring method, 11 risk themes, 10 discrepancies)"),
    tc("spend-analyst", "Write", "scripts/selfcheck.py"),
    tc("findings-analyst", "Bash", ".venv/bin/python scripts/verify_history.py outputs/history.json data/committee"),
    res("findings-analyst", "Bash", "[exit 0]\nhistory.json: 74 sourced items, 74 quotes, 4 documents\n\nALL CHECKS PASSED"),
    tc("spend-analyst", "Bash", ".venv/bin/python scripts/selfcheck.py"),
    res("spend-analyst", "Bash", "[exit 0]\nselfcheck: 7 matched, 0 failed"),
    {"type": "report", "agent": "findings-analyst", "text": "20 audits recorded; 4 directly about buying (Contract Letting and Accounts Payable: Reasonable; "
     "Personal Budgets (Direct Payments): Limited; Purchase of Residential and Nursing Care: Reasonable). No paper lists agreed actions; "
     "Appendix D is not in the file. Scoring method usable: 5x5 matrix, Table 4 bands. 10 discrepancies recorded, including Figure 4 vs Table 4."},
    {"type": "report", "agent": "spend-analyst", "text": "10,607 rows, 8,534 after excluding redacted payees, pension contributions and payments to other public bodies. "
     "Every figure is in outputs/analytics.json; every flagged payment carries a row_id. Self-check matched one item per test."},
]
T["risk"] = [
    {"type": "agent_turn", "agent": "risk-assessor", "text": "Run the risk-assessor."},
    tc("risk-assessor", "Read", '{"file_path": ".claude/skills/risk-assessment/SKILL.md"}'),
    tc("risk-assessor", "Read", '{"file_path": "outputs/analytics.json"}'),
    tc("risk-assessor", "Read", '{"file_path": "outputs/history.json"}'),
    tc("risk-assessor", "Read", '{"file_path": "outputs/rules.json"}'),
    txt("risk-assessor", "Working through the theme table: 10 risks, 6 themes excluded for lack of an observable signal. Placements take a repeat-finding uplift from the Limited opinion on Personal Budgets."),
    tc("risk-assessor", "Write", "outputs/risk-ratings.json (10 risks, 6 excluded)"),
    tc("risk-assessor", "Bash", ".venv/bin/python .claude/skills/risk-assessment/build_register.py"),
    res("risk-assessor", "Bash", "[exit 0]\nWARN  R-02.likelihood: literal figure typed in prose\n\nrisks kept: 10, excluded by validation: 0, warnings: 1, failures: 0"),
    txt("risk-assessor", "Treating the warning as a failure: rephrasing the population note without a typed figure."),
    tc("risk-assessor", "Edit", "outputs/risk-ratings.json"),
    tc("risk-assessor", "Bash", ".venv/bin/python .claude/skills/risk-assessment/build_register.py"),
    res("risk-assessor", "Bash", "[exit 0]\nrisks kept: 10, excluded by validation: 0, warnings: 0, failures: 0\nwritten: outputs/auditor-comments.md (10 risks, 0 with a decision already recorded)"),
    {"type": "report", "agent": "risk-assessor", "text": "8 risks in the Medium-High band, 2 Moderate. Top: R-01 quotes not evidenced (12), R-02 split purchases (12), "
     "R-06 spend above award (12), R-08 placements (12, uplifted). R-10 grants recommended out of scope. Please record a decision for every risk in outputs/auditor-comments.md."},
]
T["team"] = [
    {"type": "lead", "agent": "lead", "text": "spawning planner, challenger and qa-reviewer as teammates"},
    tc("planner", "Read", '{"file_path": ".claude/skills/audit-program/SKILL.md"}'),
    tc("planner", "Bash", "head -3 outputs/analytics-full/split-purchases-windows.csv outputs/analytics-full/high-value-suppliers.csv ..."),
    tc("planner", "Write", "outputs/audit-plan.json"),
    tc("planner", "Bash", ".venv/bin/python .claude/skills/audit-program/build_pack.py"),
    res("planner", "Bash", "[exit 1]\nFAIL  R-01.C-01.3: literal figure typed in prose ...\nFAIL  R-09.T-09.2: sample recipe yielded no transactions\nfailures: 7"),
    txt("planner", "Fixing: 'S.151' and '£500' count as typed figures; T-09.2's exclusion emptied its sample."),
    tc("planner", "Edit", "outputs/audit-plan.json"),
    tc("planner", "Bash", ".venv/bin/python .claude/skills/audit-program/build_pack.py"),
    res("planner", "Bash", "[exit 0]\nscope: 9 approved risks planned; controls: 15; tests: 15; sampled transactions: 155; failures: 0"),
    msg("planner", "challenger", "PACK READY v1 · 9 risks, 15 controls, 15 tests, 155 transactions, 0 failures"),
    msg("planner", "qa-reviewer", "PACK READY v1 · 9 risks, 15 controls, 15 tests, 155 transactions, 0 failures"),
    tc("qa-reviewer", "Bash", ".venv/bin/python scripts/checks/run_checks.py"),
    res("qa-reviewer", "Bash", "[exit 1]\n| quotes | FAIL | ... |\n| trace | FAIL | challenges.md missing |"),
    msg("qa-reviewer", "lead", "QA BLOCKED ON INPUT: verify_quotes.py fell back to pypdf because pdftotext is not on the checks' PATH"),
    msg("lead", "qa-reviewer", "poppler is now on the PATH; re-run on the next PACK READY"),
    tc("challenger", "Read", '{"file_path": "outputs/audit-program.md"}'),
    msg("challenger", "planner", "CHALLENGE #1 [sample] R-02: three payments per window is too few to judge aggregation. Evidence: T-02.1; $.tests.split_purchases.per_threshold[0].headline_general_procurement.windows. Ask: raise per_group_n."),
    msg("challenger", "planner", "CHALLENGE #2 [sample] R-07: placements hold most duplicate value but are not sampled. Evidence: $.tests.duplicates.per_tier.different_time.placements.gbp_beyond_first. Ask: add a placement test under C-07.1."),
    msg("challenger", "planner", "CHALLENGE #3 [coverage] R-01: CPR-10 can be tested on the R-01 contract files. Ask: cite it in T-01.1."),
    msg("challenger", "planner", "CHALLENGE #4 [control] R-04: T-01.1 suppliers with no notice get no register check. Ask: extend T-04.2."),
    msg("challenger", "planner", "CHALLENGE #5 [test] R-09: windows are not contracts. Ask: sample suppliers by annualised spend."),
    msg("challenger", "planner", "CHALLENGE #6 [rating] R-04: likelihood 3 beside a strong unmatched-supplier signal. Ask: auditor to confirm."),
    msg("planner", "challenger", "RESPONSE #1: accepted · RESPONSE #2: accepted · RESPONSE #3: accepted · RESPONSE #4: accepted · RESPONSE #5: declined (T-09.2 already samples by annualised spend) · RESPONSE #6: for the auditor"),
    tc("planner", "Edit", "outputs/audit-plan.json"),
    tc("planner", "Bash", ".venv/bin/python .claude/skills/audit-program/build_pack.py"),
    res("planner", "Bash", "[exit 0]\ncontrols: 15; tests: 16; sampled transactions: 256; failures: 0"),
    msg("planner", "challenger", "PACK READY v2"),
    msg("planner", "qa-reviewer", "PACK READY v2"),
    msg("challenger", "planner", "CHALLENGE #7 [sample] R-08: T-08.2 has five providers for a score-12 risk. Ask: ten."),
    msg("challenger", "planner", "CHALLENGE #8 [coverage] R-01: the redacted-payee limitation is not in the memo. Ask: add it."),
    msg("planner", "challenger", "RESPONSE #7: accepted · RESPONSE #8: accepted"),
    tc("planner", "Bash", ".venv/bin/python .claude/skills/audit-program/build_pack.py"),
    msg("planner", "challenger", "PACK READY v3"),
    msg("planner", "qa-reviewer", "PACK READY v3"),
    tc("challenger", "Write", "outputs/challenges.md (8 challenges: 6 resolved, 1 declined, 1 for the auditor)"),
    msg("challenger", "lead", "CHALLENGER DONE · 6 resolved, 1 declined, 1 for the auditor (#6, R-04 likelihood)"),
    msg("planner", "lead", "PLANNER DONE v3 · 9 risks, 15 controls, 16 tests, 261 sampled transactions, 0 open points"),
    tc("qa-reviewer", "Bash", ".venv/bin/python scripts/checks/run_checks.py"),
    res("qa-reviewer", "Bash", "[exit 0]\nVERDICT: READY FOR SIGN-OFF (4/4 checks pass)"),
    tc("qa-reviewer", "Write", "outputs/review.md"),
    msg("qa-reviewer", "lead", "QA DONE: READY FOR SIGN-OFF"),
    {"type": "lead", "agent": "lead", "text": "team shut down: PLANNER DONE=yes, CHALLENGER DONE=yes, QA DONE=yes"},
]

for stage, evs in T.items():
    d = HERE / stage
    d.mkdir(parents=True, exist_ok=True)
    (d / "trajectory.jsonl").write_text("\n".join(json.dumps(e, ensure_ascii=False) for e in evs) + "\n", encoding="utf-8")
    print(stage, len(evs), "events")
