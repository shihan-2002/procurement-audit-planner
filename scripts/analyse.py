#!/usr/bin/env python3
"""Run the spend tests and write outputs/analytics.json plus full lists in analytics-full/.

Reads analytics-full/spend-clean.csv, notices-clean.csv and cleaning-log.json
(from clean.py) and outputs/rules.json. Every threshold comes from rules.json.
Prints aggregates only. Indicator language: every list is a set of patterns to
investigate, never a finding.
"""
import difflib
import json
from collections import Counter
from datetime import datetime

import pandas as pd

from common import (FULL, OUT, TAG_ORDER, CAVEAT_NOTICES, load_rules, derive_thresholds,
                    null_parameters, distinctive, money)

BAND = 0.10          # clustering band: [0.9T, T)
WINDOW_DAYS = 30     # split-purchase window
DUP_DAYS = 7         # duplicate window
RATIO_FLAG = 1.25    # spend_vs_award flag
NEAR_RATIO = 0.85    # near-match SequenceMatcher threshold
TOP = 20


def below(amount, t):
    """amount is below threshold t (t starts its obligation; inclusive means >= t triggers)."""
    return amount < t["value"] if t["inclusive"] else amount <= t["value"]


def records(df, cols, n=TOP):
    out = []
    for r in df.head(n)[cols].to_dict("records"):
        out.append({k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()})
    return out


def by_tag(df, amount_col="Net amount", count_name="rows"):
    out = {}
    for t in TAG_ORDER:
        g = df[df["tag"] == t] if "tag" in df.columns else df.iloc[0:0]
        out[t] = {count_name: int(len(g)), "gbp": money(g[amount_col].sum()) if len(g) else 0.0}
    return out


# ------------------------------------------------------------------ tests

def threshold_clustering(spend, thresholds):
    per, rows_all = [], []
    for t in thresholds:
        T = t["value"]
        lo = (1 - BAND) * T
        band = spend[(spend["Net amount"] >= lo) & spend["Net amount"].map(lambda a: below(a, t))]
        comp = spend[~spend["Net amount"].map(lambda a: below(a, t)) & (spend["Net amount"] < (1 + BAND) * T)]
        base = spend[(spend["Net amount"] >= 0.5 * T) & (spend["Net amount"] < 1.5 * T)]
        sup = band.groupby("Supplier name").agg(n=("row_id", "size"), gbp=("Net amount", "sum")).sort_values(["n", "gbp"], ascending=False)
        b = band.sort_values("Net amount", ascending=False).copy()
        b["threshold"] = T
        rows_all.append(b)
        gp = band[band["tag"] == "general_procurement"]
        per.append({
            "threshold": T, "inclusive": t["inclusive"], "rule_ids": t["rule_ids"],
            "band_low": money(lo), "band_high": T,
            "count": int(len(band)), "gbp": money(band["Net amount"].sum()),
            "general_procurement": {"count": int(len(gp)), "gbp": money(gp["Net amount"].sum())},
            "comparator_above": {"count": int(len(comp)), "gbp": money(comp["Net amount"].sum()),
                                 "description": "payments from T up to 1.1 x T"},
            "baseline": {"count": int(len(base)), "description": "payments from 0.5 x T up to 1.5 x T"},
            "by_tag": by_tag(band, count_name="count"),
            "top_suppliers": [{"supplier": k, "count": int(v["n"]), "gbp": money(v["gbp"])} for k, v in sup.head(TOP).iterrows()],
            "top20": records(b, ["row_id", "pay_date", "Supplier name", "Net amount", "Service", "Narrative", "tag"]),
        })
    full = pd.concat(rows_all) if rows_all else spend.iloc[0:0]
    cols = ["threshold", "row_id", "source_file", "sheet_row", "pay_date", "Supplier name", "supplier_norm",
            "Net amount", "Service", "Narrative", "tag"]
    full[cols].to_csv(FULL / "threshold-clustering.csv", index=False)
    return {
        "description": f"payments within {int(BAND * 100)}% below each threshold from rules.json",
        "parameters": {"band": f"[{1 - BAND:.1f} x T, T)", "thresholds": [t["value"] for t in thresholds]},
        "rule_ids": sorted({r for t in thresholds for r in t["rule_ids"]}),
        "per_threshold": per, "full_list": "analytics-full/threshold-clustering.csv",
    }


