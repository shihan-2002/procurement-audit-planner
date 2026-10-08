# Procurement audit planning: risk register

*Status: DRAFT for auditor review (Phase 2 gate).*

**Indicators, not findings.** Every risk describes a pattern in public data or a control to test. Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.

*Generated 2026-10-08 by `build_register.py` from `risk-ratings.json`, `rules.json`, `analytics.json` and `history.json`. Every figure below was filled in by the script.*

## Scoring scale

Scale: the council's own method from the Risk Management Strategy 2024-27 as recorded in history.json (Table 1 impact, Table 2 likelihood, Figure 1 matrix, Table 4 bands). Where the strategy conflicts, this register uses Table 4: Figure 4's rule that risks scoring 9 or above enter the Corporate Risk Register is marked, not applied.

| Score | Likelihood | Impact |
|---|---|---|
| 5 | Certain | Critical |
| 4 | Almost Certain | Major |
| 3 | Likely | Medium |
| 2 | Unlikely | Minor |
| 1 | Rare | Negligible |

| Band | Scores | Response |
|---|---|---|
| Extreme | 15-25 | Allocate to Executive Director to oversee and Service Director implement agreed actions. |
| Medium - High | 8-12 | Allocate to Service Director to put in place Controls Assurance. |
| Moderate | 4-6 | Monitor risk |
| Low | 1-3 | Consider at next annual review |

## Summary

| ID | Risk | L | I | Score | Matrix | Band | Response | Scope |
|---|---|---|---|---|---|---|---|---|
| R-01 | Quotes or tenders not evidenced for spend at or above the quote threshold | 4 | 3 | 12 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-02 | Requirements split so each payment stays below the quote threshold | 4 | 3 | 12 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-06 | Spend running ahead of the awarded contract value without an approved variation | 3 | 4 | 12 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-08 | Care and education placements without recorded reasons or board approval | 4 | 3 | 12 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-04 | High-value suppliers with no published contract notice | 3 | 3 | 9 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-05 | Spend after a contract notice ended without an approved extension | 3 | 3 | 9 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-07 | Possible duplicate payments to the same supplier | 3 | 3 | 9 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-09 | Key Decision and delegated-authority approvals for awards above the Key Decision threshold | 2 | 4 | 8 | High | Medium - High | Allocate to Service Director to put in place Controls Assurance. | in |
| R-03 | Payments bunched just below the quote threshold | 2 | 3 | 6 | Moderate | Moderate | Monitor risk | in |
| R-10 | Grants treated outside the Rules | 2 | 3 | 6 | Moderate | Moderate | Monitor risk | out |

## Risks

### R-01: Quotes or tenders not evidenced for spend at or above the quote threshold

Suppliers whose annualised spend reaches the three-quote threshold should each be backed by a competitive process run through the Procurement Portal and by written evidence of the purchase [CPR-56] [CPR-33]. Where that evidence is missing, the purchase may not have followed the Rules.

- **Likelihood 4 (Almost Certain).** 228 general-procurement suppliers have an annualised estimate at or above £25,000, a pattern that recurs across many suppliers. The most recent Contract Letting audit gave Reasonable Assurance, so no uplift applies.
- **Impact 3 (Medium).** The annualised value exposed is £110,584,320.64. A competition rule breached on contracts of this size carries a reasonable possibility of successful legal challenge, the Medium compliance level of Table 1 [CPR-56]. The compliance column drove the rating; the £ figure is spend exposed, not loss.
- **Score 12: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-56] clause App B row B1: "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including…"
- [rule:CPR-57] clause App B row B2: "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including…"
- [rule:CPR-33] clause 10.1: "There should be written evidence of all purchases (which shall include electronic evidence)."
- [rule:CPR-22] clause 7.3: "Only the Monitoring Officer and/or the S.151 Officer may grant a waiver or an exception to these Rules, subjec…"
- [metric:$.tests.high_value_suppliers.headline_general_procurement.suppliers] general-procurement suppliers at or above the quote threshold: 228
- [metric:$.tests.high_value_suppliers.headline_general_procurement.annualised_estimate] their annualised estimate (£): 110,584,320.64
- [history:AUD-08] Contract Letting: Reasonable Assurance (audit-completed-work-2024-25-annual.pdf, p.1)

**Proposed focus.** For a sample of high-value general-procurement suppliers, obtain the quotation or tender record, the Portal invitations and the contract, or an approved waiver.

**Sample source.** `analytics-full/high-value-suppliers.csv`

