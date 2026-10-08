"""Shared helpers for the spend-analyst scripts (clean.py, analyse.py, selfcheck.py).

Everything here is deterministic. No figure is typed in: thresholds come from
outputs/rules.json, data comes from data/.
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "outputs"
FULL = OUT / "analytics-full"

EXPECTED_COLUMNS = ["Service", "Expenditure category", "Narrative", "Date", "Net amount", "Supplier name"]
SPEND_SHEET = "Data to publish"

# Supplier normalisation, shared by spend and contracts.
DROP_TOKENS = {"LTD", "LIMITED", "PLC", "LLP", "LLC", "INC", "CIC", "CIO", "UK", "THE"}
GENERIC_TOKENS = set("""AND OF THE SERVICES SERVICE GROUP CARE COMPANY HOMES HOME HOUSE UNIVERSITY
COUNCIL TRUST SOLUTIONS CONSULTANCY CONSULTING ASSOCIATES PARTNERSHIP NETWORK CENTRE CENTER TRAVEL
CARS COACHES TAXIS CONSTRUCTION HEALTHCARE HEALTH SCHOOL SCHOOLS EDUCATION SUPPORT LIVING CHILDREN
CHILDRENS SEN BERKSHIRE WEST SOUTH NORTH EAST READING NEWBURY THATCHAM HUNGERFORD SOUTHERN SYSTEMS
SOFTWARE HOUSING SECURITY CLEANING FOSTERING COMMUNITY BUSINESS MANAGEMENT FACILITIES SUPPLIES
CATERING TRANSPORT ENGINEERING HIRE PROPERTY PROPERTIES VALLEY""".split())

# Exclusion and tagging regexes (logged to cleaning-log.json).
RX_REDACTED = r"^\s*redacted\s*$"
RX_PENSION = r"LGPS|PENSION|SUPERANNUATION"
RX_INTER_AUTH_SUPPLIER = r"\b(?:COUNCIL|BOROUGH|COUNTY|CNCL|NHS|POLICE|FIRE AUTHORITY|FIRE AND RESCUE|HMRC|HM REVENUE|DEPARTMENT FOR|MINISTRY OF)\b"
RX_INTER_AUTH_NARRATIVE = r"JOINT ARRANGEMENTS"
PLACEMENT_SERVICES = ("Adult Social Care", "Children's Social Care", "Education")
PLACEMENT_NARRATIVES = {"Private Contractors", "Other agencies", "Voluntary Associations"}
RX_GRANT = r"GRANT"
RX_AGENCY = r"AGENCY"
RX_PREMISES = r"\bRENTS?\b|\bRATES\b|WATER RATES|LEASE"
TAG_ORDER = ["care_or_education_placement", "grant", "agency_staff", "premises_non_procurement", "general_procurement"]

CAVEAT_NOTICES = (
    "contracts.csv holds published notices, not a contract register. It holds awards published on "
    "Contracts Finder in roughly the last five years. A contract awarded earlier, one advertised only on "
    "Find a Tender, a framework call-off recorded under another buyer, or an exempt placement will have no "
    "notice here. 'No notice found' is therefore an indicator to check against the council's contract "
    "register, never evidence of off-contract spend. Contracts Finder does not carry awards below the "
    "publication threshold, so results must never be used to question smaller suppliers."
)


def normalise_supplier(name) -> str:
    s = str(name or "").upper()
    s = s.replace("&", " AND ")
    s = re.sub(r"\([^)]*\)", " ", s)                 # bracketed qualifiers
    s = re.sub(r"\b(T/A|TRADING AS)\b.*$", " ", s)    # trading-as suffixes
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    toks = [t for t in s.split() if t not in DROP_TOKENS]
    return " ".join(toks)


def distinctive(norm: str) -> set:
    return {t for t in norm.split() if t not in GENERIC_TOKENS and len(t) >= 3}


def load_rules():
    p = OUT / "rules.json"
    if not p.exists():
        raise SystemExit("STOP: outputs/rules.json is missing; run /extract-rules first")
    return json.loads(p.read_text(encoding="utf-8"))


def derive_thresholds(rules_doc):
    """Distinct numeric thresholds from threshold / approver / anti-avoidance rules.

    competition_triggering: the rule's required action asks for three or more quotes, or tenders.
    A single quote (Appendix B row A) is not competition.
    """
    out = {}
    for r in rules_doc["rules"]:
        if r["type"] not in ("threshold", "approver", "anti-avoidance"):
            continue
        action = (r.get("required_action") or "").lower()
        comp = bool(re.search(r"three|five|tender", action)) and r["type"] == "threshold"
        for side in ("low", "high"):
            v = r.get(f"threshold_{side}")
            if v is None:
                continue
            inc = r.get(f"threshold_{side}_inclusive")
            # the threshold is the value at which the obligation starts:
            # a low bound starts it (inclusive as printed); a high bound ends the band below it,
            # so the next band starts there (inclusive iff the high bound was exclusive)
            starts_inclusive = bool(inc) if side == "low" else (not inc if inc is not None else True)
            t = out.setdefault(v, {"value": v, "inclusive": starts_inclusive, "competition_triggering": False,
                                   "rule_ids": []})
            if side == "low":
                t["inclusive"] = starts_inclusive
                t["competition_triggering"] = t["competition_triggering"] or comp
            if r["rule_id"] not in t["rule_ids"]:
                t["rule_ids"].append(r["rule_id"])
    return [out[k] for k in sorted(out)]


def null_parameters(rules_doc):
    return [k for k, v in rules_doc.get("parameters", {}).items() if v.get("value") is None]


def money(x) -> float:
    return round(float(x), 2)