def dominant_tag(rows):
    s = rows.groupby("tag")["Net amount"].sum()
    return s.idxmax() if len(s) else ""


def split_purchases(spend, comp_thresholds, anti_ids):
    per, all_windows = [], []
    wid = 0
    for t in comp_thresholds:
        T = t["value"]
        cands = []
        sub = spend[spend["Net amount"].map(lambda a: below(a, t))].copy()
        sub["d"] = pd.to_datetime(sub["pay_date"])
        for sup, g in sub.groupby("supplier_norm"):
            if len(g) < 2:
                continue
            g = g.sort_values(["d", "row_id"])
            ds, amts, ids = list(g["d"]), list(g["Net amount"]), list(g["row_id"])
            for i in range(len(g)):
                end = ds[i] + pd.Timedelta(days=WINDOW_DAYS - 1)
                j = i
                while j + 1 < len(g) and ds[j + 1] <= end:
                    j += 1
                if j > i:
                    total = sum(amts[i:j + 1])
                    if (total >= T) if t["inclusive"] else (total > T):
                        cands.append((round(total, 2), sup, i, j, ids[i:j + 1]))
        # de-duplicate overlapping windows: keep the highest total, drop windows sharing a payment with it
        cands.sort(key=lambda c: (-c[0], c[1], c[2]))
        used, kept = set(), []
        for total, sup, i, j, ids in cands:
            if used.intersection(ids):
                continue
            used.update(ids)
            kept.append((total, sup, ids))
        idx = spend.set_index("row_id")
        wins = []
        for total, sup, ids in kept:
            rows = idx.loc[ids].reset_index()
            wid += 1
            wins.append({
                "window_id": f"W{wid:04d}", "threshold": T, "supplier_norm": sup,
                "supplier": rows["Supplier name"].mode().iloc[0],
                "window_start": min(rows["pay_date"]), "window_end": max(rows["pay_date"]),
                "n_payments": len(rows), "distinct_amounts": int(rows["Net amount"].nunique()),
                "window_total": round(total, 2), "dominant_tag": dominant_tag(rows),
                "services": "; ".join(sorted(rows["Service"].astype(str).unique())),
                "row_ids": ";".join(ids),
            })
        w = pd.DataFrame(wins)
        all_windows.append(w)
        def summ(df):
            return {"windows": int(len(df)), "suppliers": int(df["supplier_norm"].nunique()) if len(df) else 0,
                    "gbp": money(df["window_total"].sum()) if len(df) else 0.0}
        per.append({
            "threshold": T, "rule_ids": t["rule_ids"], **summ(w),
            "headline_general_procurement": summ(w[w["dominant_tag"] == "general_procurement"]) if len(w) else summ(w),
            "placements": summ(w[w["dominant_tag"] == "care_or_education_placement"]) if len(w) else summ(w),
            "by_tag": {tg: summ(w[w["dominant_tag"] == tg]) if len(w) else summ(w) for tg in TAG_ORDER},
            "top20": records(w.sort_values("window_total", ascending=False) if len(w) else w,
                             ["window_id", "supplier", "window_start", "window_end", "n_payments", "distinct_amounts",
                              "window_total", "dominant_tag", "row_ids"]) if len(w) else [],
        })
    full = pd.concat(all_windows) if all_windows else pd.DataFrame()
    full.to_csv(FULL / "split-purchases-windows.csv", index=False)
    return {
        "description": f"two or more payments to one supplier within {WINDOW_DAYS} calendar days, each below a competition-triggering threshold, together reaching it",
        "parameters": {"window_days": WINDOW_DAYS, "min_payments": 2,
                       "thresholds": [t["value"] for t in comp_thresholds],
                       "dedup": "overlapping windows de-duplicated, keeping the highest total"},
        "rule_ids": sorted(set(anti_ids) | {r for t in comp_thresholds for r in t["rule_ids"]}),
        "caveat": "population is payments over £500 only, so counts are lower bounds; periodic care fees recur by design and are reported separately",
        "per_threshold": per, "full_list": "analytics-full/split-purchases-windows.csv",
    }


