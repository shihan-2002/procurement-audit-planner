#!/usr/bin/env python3
"""Validate outputs/risk-ratings.json and render the risk register.

Usage: build_register.py [RATINGS_JSON] [--rules outputs/rules.json]
       [--analytics outputs/analytics.json] [--history outputs/history.json]
       [--comments outputs/auditor-comments.md] [--out-dir outputs]

The risk-assessor judges; this script computes and checks.
  citations     [rule:ID], [metric:$.path] (analytics.json) and [history:ID or $.path]
                (history.json) must resolve. A likelihood or impact justification with
                no resolvable citation, or with a broken one, excludes the risk.
  placeholders  {{$.path}} are filled from analytics.json; a literal figure typed in
                prose is a WARN (the agent treats it as a failure).
  scores        likelihood and impact 1-5; score = L x I; matrix label from the council's
                Figure 1 and band from Table 4 in history.json (fallback scale if the
                method is not usable).
  uplift        a repeat-finding uplift must cite a history audit with an adverse opinion.
  names         supplier names from analytics top-20 lists must not appear in statements
                or justifications (WARN).
  gate          writes outputs/auditor-comments.md (one row per rated risk, decisions kept).
                On a re-run with decisions recorded, the ratings must carry a `revision`
                block; every decision must be applied and nothing else may change.
Writes outputs/risk-register.md, outputs/auditor-comments.md and
outputs/.register-state.json (the last built state, used to detect unrequested changes).
Exit 0 when there are no failures.
"""
import argparse, datetime, json, re, sys
from collections import OrderedDict
from pathlib import Path

CITE_RE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")
PH_RE = re.compile(r"\{\{(\$[^}]+)\}\}")
NUM_RE = re.compile(r"£\s?\d|\b\d{3,}\b|\b\d+(?:\.\d+)?%")
ADVERSE = ("limited", "weak", "unsatisfactory", "no assurance", "minimal")
DECISIONS = {"approve", "amend", "reject"}
FALLBACK_LABELS = ["Very low", "Low", "Medium", "High", "Very high"]


def jpath(obj, path):
    if not path.startswith("$"):
        return False, None
    cur = obj
    for key, idx in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", path[1:]):
        try:
            cur = cur[int(idx)] if idx else cur[key]
        except (KeyError, IndexError, TypeError):
            return False, None
    return True, cur


def fmt(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, float):
        return f"{v:,.2f}" if v != int(v) else f"{int(v):,}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def history_index(h):
    idx = {}
    def walk(o):
        if isinstance(o, dict):
            if isinstance(o.get("id"), str):
                idx[o["id"]] = o
            for v in o.values(): walk(v)
        elif isinstance(o, list):
            for v in o: walk(v)
    walk(h)
    return idx


