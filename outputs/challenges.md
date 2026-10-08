# Challenges to the audit planning pack

Pack versions reviewed: v1 (round one), v2 (round two), v3 (verification). Date: 2026-10-08.

I read the approved register (revision 2) and the auditor's decisions, then
compared each risk's plan in `audit-plan.json` and the rendered pack with
the evidence the register rests on: the metrics in `analytics.json`, the
audit opinions in `history.json` and the rules in `rules.json`. I looked
for samples thinner than the score calls for, controls with no test that
would show whether they worked, rules set aside for reasons that do not
hold, and register limitations the memo drops. Points about ratings the
auditor approved are recorded *for the auditor*; the planner cannot change
them. Every challenge cites its evidence. These are challenges to the plan,
never to the council.

| # | Type | Risk | Challenge | Evidence | Ask | Response | Status |
|---|---|---|---|---|---|---|---|
| 1 | sample | R-02 | The largest split windows hold many payments, but T-02.1 drew only three per window, too few to judge whether they were one requirement. | T-02.1; $.tests.split_purchases.per_threshold[0].headline_general_procurement.windows; CPR-14 | Raise per_group_n for T-02.1 so each window shows enough of its payments. | "RESPONSE #1: accepted. per_group_n raised from 3 to 5; rebuilt as v2." | resolved |
| 2 | sample | R-07 | T-07.1 samples general procurement only, yet most duplicate value beyond the first payment sits in placements. | $.tests.duplicates.per_tier.different_time.placements.gbp_beyond_first; $.tests.duplicates.per_tier.different_time.general_procurement.gbp_beyond_first; C-07.1 | Add a placement duplicate test under C-07.1. | "RESPONSE #2: accepted. Added T-07.2: ten different-time placement groups, largest value beyond the first payment first; rebuilt as v2." | resolved |
| 3 | coverage | R-01 | CPR-10 (supplier suitability before award) is set aside as not linked to payments, but the R-01 sample already pulls the contract file where that check would sit. | CPR-10; T-01.1 | Cite CPR-10 in T-01.1 and add the suitability check to its step. | "RESPONSE #3: accepted. T-01.1 now cites CPR-10 and checks supplier due diligence; CPR-10 removed from rules_not_tested; rebuilt as v2." | resolved |
| 4 | control | R-04 | T-04.1 excludes suppliers already drawn in T-01.1, so the largest unmatched suppliers get no register check under C-04.2. | C-04.2; T-04.2; T-01.1; $.tests.off_contract.headline_unmatched_general_procurement.suppliers | Extend T-04.2 to the T-01.1 suppliers with no matching notice. | "RESPONSE #4: accepted. T-04.2 now covers T-04.1 suppliers and T-01.1 suppliers with no matching notice; rebuilt as v2." | resolved |
| 5 | test | R-09 | T-09.1 samples thirty-day windows rather than contracts, so it may miss contracts above the Key Decision threshold whose spend is spread evenly. | T-09.1; T-09.2; CPR-04; $.tests.split_purchases.per_threshold[1].headline_general_procurement.windows | Sample suppliers by annualised spend at the Key Decision threshold instead. | "RESPONSE #5: declined. A window reaching the threshold in thirty days is the strongest signal of an award at that level; T-09.2 already samples suppliers by annualised spend at the Executive threshold, and T-09.3 tests authority for both." | declined |
| 6 | rating | R-04 | Likelihood 3 sits beside a strong signal: a large number of general-procurement suppliers above the threshold have no active notice. | $.tests.off_contract.headline_unmatched_general_procurement.suppliers; $.tests.off_contract.headline_unmatched_general_procurement.annualised_estimate; CPR-56 | Auditor to confirm likelihood 3 given the caveat that notices are not a register. | "RESPONSE #6: for the auditor. The rating was approved at the gate; the plan is unchanged." | for the auditor |
| 7 | sample | R-08 | R-08 scores 12, but T-08.2 drew five providers; the skill sizes samples at ten items for scores of nine and above. | T-08.2; $.population.tags.care_or_education_placement.gbp; CPR-66 | Raise T-08.2 to ten providers. | "RESPONSE #7: accepted. n raised to 10; rebuilt as v3." | resolved |
| 8 | coverage | R-01 | The register's limitation that redacted payees are excluded from supplier-level tests is not carried into the memo. | $.population.excluded.redacted_supplier.rows; T-01.1 | Add the limitation to the memo. | "RESPONSE #8: accepted. Limitation added with its figure as a placeholder; rebuilt as v3." | resolved |

Round one: challenges 1 to 6, sent on PACK READY v1. Round two: challenges
7 and 8, sent on PACK READY v2. Every accepted change was checked in the
rebuilt pack: T-02.1 shows five payments per window, T-07.2 and its PBC
line appear in `audit-program.md`, T-01.1 cites CPR-10, T-04.2 names the
T-01.1 suppliers, T-08.2 lists ten providers, and the memo's limitations
include the redacted-payee line. The reason given for declining #5 holds.

## For the auditor at sign-off

- #6 (rating, R-04): likelihood 3 against a strong unmatched-supplier signal; confirm the rating given that notices are not a contract register.