def match_suppliers(spend_sups, notice_sups):
    """spend_sups: list of normalised names; notice_sups: list of normalised names. -> {spend: (class, candidate, rule)}"""
    nset = set(notice_sups)
    s_tokens = {s: distinctive(s) for s in spend_sups}
    n_tokens = {n: distinctive(n) for n in nset}
    s_freq = Counter(tok for toks in s_tokens.values() for tok in toks)
    n_freq = Counter(tok for toks in n_tokens.values() for tok in toks)
    out = {}
    for s in spend_sups:
        if s in nset:
            out[s] = ("exact", s, "normalised name equal"); continue
        best = max(((difflib.SequenceMatcher(None, s, n).ratio(), n) for n in nset), default=(0, ""))
        if best[0] >= NEAR_RATIO:
            out[s] = ("near_ratio", best[1], f"ratio {best[0]:.2f}"); continue
        hit = None
        st = s_tokens[s]
        for n in sorted(nset):
            nt = n_tokens[n]
            if not st or not nt:
                continue
            small, large = (st, nt) if len(st) <= len(nt) else (nt, st)
            if small <= large:
                if len(small) >= 2:
                    hit = (n, f"tokens {sorted(small)} contained"); break
                tok = next(iter(small))
                if s_freq[tok] == 1 and n_freq[tok] == 1:
                    hit = (n, f"unique token {tok} contained"); break
        out[s] = ("near_contain", hit[0], hit[1]) if hit else ("none", "", "")
    return out


def rid(rules, clause):
    """rule_id(s) for a clause as printed in rules.json (never typed by hand)."""
    ids = [r["rule_id"] for r in rules["rules"] if r["clause"] == clause]
    if not ids:
        raise SystemExit(f"STOP: no rule for clause {clause} in rules.json")
    return ids