### R-02: Requirements split so each payment stays below the quote threshold

Several payments to one supplier within thirty days that together reach a competition threshold, while each stays below it, may indicate a requirement that was not aggregated before the procurement route was chosen [CPR-14].

- **Likelihood 4 (Almost Certain).** 64 thirty-day windows across 42 general-procurement suppliers reach £25,000. The published population omits payments below its transparency floor, so these counts are a lower bound.
- **Impact 3 (Medium).** The windows total £3,442,571.49. Disaggregation to avoid the three-quote route is a breach of a mandatory Rule with a reasonable possibility of challenge [CPR-14].
- **Score 12: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-14] clause 6.16: "There shall be no artificial splitting or disaggregation of a contract to avoid the application of the provisi…"
- [rule:CPR-56] clause App B row B1: "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including…"
- [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows] split windows in general procurement: 64
- [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.suppliers] suppliers with a split window: 42
- [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.gbp] value of those windows (£): 3,442,571.49

**Proposed focus.** For the largest general-procurement windows, obtain the orders and quotes and confirm whether the requirement was one purchase that should have followed the three-quote route.

**Sample source.** `analytics-full/split-purchases-windows.csv`

### R-06: Spend running ahead of the awarded contract value without an approved variation

Annualised spend well above the annual rate of the awarded value may indicate a variation of scope that needed prior approval [CPR-64]; award values can be estimates or maxima.

- **Likelihood 3 (Likely).** 8 of 19 checkable suppliers show spend at or above the flag ratio of the award's annual rate, a clear signal confined to a few contracts.
- **Impact 4 (Major).** The flagged suppliers account for an annualised £2,946,603.88, within the Major financial band of Table 1. Variations above the Threshold need board approval [CPR-64].
- **Score 12: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-64] clause App C row E: "For contract value below the Threshold prior written approval from the Monitoring Officer and S151 Officer is…"
- [metric:$.tests.spend_vs_award.flagged] suppliers flagged: 8
- [metric:$.tests.spend_vs_award.checked] suppliers checkable: 19
- [metric:$.tests.spend_vs_award.flagged_annualised_estimate] annualised estimate of flagged suppliers (£): 2,946,603.88

**Proposed focus.** For each flagged supplier, obtain the contract, any variation and its approval, and compare spend to date with the awarded value.

**Sample source.** `analytics-full/spend-vs-award.csv`

### R-08: Care and education placements without recorded reasons or board approval

Individually chosen care and education placements are exempt from competition only if the reasons for the choice of provider are recorded, and above the Threshold the contract must be approved by the relevant board [CPR-65] [CPR-66].

- **Likelihood 4 (Almost Certain).** Placements are the largest tag in the spend, £30,571,711.30 over the window, and 178 placement windows reach the quote threshold; recurring fees can be legitimate, so the base rating is 3. Likelihood is raised by one point for a repeat finding: Personal Budgets (Direct Payments) received Limited Assurance.
- **Impact 3 (Medium).** Placement spend is material and an exemption applied without its records has a reasonable possibility of challenge; external criticism by inspectors is the Medium reputation level of Table 1 [CPR-65].
- **Score 12: High; band Medium - High.** Recommended in scope.
- **Repeat-finding uplift:** likelihood raised by one point for an adverse opinion on the same theme (AUD-03).

**Evidence**

- [rule:CPR-65] clause App C row F: "Service Directors must ensure that a record of the reasons for the choice of provider is maintained on the ind…"
- [rule:CPR-66] clause App C closing: "In the interests of clarity where an exemption is applied all contracts with an annual or total value of more…"
- [metric:$.population.tags.care_or_education_placement.gbp] placement spend in the window (£): 30,571,711.30
- [metric:$.tests.split_purchases.per_threshold[0].placements.windows] placement windows reaching the quote threshold: 178
- [history:AUD-03] Personal Budgets (Direct Payments): Limited Assurance (audit-completed-work-2025-26-q3.pdf, p.1)
- [history:AUD-05] Purchase of Residential and Nursing Care Provision: Reasonable Assurance (audit-completed-work-2025-26-q3.pdf, p.1)

**Proposed focus.** For a sample of placement suppliers, inspect case notes for the recorded reasons for the choice of provider and, above the Threshold, the board approval.

**Sample source.** `analytics-full/split-purchases-windows.csv`

### R-04: High-value suppliers with no published contract notice

Spend at or above the quote threshold should rest on a contract notice published on the Central Digital Platform and on a contract recorded in the Council Contract Register [CPR-56] [CPR-36]. A supplier with no matching notice is an indicator to check against the register, not evidence of off-contract spend.

