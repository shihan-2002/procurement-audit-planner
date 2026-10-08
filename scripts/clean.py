#!/usr/bin/env python3
"""Clean the spend workbooks and the Contracts Finder export.

Writes outputs/analytics-full/: spend-clean.csv, spend-excluded.csv,
notices-clean.csv, cleaning-log.json. Prints aggregates only.
Stops with a clear message on any malformed input.
"""
import json
import re
import sys
from datetime import datetime

import pandas as pd

from common import (DATA, FULL, EXPECTED_COLUMNS, SPEND_SHEET, RX_REDACTED, RX_PENSION,
                    RX_INTER_AUTH_SUPPLIER, RX_INTER_AUTH_NARRATIVE, PLACEMENT_SERVICES,
                    PLACEMENT_NARRATIVES, RX_GRANT, RX_AGENCY, RX_PREMISES, normalise_supplier, money)


def stop(msg):
    print(f"STOP: {msg}")
    sys.exit(1)


def load_spend():
    files = sorted(list((DATA / "spend").glob("*.xlsx")) + list((DATA / "spend").glob("*.csv")))
    if not files:
        stop("no spend files in data/spend/")
    frames, log = [], []
    for f in files:
        if f.suffix == ".csv":
            raw = pd.read_csv(f, header=None, dtype=str)
        else:
            xl = pd.ExcelFile(f)
            if SPEND_SHEET not in xl.sheet_names:
                stop(f"{f.name}: sheet '{SPEND_SHEET}' not found (sheets: {xl.sheet_names})")
            raw = pd.read_excel(f, sheet_name=SPEND_SHEET, header=None)
        hdr = [i for i in range(min(len(raw), 30)) if str(raw.iloc[i, 0]).strip() == "Service"]
        if not hdr:
            stop(f"{f.name}: no header row whose first cell is 'Service'")
        h = hdr[0]
        df = raw.iloc[h + 1:].copy()
        df.columns = [str(c).strip() for c in raw.iloc[h]]
        df = df[[c for c in df.columns if c and c != "nan"]]
        if list(df.columns) != EXPECTED_COLUMNS:
            stop(f"{f.name}: columns {list(df.columns)} != expected {EXPECTED_COLUMNS}")
        df = df.dropna(how="all")
        # sheet row: Excel is 1-based; raw row index i sits on sheet row i+1
        df["sheet_row"] = df.index + 1
        df["source_file"] = f.name
        df["row_id"] = df["source_file"] + ":" + df["sheet_row"].astype(str)
        # dates: datetime already, or text parsed month-first with explicit formats
        def parse_date(v):
            if isinstance(v, (pd.Timestamp, datetime)):
                return pd.Timestamp(v)
            s = str(v).strip()
            for fmt in ("%m/%d/%y", "%m/%d/%Y", "%m/%d/%y %H:%M", "%m/%d/%Y %H:%M:%S"):
                try:
                    return pd.Timestamp(datetime.strptime(s, fmt))
                except ValueError:
                    pass
            return pd.NaT
        df["Date"] = df["Date"].map(parse_date)
        df["Net amount"] = pd.to_numeric(df["Net amount"], errors="coerce")
        for col in ("Date", "Net amount", "Supplier name"):
            if df[col].isna().any():
                stop(f"{f.name}: {int(df[col].isna().sum())} rows with null/unparseable {col}")
        if (df["Net amount"] < 0).any():
            stop(f"{f.name}: {int((df['Net amount'] < 0).sum())} negative amounts")
        log.append({"file": f.name, "header_sheet_row": h + 1, "rows": int(len(df)),
                    "date_min": str(df["Date"].min().date()), "date_max": str(df["Date"].max().date())})
        frames.append(df)
    spend = pd.concat(frames, ignore_index=True)
    spend["pay_date"] = spend["Date"].dt.date.astype(str)
    spend["Date"] = spend["Date"].dt.strftime("%Y-%m-%d %H:%M:%S.%f").str[:-3]
    spend["Net amount"] = spend["Net amount"].round(2)
    spend["supplier_norm"] = spend["Supplier name"].map(normalise_supplier)
    return spend, log


