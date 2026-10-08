#!/usr/bin/env python3
"""Re-derive one flagged item per test independently from spend-clean.csv.

Uses plain csv (not the pandas code paths in analyse.py), so a bug there is
not repeated here. Prints only the checks and the row_ids used. Exit 0 when
every check matches.
"""
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FULL = ROOT / "outputs/analytics-full"
A = json.loads((ROOT / "outputs/analytics.json").read_text())


def rows(name):
    with open(FULL / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


spend = rows("spend-clean.csv")
by_sup = {}
for r in spend:
    by_sup.setdefault(r["supplier_norm"], []).append(r)
D = lambda s: date.fromisoformat(s)
fails = []


def check(name, ok, detail):
    print(f"{'OK  ' if ok else 'FAIL'} {name}: {detail}")
    if not ok:
        fails.append(name)


# 1. threshold clustering: count in [0.9T, T) for the £25,000 tier
tc = next(t for t in A["tests"]["threshold_clustering"]["per_threshold"] if t["count"] and t["threshold"] >= 25000)
T = tc["threshold"]
n = sum(1 for r in spend if 0.9 * T <= float(r["Net amount"]) < T)
check("threshold_clustering", n == tc["count"], f"T={T} recount {n} vs analytics {tc['count']}; e.g. {tc['top20'][0]['row_id']}")

# 2. split purchases: re-sum the top general-procurement window
sp = next(t for t in A["tests"]["split_purchases"]["per_threshold"] if t["threshold"] == T)
w = next(x for x in sp["top20"] if x["dominant_tag"] == "general_procurement")
ids = w["row_ids"].split(";")
sel = [r for r in spend if r["row_id"] in ids]
tot = round(sum(float(r["Net amount"]) for r in sel), 2)
span = (max(D(r["pay_date"]) for r in sel) - min(D(r["pay_date"]) for r in sel)).days
ok = len(sel) == len(ids) and abs(tot - w["window_total"]) < 0.01 and span <= 29 and all(float(r["Net amount"]) < T for r in sel) and tot >= T
check("split_purchases", ok, f"{w['window_id']} total {tot} vs {w['window_total']}, {len(sel)} payments over {span} days; rows {ids[:3]}")

# 3. high-value suppliers: re-sum the top general-procurement supplier
hv = A["tests"]["high_value_suppliers"]["top20_general_procurement"][0]
hvrow = next(r for r in rows("high-value-suppliers.csv") if r["supplier"] == hv["supplier"])
s = by_sup[hvrow["supplier_norm"]]
tot = round(sum(float(r["Net amount"]) for r in s), 2)
ann = round(tot * A["population"]["annualisation_factor"], 2)
check("high_value_suppliers", abs(ann - hv["annualised_estimate"]) < 0.01, f"annualised {ann} vs {hv['annualised_estimate']} over {len(s)} payments; e.g. {s[0]['row_id']}")

# 4. off_contract: the top unmatched general-procurement supplier has no exact name on an active notice
oc = A["tests"]["off_contract"]
if not oc.get("skipped"):
    notices = rows("notices-clean.csv")
    active = {r["supplier_norm"] for r in notices if r["active"] == "True"}
    top = oc["top20_unmatched_general_procurement"][0]
    norm = next(r["supplier_norm"] for r in rows("high-value-suppliers.csv") if r["supplier"] == top["supplier"])
    check("off_contract", norm not in active, f"top unmatched supplier absent from {len(active)} active notice suppliers")

# 5. duplicates: the top different-time group has equal amounts within 7 days
dg = A["tests"]["duplicates"]["top20_different_time"][0]
ids = dg["row_ids"].split(";")
sel = [r for r in spend if r["row_id"] in ids]
amts = {r["Net amount"] for r in sel}
span = (max(D(r["pay_date"]) for r in sel) - min(D(r["pay_date"]) for r in sel)).days
sups = {r["supplier_norm"] for r in sel}
check("duplicates", len(amts) == 1 and len(sups) == 1 and span <= 7 and len(sel) == dg["n"], f"{dg['group_id']}: {len(sel)} rows, one amount, {span} days apart; rows {ids}")

# 6. expired notice spend: the supplier's latest matched notice ended before the window
ex = A["tests"]["expired_notice_spend"]
if not ex.get("skipped") and ex["top20"]:
    e = ex["top20"][0]
    check("expired_notice_spend", D(e["latest_end_date"]) < D(A["population"]["date_min"]),
          f"latest end {e['latest_end_date']} before window start {A['population']['date_min']}")

# 7. spend vs award: recompute the top ratio
sv = A["tests"]["spend_vs_award"]
if not sv.get("skipped") and sv["top20"]:
    t = sv["top20"][0]
    r = round(t["annualised_estimate"] / t["award_annual_rate"], 2)
    check("spend_vs_award", abs(r - t["ratio"]) < 0.01 and r >= 1.25, f"ratio {r} vs {t['ratio']}")

print(f"\nselfcheck: {7 - len(fails)} matched, {len(fails)} failed")
sys.exit(1 if fails else 0)