- **Likelihood 3 (Likely).** 185 general-procurement suppliers above the threshold have no matching notice active in the spend window. The signal is strong, but the notices file is not a register: older awards, framework call-offs and Find a Tender notices are missing from it, so many gaps can be legitimate.
- **Impact 3 (Medium).** The unmatched suppliers account for an annualised £98,484,571.20. Missing publication and register records breach the transparency Rules with a reasonable possibility of regulatory interest [CPR-08].
- **Score 9: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-56] clause App B row B1: "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including…"
- [rule:CPR-36] clause 10.4: "The relevant Service Director must formally notify the Service Lead for Commissioning and Procurement (or nomi…"
- [rule:CPR-08] clause 5.2.1: "A register of contracts, including those in progress and those awarded, with key information such as the contr…"
- [metric:$.tests.off_contract.headline_unmatched_general_procurement.suppliers] general-procurement suppliers with no matching notice: 185
- [metric:$.tests.off_contract.headline_unmatched_general_procurement.annualised_estimate] their annualised estimate (£): 98,484,571.20
- [metric:$.contracts.active_in_window] notices active in the spend window: 62

**Proposed focus.** For the largest unmatched suppliers, request the Contract Register entry and the contract or framework call-off; confirm a notice was published where the Rules require one.

**Sample source.** `analytics-full/off-contract-unmatched.csv`

### R-05: Spend after a contract notice ended without an approved extension

Payments to a supplier whose every published notice ended before the spend window may indicate a contract extended without the S151 Officer's approval [CPR-63]; a newer contract with no notice is also possible.

- **Likelihood 3 (Likely).** 7 suppliers were paid after their only matched notices ended, a clear signal confined to a few suppliers.
- **Impact 3 (Medium).** The annualised spend involved is £761,467.68. An unapproved extension breaches Appendix C row D, with a reasonable possibility of challenge [CPR-63].
- **Score 9: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-63] clause App C row D: "The proposed contract is an extension to an existing contract where the existing contract provides for such ex…"
- [rule:CPR-36] clause 10.4: "The relevant Service Director must formally notify the Service Lead for Commissioning and Procurement (or nomi…"
- [metric:$.tests.expired_notice_spend.suppliers] suppliers paid after their notices ended: 7
- [metric:$.tests.expired_notice_spend.annualised_estimate] their annualised estimate (£): 761,467.68

**Proposed focus.** For each supplier, obtain the current contract or the S151 Officer's extension approval, and the register entry.

**Sample source.** `analytics-full/expired-notice-spend.csv`

### R-07: Possible duplicate payments to the same supplier

Payments of the same amount to the same supplier within seven days, made at different times, may indicate an invoice paid twice; the Rules require written evidence of every purchase [CPR-33].

- **Likelihood 3 (Likely).** 37 general-procurement groups were paid at different times, a clear signal confined to a limited number of suppliers. The Accounts Payable audit gave Reasonable Assurance, so no uplift applies.
- **Impact 3 (Medium).** The value beyond the first payment in those groups is £297,355.44, within the Medium financial band of Table 1 [CPR-33].
- **Score 9: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-33] clause 10.1: "There should be written evidence of all purchases (which shall include electronic evidence)."
- [metric:$.tests.duplicates.per_tier.different_time.general_procurement.groups] different-time duplicate groups, general procurement: 37
- [metric:$.tests.duplicates.per_tier.different_time.general_procurement.gbp_beyond_first] value beyond the first payment (£): 297,355.44
- [history:AUD-02] Accounts Payable: Reasonable Assurance (audit-completed-work-2025-26-q3.pdf, p.1)

**Proposed focus.** For each sampled group, obtain both invoices and the purchase orders; confirm they are distinct supplies or that the second payment was recovered.

**Sample source.** `analytics-full/duplicates-groups.csv`

### R-09: Key Decision and delegated-authority approvals for awards above the Key Decision threshold

Contract awards above the Key Decision threshold need a Key Decision with a board-approved report, and the largest need Executive approval [CPR-04] [CPR-53] [CPR-54].

- **Likelihood 2 (Unlikely).** Only 3 general-procurement windows reach £500,000; the approvals themselves are not visible in the data, so the rating rests on the Rule and the gap [CPR-04].
- **Impact 4 (Major).** Awards at this level sit in the Major financial band and an award without its Key Decision has a high possibility of legal challenge [CPR-53]; the windows total £5,133,960.69.
- **Score 8: High; band Medium - High.** Recommended in scope.