def exclusions(spend):
    s_up = spend["Supplier name"].astype(str).str.upper()
    narr = spend["Narrative"].astype(str)
    reasons = pd.Series("", index=spend.index)
    redacted = spend["Supplier name"].astype(str).str.match(RX_REDACTED, case=False)
    pension = narr.str.upper().str.contains(RX_PENSION, regex=True)
    inter = (s_up.str.contains(RX_INTER_AUTH_SUPPLIER, regex=True) | narr.str.upper().str.contains(RX_INTER_AUTH_NARRATIVE, regex=True)) \
        & (narr != "Private Contractors")
    reasons[inter] = "inter_authority"
    reasons[pension] = "pension_statutory"
    reasons[redacted] = "redacted_supplier"
    text = {
        "redacted_supplier": "supplier published as 'Redacted' covers many payees (mostly individuals); unusable for supplier-level tests",
        "pension_statutory": "LGPS / pension / superannuation contributions are statutory, not procurement",
        "inter_authority": "payments to other public bodies (councils, NHS, police, HMRC, government departments) or joint arrangements; not competed procurement",
    }
    summary = {}
    for k in ("redacted_supplier", "pension_statutory", "inter_authority"):
        m = reasons == k
        summary[k] = {"rows": int(m.sum()), "gbp": money(spend.loc[m, "Net amount"].sum()), "reason": text[k]}
    return reasons, summary


def tag(spend):
    svc = spend["Service"].astype(str)
    narr = spend["Narrative"].astype(str)
    nu = narr.str.upper()
    tags = pd.Series("general_procurement", index=spend.index)
    order = [
        ("premises_non_procurement", nu.str.contains(RX_PREMISES, regex=True)),
        ("agency_staff", nu.str.contains(RX_AGENCY, regex=True)),
        ("grant", nu.str.contains(RX_GRANT, regex=True)),
        ("care_or_education_placement", svc.str.startswith(PLACEMENT_SERVICES) & narr.isin(PLACEMENT_NARRATIVES)),
    ]
    # apply in reverse so the first rule in TAG_ORDER wins
    for name, mask in order:
        tags[mask] = name
    return tags


def load_notices(window_start):
    p = DATA / "contracts.csv"
    log = {"contracts_present": p.exists()}
    if not p.exists():
        return None, log
    c = pd.read_csv(p, dtype=str)
    log["rows_in_file"] = int(len(c))
    keep = c["Organisation Name"].str.strip().str.upper().isin(["WEST BERKSHIRE COUNCIL", "WEST BERKSHIRE"])
    log["organisation_names_kept"] = c.loc[keep, "Organisation Name"].value_counts().to_dict()
    log["rows_dropped_other_buyers"] = int((~keep).sum())
    c = c[keep].copy()
    log["rows_for_council"] = int(len(c))
    if len(c) < 20:
        log["warnings"] = [f"only {len(c)} notices for the council; treated as absent"]
        return None, log
    sup_col = [k for k in c.columns if k.startswith("Supplier [")][0]
    rows = []
    for _, r in c.iterrows():
        packed = str(r[sup_col] or "")
        blocks = [b.strip("[]") for b in re.split(r"\]\s*\[", packed.strip()) if b.strip("[] ")]
        n = len(blocks)
        for b in blocks:
            parts = b.split("|")
            name = parts[0].strip()
            ch = parts[3].strip() if len(parts) > 3 and parts[2].strip() == "COMPANIES_HOUSE" else ""
            rows.append({
                "notice_id": r["Notice Identifier"], "title": r["Title"],
                "procedure": str(r["OJEU Procedure Type"]).strip(),
                "awarded_value": float(r["Awarded Value"]) if str(r["Awarded Value"]).strip() not in ("", "nan") else 0.0,
                "start": pd.to_datetime(r["Contract start date"], format="%d/%m/%Y", errors="coerce"),
                "end": pd.to_datetime(r["Contract end date"], format="%d/%m/%Y", errors="coerce"),
                "awarded_date": pd.to_datetime(r["Awarded Date"], format="%d/%m/%Y", errors="coerce"),
                "published": pd.to_datetime(r["Published Date"], format="ISO8601", utc=True, errors="coerce"),
                "supplier": name, "supplier_norm": normalise_supplier(name),
                "companies_house": ch, "suppliers_on_notice": n,
            })
    n = pd.DataFrame(rows)
    ws = pd.Timestamp(window_start)
    n["active"] = n["end"].isna() | (n["end"] >= ws)
    per_year = n.drop_duplicates("notice_id")["published"].dt.year.value_counts().sort_index()
    log.update({
        "notices": int(n["notice_id"].nunique()), "notice_supplier_pairs": int(len(n)),
        "distinct_suppliers": int(n["supplier_norm"].nunique()),
        "active_in_window": int(n.loc[n["active"], "notice_id"].nunique()),
        "ended_before_window": int(n.loc[~n["active"], "notice_id"].nunique()),
        "zero_value_awards": int((n.drop_duplicates("notice_id")["awarded_value"] == 0).sum()),
        "rows_per_year": {str(k): int(v) for k, v in per_year.items()},
        "published_range": [str(n["published"].min().date()), str(n["published"].max().date())],
        "warnings": [],
    })
    if log["rows_in_file"] == 1000:
        log["warnings"].append("file has exactly 1,000 rows: the export may have hit the Contracts Finder download cap")
    thin = [y for y, v in log["rows_per_year"].items() if v < 5]
    if thin:
        log["warnings"].append(f"publication years with fewer than 5 notices: {thin}; the export may be incomplete")
    return n, log


