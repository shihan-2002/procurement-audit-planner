# Procurement audit: planning memo

*Generated 2026-10-08 by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision 2), `auditor-comments.md` by Shihan Wang dated 2026-10-08, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review and auditor sign-off.*

**Indicators, not findings.** Every test below checks a control against a pattern in public data. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

## Purpose

This audit tests whether West Berkshire Council's purchasing follows its own Contract Rules where the public spend data shows patterns that warrant a closer look: payments split below a threshold, high-value suppliers with no published contract notice, spend past a notice's end or above its award, possible duplicate payments, placements chosen without recorded reasons, and awards that needed a Key Decision.
It plans fieldwork. It reaches no findings: every pattern below is an indicator to investigate, and a flagged payment may have a full and proper explanation.

## Background

The spend analysis covered 10,607 published payments from 2026-05-01 to 2026-07-31 (3 months) [metric:$.population.rows_raw]. After excluding redacted payees, pension contributions and payments to other public bodies, 8,534 payments worth £66,778,104.78 were tested against the Rules [metric:$.population.rows_after_exclusions].
General procurement accounts for £28,321,138.16 of that spend and care or education placements for £30,571,711.30 [metric:$.population.tags.general_procurement.gbp]. Placements recur by design, so every test reports them separately.
The Contracts Finder export held 141 notices for the council, of which 62 were active during the spend window [metric:$.contracts.active_in_window]. No contract register was available.
Recent internal audit coverage includes Contract Letting and Accounts Payable (Reasonable Assurance) and Personal Budgets (Direct Payments) (Limited Assurance), as recorded in history.json.

## Scope

The register lists 9 rated risks. The auditor recorded 10 decisions by Shihan Wang dated 2026-10-08: 9 risks are approved and in scope, and 1 is not.

| ID | Risk | Score | Band | Decision | Auditor comment |
|---|---|---|---|---|---|
| R-01 | Quotes or tenders not evidenced for spend at or above the quote threshold | 12 | Medium - High | approve |  |
| R-02 | Requirements split so each payment stays below the quote threshold | 12 | Medium - High | approve |  |
| R-06 | Spend running ahead of the awarded contract value without an approved variation | 12 | Medium - High | approve |  |
| R-08 | Care and education placements without recorded reasons or board approval | 12 | Medium - High | approve |  |
| R-09 | Key Decision and delegated-authority approvals for awards above the Key Decision threshold | 12 | Medium - High | amend | Raise likelihood to 3: awards above £500,000 are rare but carry the highest stakes. (auditor override applied) |
| R-04 | High-value suppliers with no published contract notice | 9 | Medium - High | approve |  |
| R-05 | Spend after a contract notice ended without an approved extension | 9 | Medium - High | approve |  |
| R-07 | Possible duplicate payments to the same supplier | 9 | Medium - High | approve |  |
| R-03 | Payments bunched just below the quote threshold | 6 | Moderate | approve |  |

**Not in scope**

- R-10: Grants treated outside the Rules: reject; rejected by the auditor at the gate: Grants will be covered by a separate review.

## Approach

The Contract Rules were extracted into testable rules, each with a verbatim quote verified against the PDF. Every payment in the window was tested by script against the thresholds in those rules, and the committee papers were read for audit history and the council's own scoring method.
Risks were rated likelihood × impact on the council's five-point scales, every rating citing a rule, a metric or an audit item, and the auditor approved, amended or rejected each risk at the gate.
For each approved risk the plan names the control the Rules require, a test of it, and a sample recipe. Samples are drawn by script from the full flagged lists, largest first, sized by score: ten items for risks scoring nine or more and five below that. Each sampled payment is listed with its row in the council's workbook.

The programme holds 15 expected controls and 16 test steps, with 261 sampled transactions worth £21,843,982.83, each traceable to its row in the council's published workbooks (see `audit-program.md` and `outputs/samples/`).

## Rules coverage

39 of 66 rules in `rules.json` are cited by a risk, a control or a test. The remaining 27 are not tested in this audit, for these reasons:

- above-Threshold procedure, publication or sealing duty: the statutory Threshold figures are null in rules.json, so above-Threshold contracts cannot be identified from the data: CPR-01, CPR-12, CPR-15, CPR-16, CPR-17, CPR-18, CPR-48, CPR-59
- legal and contract-file control with no transaction signal; outside a spend-led procurement audit: CPR-35, CPR-37, CPR-38, CPR-39, CPR-40, CPR-42, CPR-43, CPR-44, CPR-45, CPR-46, CPR-47, CPR-49, CPR-50
- governance, reporting or retention duty not linked to individual payments: CPR-03, CPR-09, CPR-31
- transparency obligation met by the published spend dataset this audit uses: CPR-06
- payment terms cannot be measured: the spend Date is a payment-run timestamp, not an invoice date: CPR-41
- Provider Selection Regime contracts are not identifiable in the spend or notice data: CPR-61

## Limitations

- The population is published expenditure above the transparency floor only, so split and duplicate counts are lower bounds.
- Payments published with the supplier 'Redacted' (2,015 rows) are excluded from every supplier-level test, so no sample can reach them [metric:$.population.excluded.redacted_supplier.rows].
- The spend Date is a payment-run timestamp, not an invoice date.
- The statutory Threshold figures are not stated in the Rules and were not supplied, so above-Threshold tiers are not separated in the samples.
- The notices file is not a contract register: a supplier with no notice is a question for the register, not evidence of off-contract spend.
- Annualised estimates extrapolate three months and ignore seasonality; award values may be estimates or maxima.
- Appendix D (the three-year audit plan) and the individual audit reports are not public, so planned coverage and the reasons for past opinions are unknown.

## Review and sign-off

The challenger's points and their status are in `challenges.md`; points marked *for the auditor* need a decision at sign-off. The QA reviewer's checks and verdict are in `review.md`, which ends with the sign-off block.