def read_comments(path):
    out = {"reviewer": "", "date": "", "rows": OrderedDict()}
    if not path.exists():
        return out
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^Reviewer:[ \t]*(.*)$", text, re.M); out["reviewer"] = m.group(1).strip() if m else ""
    m = re.search(r"^Date:[ \t]*(.*)$", text, re.M); out["date"] = m.group(1).strip() if m else ""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"R-\d+", cells[0]):
            out["rows"][cells[0]] = {"title": cells[1], "now": cells[2], "scope": cells[3],
                                     "decision": cells[4].lower(), "comment": "|".join(cells[5:]).strip()}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ratings", nargs="?", default="outputs/risk-ratings.json")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--history", default="outputs/history.json")
    ap.add_argument("--comments", default="outputs/auditor-comments.md")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args()
    out = Path(a.out_dir)
    fails, warns = [], []

    for p in (a.ratings, a.rules, a.analytics, a.history):
        if not Path(p).exists():
            print(f"FAIL  input missing: {p}"); return 1
    R = json.loads(Path(a.ratings).read_text(encoding="utf-8"))
    rules = {r["rule_id"]: r for r in json.loads(Path(a.rules).read_text())["rules"]}
    an = json.loads(Path(a.analytics).read_text())
    hist = json.loads(Path(a.history).read_text())
    hidx = history_index(hist)
    state_path = out / ".register-state.json"
    prev = json.loads(state_path.read_text()) if state_path.exists() else {"revision": 0, "risks": {}}
    com = read_comments(Path(a.comments))
    decided = OrderedDict((k, v) for k, v in com["rows"].items() if v["decision"])

    # ---------------------------------------------------------------- scale
    sm = hist.get("scoring_method") or {}
    usable = bool(sm.get("usable"))
    if usable:
        L_lab = {e["score"]: e["label"] for e in sm["likelihood_scale"]}
        I_lab = {e["score"]: e["label"] for e in sm["impact_scale"]}
        matrix = sm["combination"]["matrix_labels_by_impact_then_likelihood"]
        bands = sm["bands"]
        scale_note = ("Scale: the council's own method from the Risk Management Strategy 2024-27 as recorded in "
                      "history.json (Table 1 impact, Table 2 likelihood, Figure 1 matrix, Table 4 bands) [history:$.scoring_method.usable].")
        conflict = hidx.get("D-01")
        if conflict:
            scale_note += (" Where the strategy conflicts, this register uses Table 4: Figure 4's rule that risks scoring 9 or above enter "
                           "the Corporate Risk Register is marked, not applied [history:D-01].")
    else:
        L_lab = I_lab = {i + 1: FALLBACK_LABELS[i] for i in range(5)}
        matrix = None
        bands = [{"level": "High", "score_min": 15, "score_max": 25, "response": ""},
                 {"level": "Medium", "score_min": 8, "score_max": 14, "response": ""},
                 {"level": "Low", "score_min": 1, "score_max": 7, "response": ""}]
        scale_note = "FALLBACK SCALE: history.json reports no usable scoring method, so 1-5 Very low to Very high is used."

    def band_of(score):
        for b in bands:
            if b["score_min"] <= score <= b["score_max"]:
                return b
        return {"level": "unbanded", "response": ""}

    def label_of(L, I):
        if matrix:
            return matrix[str(I)][L - 1]
        return band_of(L * I)["level"]

    supplier_names = set()
    def collect_names(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if k == "supplier" and isinstance(v, str) and len(v) >= 6:
                    supplier_names.add(v.upper())
                collect_names(v)
        elif isinstance(o, list):
            for v in o: collect_names(v)
    collect_names(an.get("tests", {}))

    # ---------------------------------------------------------------- helpers
    def resolve(text):
        """-> (n_ok, problems, rendered_evidence_list)"""
        ok, probs, ev = 0, [], []
        for kind, ref in CITE_RE.findall(text or ""):
            ref = ref.strip()
            if kind == "rule":
                if ref in rules: ok += 1; ev.append(("rule", ref))
                else: probs.append(f"unknown rule {ref}")
            elif kind == "metric":
                f, v = jpath(an, ref)
                if f and not isinstance(v, (dict, list)): ok += 1; ev.append(("metric", ref))
                elif f: probs.append(f"metric {ref} is not a scalar")
                else: probs.append(f"metric path not found {ref}")
            else:
                if ref.startswith("$"):
                    f, v = jpath(hist, ref)
                    if f: ok += 1; ev.append(("history", ref))
                    else: probs.append(f"history path not found {ref}")
                elif ref in hidx: ok += 1; ev.append(("history", ref))
                else: probs.append(f"unknown history item {ref}")
        return ok, probs, ev

    def fill(text, where, probs):
        def sub(m):
            f, v = jpath(an, m.group(1))
            if not f or isinstance(v, (dict, list)):
                probs.append(f"{where}: placeholder not resolvable {m.group(1)}")
                return "«unresolved»"
            return fmt(v)
        filled = PH_RE.sub(sub, text or "")
        bare = CITE_RE.sub("", PH_RE.sub("", text or ""))
        if NUM_RE.search(bare):
            warns.append(f"{where}: literal figure typed in prose; use a {{{{$.path}}}} placeholder: {bare.strip()[:70]!r}")
        up = bare.upper()
        for n in supplier_names:
            if n in up:
                warns.append(f"{where}: supplier name appears in prose: {n.title()[:40]}")
        return filled

    def strip(text):
        t = CITE_RE.sub(lambda m: f"[{m.group(2)}]" if m.group(1) == "rule" else "", text or "")
        return re.sub(r"\s+([.,;:])", r"\1", re.sub(r"\s{2,}", " ", t)).strip()

    # ---------------------------------------------------------------- risks
    kept, excluded_by_validation = OrderedDict(), []
    ids_seen = set()
    for r in R.get("risks", []):
        rid = r.get("id", "?")
        probs = []
        if not re.fullmatch(r"R-\d{2}", rid) or rid in ids_seen:
            probs.append("id must be R-NN and unique")
        ids_seen.add(rid)
        for part in ("likelihood", "impact"):
            p = r.get(part) or {}
            s = p.get("score")
            if not isinstance(s, int) or not 1 <= s <= 5:
                probs.append(f"{part}.score must be an integer 1-5")
            n_ok, bad, _ = resolve(p.get("justification", ""))
            if bad: probs += [f"{part}: {b}" for b in bad]
            if n_ok == 0: probs.append(f"{part}: justification cites no rule, metric or history item")
        up = r.get("uplift")
        if up:
            hid = up.get("history", "")
            item = hidx.get(hid)
            if not item:
                probs.append(f"uplift cites unknown history item {hid}")
            elif not any(w in (str(item.get("opinion", "")) + " " + str(item.get("implementation_opinion", ""))).lower() for w in ADVERSE):
                probs.append(f"uplift cites {hid}, which has no adverse opinion")
            elif f"[history:{hid}]" not in r["likelihood"].get("justification", ""):
                probs.append("uplift is not stated in the likelihood justification")
        ev_ok = 0
        for e in r.get("evidence") or []:
            n_ok, bad, _ = resolve(e)
            ev_ok += n_ok
            probs += [f"evidence: {b}" for b in bad]
        if ev_ok == 0: probs.append("evidence list cites nothing")
        if probs:
            excluded_by_validation.append({"id": rid, "title": r.get("title", ""), "reasons": probs})
            continue
        L, I = r["likelihood"]["score"], r["impact"]["score"]
        rr = {"raw": r, "L": L, "I": I, "score": L * I, "label": label_of(L, I), "band": band_of(L * I)}
        rr["statement"] = fill(r.get("statement", ""), f"{rid}.statement", fails)
        rr["lj"] = fill(r["likelihood"]["justification"], f"{rid}.likelihood", fails)
        rr["ij"] = fill(r["impact"]["justification"], f"{rid}.impact", fails)
        rr["focus"] = fill(r.get("proposed_focus", ""), f"{rid}.proposed_focus", fails)
        kept[rid] = rr

    # ---------------------------------------------------------------- revision / gate
    rev_no = 0
    rev = R.get("revision")
    changed_labels = []
    if decided:
        if not rev:
            fails.append("auditor decisions are recorded in auditor-comments.md but risk-ratings.json has no 'revision' block")
        else:
            rev_no = rev.get("number")
            if rev_no != prev.get("revision", 0) + 1:
                fails.append(f"revision.number is {rev_no}; expected {prev.get('revision', 0) + 1}")
            changed = {c["id"]: c["change"] for c in rev.get("changed", [])}
            excl_ids = {x.get("id") for x in R.get("excluded", []) if x.get("id")}
            for cid, d in decided.items():
                dec = d["decision"]
                if dec not in DECISIONS:
                    fails.append(f"{cid}: decision '{dec}' is not approve, amend or reject"); continue
                if dec == "reject":
                    if cid in kept: fails.append(f"{cid}: rejected by the auditor but still rated in the register")
                    if cid not in excl_ids: fails.append(f"{cid}: rejected but not listed in excluded with its id and the auditor's reason")
                    if changed.get(cid) != "rejected": fails.append(f"{cid}: rejection not recorded in revision.changed")
                elif dec == "amend":
                    if cid not in kept: fails.append(f"{cid}: amended but missing from the register")
                    if changed.get(cid) != "amended": fails.append(f"{cid}: amendment not recorded in revision.changed")
                elif dec == "approve":
                    if cid not in kept: fails.append(f"{cid}: approved but missing from the register")
                    if cid in changed: fails.append(f"{cid}: approved as rated but listed as changed")
            for cid in changed:
                if decided.get(cid, {}).get("decision") not in ("amend", "reject"):
                    fails.append(f"{cid}: listed in revision.changed but the auditor did not amend or reject it")
            for cid, rr in kept.items():
                p = prev["risks"].get(cid)
                if p is None:
                    fails.append(f"{cid}: new risk added in a revision; the auditor did not ask for it"); continue
                same = p["L"] == rr["L"] and p["I"] == rr["I"] and p["in_scope"] == rr["raw"].get("recommend_in_scope", True)
                if not same and decided.get(cid, {}).get("decision") != "amend":
                    fails.append(f"{cid}: score or scope changed without an auditor amendment")
            changed_labels = [f"{k} ({v})" for k, v in changed.items()]
    elif rev:
        fails.append("risk-ratings.json has a 'revision' block but no decisions are recorded in auditor-comments.md")

    # ---------------------------------------------------------------- render register
    today = R.get("generated_at") or str(datetime.date.today())
    rules_txt = lambda rid: rules[rid]["verbatim_quote"]
    md = ["# Procurement audit planning: risk register\n"]
    if rev_no:
        md.append(f"*Status: REVISION {rev_no} for auditor sign-off.*\n")
        md.append(f"*Revision {rev_no}, following auditor comments dated {com['date'] or 'undated'}.\nChanged: "
                  f"{', '.join(changed_labels) if changed_labels else 'none'}.*\n")
    else:
        md.append("*Status: DRAFT for auditor review (Phase 2 gate).*\n")
    md.append("**Indicators, not findings.** Every risk describes a pattern in public data or a control to test. "
              "Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.\n")
    md.append(f"*Generated {today} by `build_register.py` from `risk-ratings.json`, `rules.json`, `analytics.json` and `history.json`. "
              "Every figure below was filled in by the script.*\n")
    md.append("## Scoring scale\n")
    md.append(strip(scale_note) + "\n")
    md.append("| Score | Likelihood | Impact |\n|---|---|---|")
    for s in range(5, 0, -1):
        md.append(f"| {s} | {L_lab[s]} | {I_lab[s]} |")
    md.append("\n| Band | Scores | Response |\n|---|---|---|")
    for b in bands:
        md.append(f"| {b['level']} | {b['score_min']}-{b['score_max']} | {b.get('response', '')} |")
    md.append("\n## Summary\n")
    md.append("| ID | Risk | L | I | Score | Matrix | Band | Response | Scope |\n|---|---|---|---|---|---|---|---|---|")
    order = sorted(kept.items(), key=lambda kv: (-kv[1]["score"], kv[0]))
    for rid, rr in order:
        r = rr["raw"]
        md.append(f"| {rid} | {r.get('title', '')} | {rr['L']} | {rr['I']} | {rr['score']} | {rr['label']} | {rr['band']['level']} | "
                  f"{rr['band'].get('response', '')} | {'in' if r.get('recommend_in_scope', True) else 'out'} |")
    md.append("\n## Risks\n")
    for rid, rr in order:
        r = rr["raw"]
        ov = " *(auditor override)*" if r.get("auditor_override") else ""
        md.append(f"### {rid}: {r.get('title', '')}{ov}\n")
        md.append(f"{strip(rr['statement'])}\n")
        md.append(f"- **Likelihood {rr['L']} ({L_lab[rr['L']]}).** {strip(rr['lj'])}")
        md.append(f"- **Impact {rr['I']} ({I_lab[rr['I']]}).** {strip(rr['ij'])}")
        md.append(f"- **Score {rr['score']}: {rr['label']}; band {rr['band']['level']}.** "
                  f"Recommended {'in' if r.get('recommend_in_scope', True) else 'out of'} scope.")
        if r.get("uplift"):
            md.append(f"- **Repeat-finding uplift:** likelihood raised by one point for an adverse opinion on the same theme ({r['uplift']['history']}).")
        md.append("\n**Evidence**\n")
        seen = set()
        for e in r.get("evidence") or []:
            _, _, ev = resolve(e)
            label = strip(CITE_RE.sub("", PH_RE.sub(lambda m: fmt(jpath(an, m.group(1))[1]), e))).strip(" :;-")
            for kind, ref in ev:
                if (kind, ref) in seen: continue
                seen.add((kind, ref))
                if kind == "rule":
                    q = re.sub(r"\s+", " ", rules_txt(ref))
                    exc = q if len(q) <= 110 else q[:110].rstrip() + "…"
                    md.append(f"- [rule:{ref}] clause {rules[ref]['clause']}: \"{exc}\"")
                elif kind == "metric":
                    md.append(f"- [metric:{ref}] {label or 'value'}: {fmt(jpath(an, ref)[1])}")
                else:
                    item = hidx.get(ref) if not ref.startswith("$") else None
                    if item and "audit_title" in item:
                        md.append(f"- [history:{ref}] {item['audit_title']}: {item['opinion']} ({item['source']}, p.{item['pdf_page']})")
                    elif item:
                        md.append(f"- [history:{ref}] {item.get('theme') or item.get('item') or label}: {item.get('source', '')}, p.{item.get('pdf_page', '')}")
                    else:
                        md.append(f"- [history:{ref}] {label or 'scoring method'}")
        md.append(f"\n**Proposed focus.** {strip(rr['focus'])}\n")
        if r.get("sample_source"):
            md.append(f"**Sample source.** `analytics-full/{r['sample_source']}`\n")
    md.append("## Excluded\n")
    md.append("Themes considered and not rated, and risks removed at the gate.\n")
    for x in R.get("excluded", []):
        tag = f"{x['id']}: " if x.get("id") else ""
        md.append(f"- {tag}{x.get('theme', x.get('title', ''))}: {strip(x.get('reason', ''))}")
    for x in excluded_by_validation:
        md.append(f"- {x['id']}: {x['title']}: excluded by validation ({'; '.join(x['reasons'])})")
    md.append("\n## Auditor decisions\n")
    if not decided:
        md.append("None recorded yet. The auditor records approve, amend or reject for each risk in `outputs/auditor-comments.md`; "
                  "the risk-assessor then applies them in a revision.")
    else:
        md.append(f"Decisions by {com['reviewer'] or 'unnamed reviewer'} dated {com['date'] or 'undated'}, applied in revision {rev_no}.\n")
        md.append("| ID | Decision | Applied as |\n|---|---|---|")
        for cid, d in decided.items():
            applied = {"approve": "kept as rated", "reject": "rejected; moved to excluded",
                       "amend": "amended" + (" (auditor override)" if kept.get(cid, {}).get("raw", {}).get("auditor_override") else "")}.get(d["decision"], "?")
            md.append(f"| {cid} | {d['decision']} | {applied} |")
        blank = [k for k in kept if k not in decided]
        if blank:
            md.append(f"\nStill undecided: {', '.join(blank)}.")

    # ---------------------------------------------------------------- report and write
    for w in warns: print("WARN ", w)
    for f in fails: print("FAIL ", f)
    for x in excluded_by_validation: print(f"EXCL  {x['id']}: " + "; ".join(x["reasons"]))
    print(f"\nrisks kept: {len(kept)}, excluded by validation: {len(excluded_by_validation)}, warnings: {len(warns)}, failures: {len(fails)}")
    if fails:
        print("nothing written: fix the failures first")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    (out / "risk-register.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # auditor-comments.md: one row per kept risk, plus rows for risks already rejected
    rows = []
    for rid, rr in order:
        old = com["rows"].get(rid, {})
        rows.append(f"| {rid} | {rr['raw'].get('title', '')} | {rr['L']} × {rr['I']} = {rr['score']} | "
                    f"{'in' if rr['raw'].get('recommend_in_scope', True) else 'out'} | {old.get('decision', '')} | {old.get('comment', '')} |")
    for rid, d in com["rows"].items():
        if rid not in kept and d["decision"] == "reject":
            rows.append(f"| {rid} | {d['title']} | {d['now']} | out | reject | {d['comment']} |")
    cm = ["# Auditor comments: risk register gate\n", f"Reviewer: {com['reviewer']}", f"Date: {com['date']}\n",
          "For each risk write **approve**, **amend** (say what to change in Comment) or **reject** (give the reason in Comment). "
          "A blank Decision means undecided. The risk-assessor applies the decisions in a revision; nothing goes to the agent team "
          "until every risk has a decision.\n",
          "| ID | Risk | Now | Scope now | Decision | Comment |", "|---|---|---|---|---|---|", *rows]
    (out / "auditor-comments.md").write_text("\n".join(cm) + "\n", encoding="utf-8")
    state = {"revision": rev_no if rev_no else prev.get("revision", 0),
             "risks": {rid: {"L": rr["L"], "I": rr["I"], "in_scope": rr["raw"].get("recommend_in_scope", True)} for rid, rr in kept.items()}}
    state_path.write_text(json.dumps(state, indent=2) + "\n")
    n_dec = sum(1 for rid in kept if com["rows"].get(rid, {}).get("decision"))
    print(f"written: {out / 'risk-register.md'}")
    print(f"written: {out / 'auditor-comments.md'} ({len(kept)} risks, {n_dec} with a decision already recorded"
          + (f"; revision {rev_no}, {len(changed_labels)} changed)" if rev_no else ")"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