def main():
    FULL.mkdir(parents=True, exist_ok=True)
    spend, files_log = load_spend()
    reasons, excl = exclusions(spend)
    spend["tag"] = tag(spend)
    kept = spend[reasons == ""].copy()
    excluded = spend[reasons != ""].copy()
    excluded["exclusion"] = reasons[reasons != ""]
    cols = ["row_id", "source_file", "sheet_row", "Date", "pay_date", "Service", "Expenditure category",
            "Narrative", "Net amount", "Supplier name", "supplier_norm", "tag"]
    kept[cols].to_csv(FULL / "spend-clean.csv", index=False)
    excluded[cols + ["exclusion"]].to_csv(FULL / "spend-excluded.csv", index=False)

    window_start = min(pd.Timestamp(x) for x in kept["pay_date"])
    notices, nlog = load_notices(window_start)
    if notices is not None:
        out = notices.copy()
        for c in ("start", "end", "awarded_date"):
            out[c] = out[c].dt.strftime("%Y-%m-%d")
        out["published"] = out["published"].dt.strftime("%Y-%m-%d")
        out.to_csv(FULL / "notices-clean.csv", index=False)
    reg = DATA / "contract-register.csv"

    tags = {}
    for t, g in kept.groupby("tag"):
        tags[t] = {"rows": int(len(g)), "gbp": money(g["Net amount"].sum()), "suppliers": int(g["supplier_norm"].nunique())}
    months = sorted({d[:7] for d in kept["pay_date"]})
    log = {
        "generated_at": datetime.now().strftime("%Y-%m-%d"),
        "files": files_log,
        "rows_raw": int(len(spend)), "rows_after_exclusions": int(len(kept)),
        "date_min": min(kept["pay_date"]), "date_max": max(kept["pay_date"]),
        "months": months, "months_covered": len(months),
        "total_gbp_raw": money(spend["Net amount"].sum()), "total_gbp": money(kept["Net amount"].sum()),
        "excluded": excl, "tags": tags,
        "regexes": {"redacted": RX_REDACTED, "pension": RX_PENSION, "inter_authority_supplier": RX_INTER_AUTH_SUPPLIER,
                    "inter_authority_narrative": RX_INTER_AUTH_NARRATIVE, "grant": RX_GRANT, "agency": RX_AGENCY,
                    "premises": RX_PREMISES, "placement_services": list(PLACEMENT_SERVICES),
                    "placement_narratives": sorted(PLACEMENT_NARRATIVES)},
        "contracts": nlog,
        "register_present": reg.exists(),
    }
    (FULL / "cleaning-log.json").write_text(json.dumps(log, indent=2) + "\n", encoding="utf-8")
    print(f"spend: {log['rows_raw']} rows raw, {log['rows_after_exclusions']} kept, {log['months_covered']} months "
          f"({log['date_min']} to {log['date_max']})")
    for k, v in excl.items():
        print(f"  excluded {k}: {v['rows']} rows")
    for k, v in tags.items():
        print(f"  tag {k}: {v['rows']} rows, {v['suppliers']} suppliers")
    print(f"contracts: present={nlog['contracts_present']} council rows={nlog.get('rows_for_council')} "
          f"dropped={nlog.get('rows_dropped_other_buyers')} pairs={nlog.get('notice_supplier_pairs')} "
          f"active={nlog.get('active_in_window')} ended={nlog.get('ended_before_window')} warnings={nlog.get('warnings')}")
    print(f"register_present={log['register_present']}")


if __name__ == "__main__":
    main()