def main():
    rules = load_rules()
    RID = {k: rid(rules, k) for k in ("6.16", "10.1", "10.4", "5.2.1", "App C row D", "App C row E")}
    thresholds = derive_thresholds(rules)
    comp = [t for t in thresholds if t["competition_triggering"]]
    nulls = null_parameters(rules)
    log = json.loads((FULL / "cleaning-log.json").read_text())
    spend = pd.read_csv(FULL / "spend-clean.csv", dtype={"row_id": str, "sheet_row": int})
    months = log["months_covered"]
    factor = 12 / months
    contracts_present = (FULL / "notices-clean.csv").exists() and log["contracts"].get("contracts_present", False)
    register_present = log["register_present"]
    notices = pd.read_csv(FULL / "notices-clean.csv") if contracts_present else None

    skipped = []
    for p in nulls:
        skipped.append({"test": "all threshold tests", "tier": p, "reason": f"{p} is null in rules.json; statutory tier not tested"})

    tests = {}
    tests["threshold_clustering"] = threshold_clustering(spend, thresholds)
    tests["split_purchases"] = split_purchases(spend, comp, RID["6.16"])

    # ---- high-value suppliers
    T_low = min(comp, key=lambda t: t["value"])
    g = spend.groupby("supplier_norm")
    sup = pd.DataFrame({
        "supplier": g["Supplier name"].agg(lambda s: s.mode().iloc[0]),
        "total_gbp": g["Net amount"].sum().round(2),
        "n_payments": g.size(),
        "top_narrative": g["Narrative"].agg(lambda s: s.mode().iloc[0]),
        "top_service": g["Service"].agg(lambda s: s.mode().iloc[0]),
        "n_tags": g["tag"].nunique(),
    })
    sup["annualised_estimate"] = (sup["total_gbp"] * factor).round(2)
    dom = spend.groupby(["supplier_norm", "tag"])["Net amount"].sum().reset_index().sort_values("Net amount", ascending=False).drop_duplicates("supplier_norm").set_index("supplier_norm")["tag"]
    sup["dominant_tag"] = dom
    sup["spans_tags"] = sup["n_tags"] > 1
    hv = sup[sup["annualised_estimate"] >= T_low["value"]].copy().sort_values("annualised_estimate", ascending=False)

    # ---- matching (only with notices or a register)
    matching = {"exact": 0, "near_ratio": 0, "near_contain": 0, "none": 0}
    if contracts_present:
        active = notices[notices["active"] == True]
        m = match_suppliers(list(sup.index), list(active["supplier_norm"].dropna().unique()))
        sup["match_class"] = [m[s][0] for s in sup.index]
        sup["match_candidate"] = [m[s][1] for s in sup.index]
        sup["match_rule"] = [m[s][2] for s in sup.index]
        hv = hv.join(sup[["match_class", "match_candidate", "match_rule"]])
        mt = sup[["supplier", "match_class", "match_candidate", "match_rule", "annualised_estimate", "dominant_tag"]]
        mt.to_csv(FULL / "supplier-match.csv")
        mt[mt["match_class"].isin(["near_ratio", "near_contain"])].to_csv(FULL / "near-matches.csv")
        matching = {k: int((sup["match_class"] == k).sum()) for k in matching}
        matching["near_matches_file"] = "analytics-full/near-matches.csv"
        matching["scope"] = "every spend supplier against suppliers on notices active in the spend window"
    hv_out = hv.reset_index().rename(columns={"index": "supplier_norm"})
    hv_out.to_csv(FULL / "high-value-suppliers.csv", index=False)

    def hv_summary(df):
        return {"suppliers": int(len(df)), "gbp_3_month": money(df["total_gbp"].sum()),
                "annualised_estimate": money(df["annualised_estimate"].sum())}
    hv_gp = hv_out[hv_out["dominant_tag"] == "general_procurement"]
    tests["high_value_suppliers"] = {
        "description": "suppliers whose annualised estimate reaches the lowest competition-triggering threshold: the population for which contract evidence is requested in fieldwork",
        "parameters": {"threshold": T_low["value"], "annualisation_factor": factor, "basis": "annualised estimate = 3-month total x 12 / months covered"},
        "rule_ids": T_low["rule_ids"],
        **hv_summary(hv_out),
        "headline_general_procurement": hv_summary(hv_gp),
        "by_dominant_tag": {t: hv_summary(hv_out[hv_out["dominant_tag"] == t]) for t in TAG_ORDER},
        "spanning_several_tags": int(hv_out["spans_tags"].sum()),
        "top20_general_procurement": records(hv_gp, ["supplier", "annualised_estimate", "total_gbp", "n_payments", "top_narrative", "top_service"]),
        "full_list": "analytics-full/high-value-suppliers.csv",
    }
    if any(p for p in nulls if "GOODS" in p):
        skipped.append({"test": "high_value_suppliers", "tier": "statutory", "reason": "STATUTORY_THRESHOLD_GOODS_SERVICES is null"})

    # ---- off_contract
    if contracts_present or register_present:
        cls = {}
        for c in ("exact", "near_ratio", "near_contain", "none"):
            d = hv_out[hv_out["match_class"] == c]
            cls[c] = hv_summary(d)
        un = hv_out[hv_out["match_class"] == "none"]
        un_gp = un[un["dominant_tag"] == "general_procurement"]
        un.to_csv(FULL / "off-contract-unmatched.csv", index=False)
        tests["off_contract"] = {
            "description": "high-value suppliers (annualised estimate at or above the publication threshold) with no matching notice active in the spend window",
            "parameters": {"threshold": T_low["value"], "match_rules": ["exact normalised name", f"near_ratio >= {NEAR_RATIO}", "near_contain distinctive tokens"],
                           "near_matches_counted_as_matches": False},
            "rule_ids": sorted(set(T_low["rule_ids"]) | set(RID["10.4"]) | set(RID["5.2.1"])),
            "contracts_present": contracts_present, "register_present": register_present,
            "caveat": CAVEAT_NOTICES,
            "by_match_class": cls,
            "unmatched": hv_summary(un),
            "unmatched_by_tag": {t: hv_summary(un[un["dominant_tag"] == t]) for t in TAG_ORDER},
            "headline_unmatched_general_procurement": hv_summary(un_gp),
            "top20_unmatched_general_procurement": records(un_gp, ["supplier", "annualised_estimate", "n_payments", "top_narrative", "top_service"]),
            "full_list": "analytics-full/off-contract-unmatched.csv",
        }
    else:
        tests["off_contract"] = {"skipped": True, "reason": "no contracts.csv or contract register in data/"}
        skipped.append({"test": "off_contract", "tier": "all", "reason": "no contracts.csv or contract register in data/"})

    # ---- duplicates
    groups, grows = [], []
    gid = 0
    s2 = spend.copy()
    s2["d"] = pd.to_datetime(s2["pay_date"])
    for (sn, amt), g in s2.groupby(["supplier_norm", "Net amount"]):
        if len(g) < 2:
            continue
        g = g.sort_values(["d", "row_id"])
        cur = []
        def flush(cur):
            nonlocal gid
            if len(cur) < 2:
                return
            gid += 1
            rows = pd.DataFrame(cur)
            tier = "same_timestamp" if rows["Date"].nunique() == 1 else "different_time"
            groups.append({"group_id": f"D{gid:04d}", "tier": tier, "supplier_norm": sn,
                           "supplier": rows["Supplier name"].iloc[0], "amount": round(amt, 2), "n": len(rows),
                           "first_date": rows["pay_date"].min(), "last_date": rows["pay_date"].max(),
                           "extra_gbp": round(amt * (len(rows) - 1), 2), "dominant_tag": dominant_tag(rows),
                           "row_ids": ";".join(rows["row_id"])})
            for _, r in rows.iterrows():
                grows.append({"group_id": f"D{gid:04d}", "tier": tier, **{k: r[k] for k in ["row_id", "source_file", "sheet_row", "pay_date", "Date", "Supplier name", "supplier_norm", "Net amount", "Service", "Narrative", "tag"]}})
        for _, r in g.iterrows():
            if cur and (r["d"] - cur[0]["d"]).days > DUP_DAYS:
                flush(cur); cur = []
            cur.append(r)
        flush(cur)
    dg = pd.DataFrame(groups)
    dg.to_csv(FULL / "duplicates-groups.csv", index=False)
    pd.DataFrame(grows).to_csv(FULL / "duplicates-rows.csv", index=False)
    def dsum(df):
        return {"groups": int(len(df)), "rows": int(df["n"].sum()) if len(df) else 0,
                "gbp_beyond_first": money(df["extra_gbp"].sum()) if len(df) else 0.0}
    tests["duplicates"] = {
        "description": f"same supplier, same amount to the penny, calendar dates within {DUP_DAYS} days",
        "parameters": {"window_days": DUP_DAYS, "match": "normalised supplier and exact amount"},
        "rule_ids": RID["10.1"],
        **dsum(dg),
        "per_tier": {t: {**dsum(dg[dg["tier"] == t]),
                         "general_procurement": dsum(dg[(dg["tier"] == t) & (dg["dominant_tag"] == "general_procurement")]),
                         "placements": dsum(dg[(dg["tier"] == t) & (dg["dominant_tag"] == "care_or_education_placement")])}
                     for t in ("same_timestamp", "different_time")},
        "by_tag": {t: dsum(dg[dg["dominant_tag"] == t]) for t in TAG_ORDER},
        "top20_different_time": records(dg[dg["tier"] == "different_time"].sort_values("amount", ascending=False),
                                        ["group_id", "supplier", "amount", "n", "first_date", "last_date", "dominant_tag", "row_ids"]),
        "full_list": "analytics-full/duplicates-groups.csv",
    }

    # ---- expired_notice_spend and spend_vs_award
    window_start = pd.Timestamp(log["date_min"])
    if contracts_present:
        n = notices.copy()
        n["end_d"] = pd.to_datetime(n["end"])
        n["start_d"] = pd.to_datetime(n["start"])
        active_names = set(n.loc[n["active"] == True, "supplier_norm"])
        ended = n[n["active"] == False]
        rows = []
        for s, grp in ended.groupby("supplier_norm"):
            if s in sup.index and s not in active_names:
                last = grp.sort_values("end_d").iloc[-1]
                rows.append({"supplier_norm": s, "supplier": sup.loc[s, "supplier"],
                             "total_gbp": sup.loc[s, "total_gbp"], "annualised_estimate": sup.loc[s, "annualised_estimate"],
                             "n_payments": int(sup.loc[s, "n_payments"]), "dominant_tag": sup.loc[s, "dominant_tag"],
                             "latest_end_date": str(last["end_d"].date()), "notice_id": last["notice_id"],
                             "notice_title": last["title"], "notices_matched": int(grp["notice_id"].nunique())})
        ex = pd.DataFrame(rows).sort_values("annualised_estimate", ascending=False) if rows else pd.DataFrame(columns=["supplier_norm"])
        ex.to_csv(FULL / "expired-notice-spend.csv", index=False)
        tests["expired_notice_spend"] = {
            "description": "suppliers paid in the spend window whose every exactly matched notice ended before the window started",
            "parameters": {"window_start": str(window_start.date()), "match": "exact normalised name"},
            "rule_ids": RID["App C row D"],
            "caveat": "a newer contract may exist with no Contracts Finder notice; an indicator to check against the contract register, not evidence of spend without an extension",
            "suppliers": int(len(ex)),
            "gbp_3_month": money(ex["total_gbp"].sum()) if len(ex) else 0.0,
            "annualised_estimate": money(ex["annualised_estimate"].sum()) if len(ex) else 0.0,
            "top20": records(ex, ["supplier", "annualised_estimate", "latest_end_date", "notice_id", "dominant_tag"]) if len(ex) else [],
            "full_list": "analytics-full/expired-notice-spend.csv",
        }
        act = n[n["active"] == True]
        rows = []
        for s in sup.index:
            if sup.loc[s, "annualised_estimate"] <= 0:
                continue
            ms = act[act["supplier_norm"] == s]
            if ms["notice_id"].nunique() != 1:
                continue
            r = ms.iloc[0]
            if r["suppliers_on_notice"] != 1 or not (r["awarded_value"] > 0) or pd.isna(r["end_d"]) or pd.isna(r["start_d"]):
                continue
            years = max((r["end_d"] - r["start_d"]).days / 365.25, 1 / 12)
            rate = r["awarded_value"] / years
            ratio = sup.loc[s, "annualised_estimate"] / rate
            rows.append({"supplier_norm": s, "supplier": sup.loc[s, "supplier"], "notice_id": r["notice_id"],
                         "notice_title": r["title"], "awarded_value": round(r["awarded_value"], 2),
                         "contract_years": round(years, 2), "award_annual_rate": round(rate, 2),
                         "annualised_estimate": sup.loc[s, "annualised_estimate"], "total_gbp": sup.loc[s, "total_gbp"],
                         "ratio": round(ratio, 2), "flagged": bool(ratio >= RATIO_FLAG), "dominant_tag": sup.loc[s, "dominant_tag"]})
        sv = pd.DataFrame(rows).sort_values("ratio", ascending=False) if rows else pd.DataFrame(columns=["supplier_norm", "flagged"])
        sv.to_csv(FULL / "spend-vs-award.csv", index=False)
        fl = sv[sv["flagged"] == True]
        tests["spend_vs_award"] = {
            "description": f"suppliers matched to one live single-supplier notice with an award value: annualised estimate divided by the award's annual rate, flagged at {RATIO_FLAG} or more",
            "parameters": {"ratio_flag": RATIO_FLAG, "award_annual_rate": "Awarded Value / contract years (start to end)"},
            "rule_ids": RID["App C row E"],
            "caveat": "award values may be estimates or maxima, and the spend window is short; a high ratio is a question for the contract manager, not evidence of a variation",
            "checked": int(len(sv)), "flagged": int(len(fl)),
            "flagged_annualised_estimate": money(fl["annualised_estimate"].sum()) if len(fl) else 0.0,
            "top20": records(fl, ["supplier", "ratio", "annualised_estimate", "award_annual_rate", "notice_id"]) if len(fl) else [],
            "full_list": "analytics-full/spend-vs-award.csv",
        }
    else:
        for k in ("expired_notice_spend", "spend_vs_award"):
            tests[k] = {"skipped": True, "reason": "no contracts.csv in data/"}
            skipped.append({"test": k, "tier": "all", "reason": "no contracts.csv in data/"})

    c = log["contracts"]
    analytics = {
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "scripts": ["scripts/clean.py", "scripts/analyse.py", "scripts/common.py"],
        "population": {
            "files": [f["file"] for f in log["files"]], "rows_raw": log["rows_raw"],
            "rows_after_exclusions": log["rows_after_exclusions"], "date_min": log["date_min"], "date_max": log["date_max"],
            "months_covered": months, "annualisation_factor": factor, "total_gbp": log["total_gbp"],
            "excluded": log["excluded"], "tags": log["tags"],
            "limitations": ["population is expenditure over £500 only, so split and duplicate counts are lower bounds",
                            "Date is a payment-run timestamp, not an invoice date",
                            "suppliers published as 'Redacted' are excluded from every supplier-level test",
                            "annualised estimates extrapolate three months and ignore seasonality"],
        },
        "thresholds": thresholds,
        "skipped": skipped,
        "contracts": {**{k: c.get(k) for k in ("contracts_present", "rows_in_file", "rows_for_council", "rows_dropped_other_buyers",
                                                 "notice_supplier_pairs", "distinct_suppliers", "active_in_window",
                                                 "ended_before_window", "zero_value_awards", "rows_per_year",
                                                 "published_range", "warnings")},
                      "register_present": register_present, "caveat": CAVEAT_NOTICES},
        "matching": matching,
        "tests": tests,
    }
    (OUT / "analytics.json").write_text(json.dumps(analytics, indent=2, ensure_ascii=False, default=str) + "\n", encoding="utf-8")

    print(f"thresholds: {[(t['value'], t['competition_triggering']) for t in thresholds]}; skipped tiers: {nulls}")
    for t in tests["threshold_clustering"]["per_threshold"]:
        print(f"threshold_clustering T={t['threshold']}: {t['count']} payments (general procurement {t['general_procurement']['count']})")
    for t in tests["split_purchases"]["per_threshold"]:
        print(f"split_purchases T={t['threshold']}: {t['windows']} windows / {t['suppliers']} suppliers; general procurement {t['headline_general_procurement']}")
    hvs = tests["high_value_suppliers"]
    print(f"high_value_suppliers: {hvs['suppliers']} (general procurement {hvs['headline_general_procurement']['suppliers']})")
    oc = tests["off_contract"]
    if not oc.get("skipped"):
        print("off_contract: by class " + str({k: v['suppliers'] for k, v in oc['by_match_class'].items()}))
    d = tests["duplicates"]
    print(f"duplicates: {d['groups']} groups; per tier " + str({k: v['groups'] for k, v in d['per_tier'].items()}))
    if not tests["expired_notice_spend"].get("skipped"):
        print(f"expired_notice_spend: {tests['expired_notice_spend']['suppliers']} suppliers")
        print(f"spend_vs_award: {tests['spend_vs_award']['flagged']} of {tests['spend_vs_award']['checked']} flagged")
    print(f"matching: {matching}")
    print("written: outputs/analytics.json and analytics-full/")


if __name__ == "__main__":
    main()
