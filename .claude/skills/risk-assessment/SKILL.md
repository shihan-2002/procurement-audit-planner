---
name: risk-assessment
description: Merge outputs/rules.json, outputs/analytics.json and outputs/history.json into outputs/risk-register.md: risks rated likelihood × impact on the council's own scale, every rating cited to a rule, a named metric or a history item, rendered and validated by build_register.py. Use when building the risk register after both analysts have finished, or when applying the auditor's decisions from outputs/auditor-comments.md as a revision. Loaded by the risk-assessor sub-agent.
---

# risk-assessment

Produce the risk register a human auditor will approve, amend or reject.
You judge which risks exist and how likely and how severe each is; Python
resolves every citation, fills every figure, computes every score and
writes the register. Write your judgments to `outputs/risk-ratings.json`,
then let `build_register.py` render `outputs/risk-register.md` and the
decision template `outputs/auditor-comments.md`. A rating the script cannot
trace is excluded, by design.

## Inputs and outputs

| | Path |
| --- | --- |
| Rules | `outputs/rules.json` (rule IDs, clauses, verbatim quotes) |
| Analytics | `outputs/analytics.json` (named metrics; scalar paths only) |
| History | `outputs/history.json` (audit opinions `AUD-nn`, risk themes `RT-nn`, discrepancies `D-nn`, `scoring_method`) |
| Your judgments | `outputs/risk-ratings.json` (you write this) |
| Builder | `.claude/skills/risk-assessment/build_register.py` (run with `.venv/bin/python`) |
| Register | `outputs/risk-register.md` (builder writes) |
| Decision template | `outputs/auditor-comments.md` (builder writes; the auditor fills it in; never edit it yourself) |

Stop and report if any input is missing.

## Non-negotiable rules

1. **Every justification cites.** Each likelihood and each impact
   justification carries at least one tag: `[rule:CPR-14]`,
   `[metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows]`,
   `[history:AUD-03]` or `[history:$.scoring_method.impact_scale[1]]`.
   Metric paths must point at a scalar. No citation, or a broken one, and
   the builder excludes the risk.
2. **You type no figures.** Every number from the data in prose is a
   `{{$.path}}` placeholder resolved from analytics.json. A literal figure
   (three or more digits, a £ amount or a percentage) is a WARN; treat it as
   a failure. Scores are the only digits you write.
3. **The council's scale.** Likelihood 1–5 and impact 1–5 as defined in
   `history.json.scoring_method` (Table 2 and Table 1 of the Risk
   Management Strategy). The builder applies Figure 1's matrix label and
   Table 4's band. If `scoring_method.usable` is false, the builder falls
   back to 1–5 Very low…Very high and says so in the header.
4. **Conflicts are marked, not resolved.** The strategy's Table 4 and
   Figure 4 disagree on when a risk enters the Corporate Risk Register
   (`D-01`). The register uses Table 4 bands and the builder notes the
   Figure 4 rule. Do not choose silently between conflicting thresholds.
5. **Repeat findings raise likelihood by one point,** stated explicitly:
   add `"uplift": {"history": "AUD-nn", "reason": "..."}` and cite the
   same item in the likelihood justification. The builder rejects an
   uplift whose audit has no adverse opinion (Limited, Weak,
   Unsatisfactory).
6. **Indicator language.** Risks describe patterns to investigate and
   controls to test. No supplier, officer or department is characterised.
   Supplier names never appear in statements or justifications (the
   builder warns if one does).

## Theme table

Work through these themes in order. Each becomes a risk or an `excluded`
entry with a one-line reason.

| Theme | Rules to cite | Metrics | History | Sample source |
| --- | --- | --- | --- | --- |
| Quotes or tenders not evidenced for spend at or above the quote threshold | App B rows B1/B2/C, 10.1, 7.3 | `high_value_suppliers.headline_general_procurement.*` | Contract Letting (AUD) | `high-value-suppliers.csv` |
| Requirements split to stay below a threshold | 6.16, App B row B1 | `split_purchases.per_threshold[n].headline_general_procurement.*` | — | `split-purchases-windows.csv` |
| Payments bunched just below a threshold | App B rows A/B1 | `threshold_clustering.per_threshold[n].*` incl. `comparator_above` | — | `threshold-clustering.csv` |
| High-value suppliers with no published notice | App B row B1 (CDP notice), 10.4, 5.2.1 | `off_contract.headline_unmatched_general_procurement.*` | — | `off-contract-unmatched.csv` |
| Spend after a notice ended without an approved extension | App C row D | `expired_notice_spend.*` | — | `expired-notice-spend.csv` |
| Spend beyond the award without an approved variation | App C row E | `spend_vs_award.*` | — | `spend-vs-award.csv` |
| Duplicate payments | 10.1 | `duplicates.per_tier.different_time.*` | Accounts Payable (AUD) | `duplicates-groups.csv` |
| Placements chosen without recorded reasons or board approval | App C row F, App C closing | `split_purchases.per_threshold[n].placements.*`, `population.tags.care_or_education_placement.*` | Personal Budgets, Purchase of Residential Care (AUD) | `split-purchases-windows.csv` |
| Awards above the Key Decision threshold without the required approvals | 4.3, App A rows 3–4 | `split_purchases.per_threshold[1].*` | — | `split-purchases-windows.csv` |
| Grants treated outside the Rules | 10.1, 10.4 (grant = contract under 1.6.2, excluded as a definition) | `population.tags.grant.*` | — | `high-value-suppliers.csv` |
| Waivers and exceptions | 7.3, 7.4.x, 7.5.x | none observable | — | — |
| Tender opening, evaluation, sealing, bonds, insurance, social value | 6.19–6.26, 11.x, 3.5 | none observable | — | — |