**Evidence**

- [rule:CPR-04] clause 4.3: "Any contract award with a value over £500,000 is a Key Decision of the Council."
- [rule:CPR-53] clause App A row 3: "The award of these contracts shall be a Key Decision delegated to the relevant Service Director in consultatio…"
- [rule:CPR-54] clause App A row 4: "Contracts with a value in excess of £2.5million shall require Executive approval, which may be given as below."
- [metric:$.tests.split_purchases.per_threshold[1].headline_general_procurement.windows] general-procurement windows at the Key Decision threshold: 3
- [metric:$.tests.split_purchases.per_threshold[1].headline_general_procurement.gbp] their value (£): 5,133,960.69

**Proposed focus.** For suppliers whose spend reaches the Key Decision threshold, obtain the Key Decision record, the board-approved report and, where required, the Executive approval.

**Sample source.** `analytics-full/split-purchases-windows.csv`

### R-03: Payments bunched just below the quote threshold

Payments placed just below a threshold can indicate values set to avoid the next procurement route [CPR-55] [CPR-56].

- **Likelihood 2 (Unlikely).** 10 general-procurement payments fall within ten per cent below £25,000, while 52 payments sit just above it. There is no bunching below the line, so the signal is weak.
- **Impact 3 (Medium).** A value set to avoid the three-quote route breaches a mandatory Rule [CPR-56]; Medium compliance impact.
- **Score 6: Moderate; band Moderate.** Recommended in scope.

**Evidence**

- [rule:CPR-55] clause App B row A: "At least one quote must be sought from an appropriate source."
- [rule:CPR-56] clause App B row B1: "Invitations to quote must be sent via the Procurement Portal to at least three appropriate sources, including…"
- [metric:$.tests.threshold_clustering.per_threshold[1].count] payments within ten per cent below the quote threshold: 46
- [metric:$.tests.threshold_clustering.per_threshold[1].general_procurement.count] of which general procurement: 10
- [metric:$.tests.threshold_clustering.per_threshold[1].comparator_above.count] payments just above the threshold: 52

**Proposed focus.** For the general-procurement payments just below the quote threshold, confirm the order value and that no related order was raised in the same period.

**Sample source.** `analytics-full/threshold-clustering.csv`

### R-10: Grants treated outside the Rules

The Rules treat providing a grant as entering a contract, so grants need written evidence and an award record like any purchase [CPR-33] [CPR-36].

- **Likelihood 2 (Unlikely).** 339 grant payments to 198 recipients are in the window; grant awards are not visible as contracts in the data, so the rating rests on the Rule and the gap.
- **Impact 3 (Medium).** Grant spend of £6,033,599.82 treated outside the Rules has a reasonable possibility of challenge [CPR-33].
- **Score 6: Moderate; band Moderate.** Recommended out of scope.

**Evidence**

- [rule:CPR-33] clause 10.1: "There should be written evidence of all purchases (which shall include electronic evidence)."
- [rule:CPR-36] clause 10.4: "The relevant Service Director must formally notify the Service Lead for Commissioning and Procurement (or nomi…"
- [metric:$.population.tags.grant.rows] grant payments: 339
- [metric:$.population.tags.grant.gbp] grant spend (£): 6,033,599.82

**Proposed focus.** For the largest grant recipients, obtain the grant agreement and the approval, and confirm the award was recorded.

**Sample source.** `analytics-full/high-value-suppliers.csv`

## Excluded

Themes considered and not rated, and risks removed at the gate.

- Waivers and exceptions (7.3, 7.4, 7.5): no observable metric in public data; waiver approvals are tested within R-01, where a missing quote record may be explained by an approved waiver [CPR-22]
- Tender opening, evaluation and award basis (6.19-6.26): council-records only; no signal in the spend or notice data to rate likelihood
- Sealing, bonds, indemnities and insurance (11.x): legal-file controls with no signal in the data; outside a spend-led procurement audit
- Payment within thirty days (10.7.9.1): the spend Date is a payment-run timestamp, not an invoice date, so payment terms cannot be measured
- Statutory-threshold tiers: the statutory Threshold parameters are null in rules.json, so above-Threshold tiers were skipped by the spend analysis
- Clustering below the Key Decision and Executive thresholds: no payments fall in the band below those thresholds

## Auditor decisions

None recorded yet. The auditor records approve, amend or reject for each risk in `outputs/auditor-comments.md`; the risk-assessor then applies them in a revision.