## Likelihood rubric

Use the first row that fits, so two runs rate the same evidence the same
way. "Signal" means a named metric in analytics.json.

| Score | Label | When |
| --- | --- | --- |
| 5 | Certain | A strong signal in general procurement **and** an adverse audit opinion on the same theme. |
| 4 | Almost Certain | A strong signal in general procurement: the pattern recurs across many suppliers, or the flagged value is material against the general-procurement population. |
| 3 | Likely | A clear signal confined to a few suppliers or transactions, or a strong signal only in tags where the pattern can be legitimate (placements, grants). |
| 2 | Unlikely | A weak or absent signal, but the control is mandatory and the data cannot see it (approvals, waivers, records). |
| 1 | Rare | No signal and a recent Substantial or Reasonable opinion covering the control. |

Then apply the repeat-finding uplift (+1, capped at 5) where rule 5 applies.

## Impact method

Rate impact against Table 1 of the strategy, citing the scale entry
(`[history:$.scoring_method.impact_scale[k]]`) and the metric for the
money at stake. Financial: compare the annualised value exposed with the
Table 1 bands (`gbp_low` / `gbp_high`). Compliance: a breach of a
mandatory Rule with legal challenge possible is at least 3. Take the
higher of the two and say which column drove it.

## Procedure

### Step 1: Read the inputs

Read `rules.json`, `analytics.json` and `history.json` in full (they are
summaries). If `auditor-comments.md` exists, read it first: see Step 4.

### Step 2: Rate each theme

For each theme in the table: decide whether the evidence supports a risk.
If it does, write a risk entry; if not, an `excluded` entry with the reason.

### Step 3: Write `outputs/risk-ratings.json`

```json
{
  "generated_at": "YYYY-MM-DD",
  "risks": [
    {
      "id": "R-02",
      "theme": "split_purchases",
      "title": "Requirements split to stay below the quote threshold",
      "statement": "Payments to one supplier within thirty days that together reach a competition threshold may indicate a requirement that was not aggregated before the route was chosen [rule:CPR-14].",
      "likelihood": {"score": 4, "justification": "{{$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows}} windows in general procurement [metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows] ..."},
      "impact": {"score": 3, "justification": "... [history:$.scoring_method.impact_scale[2]] [rule:CPR-56]"},
      "evidence": ["[rule:CPR-14]", "[metric:$.tests.split_purchases.per_threshold[0].headline_general_procurement.windows] split windows, general procurement"],
      "proposed_focus": "What fieldwork should test.",
      "sample_source": "split-purchases-windows.csv",
      "recommend_in_scope": true
    }
  ],
  "excluded": [
    {"theme": "Waivers and exceptions", "reason": "no observable metric; ..."}
  ]
}
```

IDs are `R-01`, `R-02`… in theme-table order and stay stable across
revisions. `recommend_in_scope` is a recommendation; the auditor decides.

### Step 4: Revision after the auditor gate

When `auditor-comments.md` holds decisions:

- **approve**: keep the risk exactly as rated.
- **amend**: apply the change asked for. If it sets a score the evidence
  alone would not support, keep the auditor's score, add
  `"auditor_override": true`, quote the comment in the justification, and
  keep at least one real citation (the comments file is not citable).
- **reject**: remove the risk from `risks` and add it to `excluded` with
  its `id` and the auditor's reason.
- Add a top-level block, cumulative across revisions:
  `"revision": {"number": N, "changed": [{"id": "R-09", "change": "amended"}, {"id": "R-10", "change": "rejected"}]}`.
  N is one more than the last revision built.

The builder fails if a decision is unapplied, if anything changed that the
auditor did not ask for, or if the revision number is wrong. It writes the
revision header and the closing "Auditor decisions" section itself; never
edit the register by hand.

### Step 5: Build and validate

```bash
.venv/bin/python .claude/skills/risk-assessment/build_register.py
```

Fix every FAIL and every WARN by correcting citations or placeholders, or
by removing the risk, never by inventing a citation. Re-run until it
reports `failures: 0` and `warnings: 0`.

### Step 6: Report

Under 400 words: risks by band, the top three with their scores, the
excluded themes, any risk the builder excluded and why, the scale used and
the conflict noted, and the explicit request for the auditor to record a
decision for every risk in `outputs/auditor-comments.md`.

## Not this skill's job

- Computing metrics or reading `data/`; the analysts did that.
- Planning tests or samples; the audit-program skill does that.
- Approving scope; the auditor decides at the gate.
