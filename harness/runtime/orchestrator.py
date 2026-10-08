"""The orchestrator: runs the guide's workflow as stages over a per-run workspace.

Stages (same order as the guide):
  1 extract_rules   skill /extract-rules, run in the lead's own context
  2 analysts        spend-analyst and findings-analyst, sub-agents in parallel
  3 risk            risk-assessor sub-agent (loads the risk-assessment skill)
  4 gate            HUMAN: the auditor records decisions in the web UI;
                    the risk-assessor then applies them as a revision
  5 team            planner, challenger and qa-reviewer as an agent team that
                    messages itself; the lead only routes and watches for DONE
  6 signoff         HUMAN: the auditor signs off in review.md

Every stage ends with the project's own deterministic checks (verify_quotes,
selfcheck, verify_history, build_register, build_pack --gate, run_checks),
run by the harness, not by a model. Two modes:
  live    every judgment is made by Claude through the API
  replay  the judgments of a recorded live run are replayed (no API calls),
          the human gate is still yours, and every script and check runs for real
"""
from __future__ import annotations

import datetime
import json
import os
import queue
import re
import shutil
import subprocess
import sys
import threading
import time
import uuid
from pathlib import Path

from .agent import MODEL, Agent, BudgetExceeded, Usage, parse_agent_file
from .tools import Sandbox

ROOT = Path(__file__).resolve().parents[2]          # the Part A project
HARNESS = ROOT / "harness"
RUNS = Path(os.environ.get("HARNESS_RUNS_DIR", HARNESS / "runs"))
REPLAY = HARNESS / "replay"
MAX_RUN_USD = float(os.environ.get("HARNESS_MAX_RUN_USD", "25"))
SANDBOX_USER = os.environ.get("HARNESS_SANDBOX_USER") or None
TEAM_TIMEOUT_S = int(os.environ.get("HARNESS_TEAM_TIMEOUT_S", "3600"))
REPLAY_DELAY = float(os.environ.get("HARNESS_REPLAY_DELAY", "0.35"))

STAGES = [
    {"id": "extract_rules", "title": "Skill: /extract-rules", "kind": "skill", "lesson": "Lesson 1"},
    {"id": "analysts", "title": "Sub-agents: spend-analyst ‖ findings-analyst", "kind": "subagents", "lesson": "Lesson 2"},
    {"id": "risk", "title": "Sub-agent: risk-assessor", "kind": "subagent", "lesson": "Lesson 2"},
    {"id": "gate", "title": "Human gate: auditor decisions", "kind": "human", "lesson": "Lesson 3"},
    {"id": "team", "title": "Agent team: planner · challenger · qa-reviewer", "kind": "team", "lesson": "Lesson 4"},
    {"id": "signoff", "title": "Human gate: sign-off", "kind": "human", "lesson": "Lesson 4"},
]
TEMPLATE_ITEMS = ["CLAUDE.md", "requirements.txt", "data", "scripts", ".claude/skills", ".claude/agents",
                  ".claude/agent-memory", ".claude/settings.json", ".claude/hooks"]


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")


def as_sandbox() -> dict:
    if SANDBOX_USER and hasattr(os, "geteuid") and os.geteuid() == 0:
        return {"user": SANDBOX_USER, "group": SANDBOX_USER}
    return {}


def tool_env():
    env = dict(os.environ)
    for k in list(env):
        if k.startswith("ANTHROPIC") or k.startswith("HARNESS_PASS"):
            env.pop(k)
    return env


class Run:
    def __init__(self, mode: str, run_id: str | None = None):
        self.id = run_id or datetime.datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6]
        self.mode = mode
        self.dir = RUNS / self.id
        self.ws = self.dir / "workspace"
        self.events: list[dict] = []
        self.cond = threading.Condition()
        self.status = {s["id"]: "pending" for s in STAGES}
        self.stage_notes: dict[str, str] = {}
        self.usage: dict[str, Usage] = {}
        self.busy = False
        self.error = None
        self.stop = threading.Event()
        self.created = now()
        self.agents_live: dict[str, Agent] = {}

    # ---------------------------------------------------------------- setup
    def create_workspace(self):
        self.ws.mkdir(parents=True, exist_ok=True)
        for item in TEMPLATE_ITEMS:
            src, dst = ROOT / item, self.ws / item
            if not src.exists():
                continue
            if src.is_dir():
                shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
        (self.ws / "outputs").mkdir(exist_ok=True)
        (self.ws / ".scratch").mkdir(exist_ok=True)
        venv_bin = self.ws / ".venv" / "bin"
        venv_bin.mkdir(parents=True, exist_ok=True)
        py = Path(sys.executable)
        for n in ("python", "python3"):
            (venv_bin / n).symlink_to(py)
        if SANDBOX_USER and hasattr(os, "geteuid") and os.geteuid() == 0:
            subprocess.run(["chown", "-R", f"{SANDBOX_USER}:{SANDBOX_USER}", str(self.ws)], check=False)
            subprocess.run(["chmod", "-R", "a-w", str(self.ws / "data")], check=False)
        self.save()
        self.emit({"type": "run", "text": f"workspace created ({self.mode} mode)"})

    # ---------------------------------------------------------------- events
    def emit(self, ev: dict):
        ev = {"t": now(), "seq": len(self.events), **ev}
        with self.cond:
            self.events.append(ev)
            self.cond.notify_all()
        with open(self.dir / "events.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(ev, default=str) + "\n")

    def save(self):
        (self.dir / "run.json").write_text(json.dumps(self.state(), indent=2, default=str), encoding="utf-8")

    def state(self) -> dict:
        usd = sum(u.usd() for u in self.usage.values())
        return {"id": self.id, "mode": self.mode, "created": self.created, "busy": self.busy, "error": self.error,
                "stages": [{**s, "status": self.status[s["id"]], "note": self.stage_notes.get(s["id"], "")} for s in STAGES],
                "usage": {k: {"input": v.input + v.cache_read + v.cache_write, "output": v.output, "usd": round(v.usd(), 4)}
                          for k, v in self.usage.items()},
                "usd_total": round(usd, 4), "usd_cap": MAX_RUN_USD, "model": MODEL if self.mode == "live" else "replay",
                "outputs": sorted(p.relative_to(self.ws).as_posix() for p in (self.ws / "outputs").rglob("*")
                                  if p.is_file() and "analytics-full" not in p.parts and "samples" not in p.parts and not p.name.startswith("."))
                if (self.ws / "outputs").exists() else []}

    # ---------------------------------------------------------------- helpers
    def sh(self, args: list[str], label: str) -> tuple[int, str]:
        """Run a project script deterministically (the harness's own checks)."""
        self.emit({"type": "check_start", "agent": "harness", "text": label, "command": " ".join(args)})
        p = subprocess.run(args, cwd=self.ws, capture_output=True, text=True, env=tool_env(), timeout=900, **as_sandbox())
        out = (p.stdout + ("\n" + p.stderr if p.stderr.strip() else "")).strip()
        self.emit({"type": "check", "agent": "harness", "text": label, "exit": p.returncode, "output": out[-6000:]})
        return p.returncode, out

    def fix_owner(self):
        """In the container, keep the workspace owned by the unprivileged sandbox user."""
        if SANDBOX_USER and hasattr(os, "geteuid") and os.geteuid() == 0:
            subprocess.run(["chown", "-R", f"{SANDBOX_USER}:{SANDBOX_USER}", str(self.ws)], check=False)
            subprocess.run(["chmod", "-R", "a-w", str(self.ws / "data")], check=False)

    def py(self, *script_args) -> list[str]:
        return [str(self.ws / ".venv/bin/python"), *script_args]

    def budget(self):
        total = sum(u.usd() for u in self.usage.values())
        if total > MAX_RUN_USD:
            raise BudgetExceeded(f"run spend ${total:.2f} exceeded the cap of ${MAX_RUN_USD:.2f}")
        if self.stop.is_set():
            raise InterruptedError("run stopped")

    def make_agent(self, agent_md: Path, client, extra_system="", on_send=None, name=None) -> Agent:
        sb = Sandbox(root=self.ws, sandbox_user=SANDBOX_USER)
        a = Agent.from_file(agent_md, self.ws, client, self.emit, extra_system=extra_system, sandbox=sb,
                            budget=self.budget, on_send=on_send)
        if name:
            a.name = name
        self.usage[a.name] = a.usage
        self.agents_live[a.name] = a
        a.stop_flag = self.stop
        return a

    def file(self, rel: str) -> str:
        p = (self.ws / rel).resolve()
        if self.ws.resolve() not in p.parents or not p.is_file():
            raise FileNotFoundError(rel)
        return p.read_text(encoding="utf-8", errors="replace")


# =============================================================================== stage runner
class Orchestrator:
    def __init__(self, run: Run, client=None):
        self.r = run
        self.client = client

    def start(self, stage: str, payload: dict | None = None):
        r = self.r
        if r.busy:
            raise RuntimeError("a stage is already running")
        order = [s["id"] for s in STAGES]
        i = order.index(stage)
        for prev in order[:i]:
            if r.status[prev] != "done":
                raise RuntimeError(f"stage '{prev}' must be done first")
        if r.status[stage] == "done" and stage not in ("gate",):
            raise RuntimeError(f"stage '{stage}' is already done")
        if r.mode == "live" and self.client is None and stage not in ("signoff",):
            raise RuntimeError("live mode needs ANTHROPIC_API_KEY on the server")
        r.busy, r.error = True, None
        r.status[stage] = "running"
        r.save()
        threading.Thread(target=self._wrap, args=(stage, payload or {}), daemon=True).start()

    def _wrap(self, stage, payload):
        r = self.r
        r.emit({"type": "stage_start", "stage": stage})
        try:
            r.fix_owner()
            fn = getattr(self, f"stage_{stage}")
            result = fn(payload)
            r.fix_owner()
            r.status[stage] = result or "done"
            r.emit({"type": "stage_end", "stage": stage, "status": r.status[stage], "text": r.stage_notes.get(stage, "")})
        except Exception as e:
            r.status[stage] = "failed"
            r.error = f"{type(e).__name__}: {e}"
            r.emit({"type": "stage_end", "stage": stage, "status": "failed", "text": r.error})
        finally:
            r.busy = False
            r.save()

    # ------------------------------------------------------------- 1. skill
    def stage_extract_rules(self, _):
        r = self.r
        if r.mode == "live":
            skill = (r.ws / ".claude/skills/extract-rules/SKILL.md").read_text(encoding="utf-8")
            body = re.sub(r"^---.*?---\n", "", skill, flags=re.S)
            md = r.ws / ".scratch/main-session.md"
            md.write_text("---\nname: main\ntools: Read, Write, Edit, Glob, Grep, Bash\n---\n"
                          "You are the main session for this project. The auditor typed /extract-rules. "
                          "The skill's instructions follow; carry them out exactly, in this context.\n\n" + body, encoding="utf-8")
            a = r.make_agent(md, self.client)
            final = a.run("/extract-rules\n\n(outputs/rules.json does not exist yet; there is nothing to overwrite.)")
            r.emit({"type": "report", "agent": "main", "text": final})
        else:
            self.replay("extract_rules")
        code, out = r.sh(r.py(".claude/skills/extract-rules/verify_quotes.py", "outputs/rules.json", "data/contract-rules.pdf"),
                         "verify_quotes.py: every quote on its stated PDF page")
        if code != 0:
            raise RuntimeError("rules.json failed verification")
        r.stage_notes["extract_rules"] = out.splitlines()[-1]

    # ------------------------------------------------------------- 2. sub-agents in parallel
    def stage_analysts(self, _):
        r = self.r
        if r.mode == "live":
            jobs = {"spend-analyst": "Run the spend-analyst: analyse the full spend population against outputs/rules.json "
                                     "and data/contracts.csv as your instructions describe, then report.",
                    "findings-analyst": "Run the findings-analyst: read the committee papers and write outputs/history.json "
                                        "as your instructions describe, then report."}
            errors, threads = {}, []

            def go(name, prompt):
                try:
                    a = r.make_agent(r.ws / f".claude/agents/{name}.md", self.client)
                    r.emit({"type": "report", "agent": name, "text": a.run(prompt)})
                except Exception as e:
                    errors[name] = f"{type(e).__name__}: {e}"
            for n, p in jobs.items():
                t = threading.Thread(target=go, args=(n, p), daemon=True); t.start(); threads.append(t)
            for t in threads:
                t.join()
            if errors:
                raise RuntimeError("; ".join(f"{k}: {v}" for k, v in errors.items()))
        else:
            self.replay("analysts")
        c1, o1 = r.sh(r.py("scripts/selfcheck.py"), "selfcheck.py: one item per test re-derived independently")
        c2, o2 = r.sh(r.py("scripts/verify_history.py", "outputs/history.json", "data/committee"),
                      "verify_history.py: every history quote on its stated page")
        if c1 or c2:
            raise RuntimeError("analyst outputs failed verification")
        r.stage_notes["analysts"] = f"{o1.splitlines()[-1]} · {o2.splitlines()[-1]}"

    # ------------------------------------------------------------- 3. risk-assessor
    def stage_risk(self, _):
        r = self.r
        if r.mode == "live":
            a = r.make_agent(r.ws / ".claude/agents/risk-assessor.md", self.client)
            r.emit({"type": "report", "agent": "risk-assessor", "text": a.run("Run the risk-assessor: build the risk register.")})
        else:
            self.replay("risk")
        code, out = r.sh(r.py(".claude/skills/risk-assessment/build_register.py"), "build_register.py: every rating cited and computed")
        if code != 0:
            raise RuntimeError("the register did not validate")
        r.stage_notes["risk"] = next((l for l in out.splitlines() if l.startswith("risks kept")), "")

    # ------------------------------------------------------------- 4. human gate + revision
    def stage_gate(self, payload):
        r = self.r
        decisions = payload.get("decisions") or {}
        reviewer = (payload.get("reviewer") or "").strip()
        if not reviewer or not decisions:
            raise RuntimeError("reviewer and decisions are required")
        write_decisions(r.ws / "outputs/auditor-comments.md", reviewer, decisions)
        r.fix_owner()
        r.emit({"type": "human", "agent": "auditor", "text": f"{reviewer} recorded {len(decisions)} decisions: " +
                ", ".join(f"{k} {v['decision']}" for k, v in decisions.items())})
        if r.mode == "live":
            a = r.make_agent(r.ws / ".claude/agents/risk-assessor.md", self.client, name="risk-assessor")
            a.messages, a.turns = [], 0
            r.emit({"type": "report", "agent": "risk-assessor", "text": a.run(
                "Run the risk-assessor again. Apply the decisions in outputs/auditor-comments.md and mark the register as a revision.")})
        else:
            replay_apply_decisions(r.ws, decisions, r.emit)
            r.fix_owner()
        code, out = r.sh(r.py(".claude/skills/risk-assessment/build_register.py"), "build_register.py: decisions applied, nothing else changed")
        if code != 0:
            raise RuntimeError("the revision did not validate")
        code, gate = r.sh(r.py(".claude/skills/audit-program/build_pack.py", "--gate"), "build_pack.py --gate")
        r.stage_notes["gate"] = gate.splitlines()[0] if gate else ""
        if code != 0:
            return "waiting"  # some risks undecided: the gate stays open
        return "done"

    # ------------------------------------------------------------- 5. agent team
    def stage_team(self, _):
        r = self.r
        code, gate = r.sh(r.py(".claude/skills/audit-program/build_pack.py", "--gate"), "lead: gate check")
        if code != 0:
            raise RuntimeError("gate not closed: " + gate)
        if r.mode == "live":
            Team(r, self.client, gate).run()
        else:
            self.replay("team")
        code, out = r.sh(r.py("scripts/checks/run_checks.py"), "run_checks.py: quotes · numbers · trace · samples")
        if r.mode != "live":
            write_review(r.ws, out)
            r.fix_owner()
        verdict = "READY FOR SIGN-OFF" if "VERDICT: READY FOR SIGN-OFF" in out else "BLOCKED"
        r.stage_notes["team"] = f"QA verdict: {verdict}"
        if verdict != "READY FOR SIGN-OFF":
            raise RuntimeError("QA verdict BLOCKED: the pack goes back to the team, not to the auditor")

    # ------------------------------------------------------------- 6. sign-off
    def stage_signoff(self, payload):
        r = self.r
        rv = r.ws / "outputs/review.md"
        text = rv.read_text(encoding="utf-8")
        if "READY FOR SIGN-OFF" not in text:
            raise RuntimeError("review.md does not show READY FOR SIGN-OFF")
        name = (payload.get("name") or "").strip()
        decision = payload.get("decision") or "sign off"
        if not name:
            raise RuntimeError("name is required")
        block = (f"## Auditor sign-off\n\nSigned off by: {name}\nDate: {datetime.date.today()}\n"
                 f"Decision (sign off / return to the team): {decision}\nComment: {(payload.get('comment') or '').strip()}\n")
        text = re.sub(r"## Auditor sign-off.*$", block, text, flags=re.S) if "## Auditor sign-off" in text else text + "\n" + block
        rv.write_text(text, encoding="utf-8")
        r.emit({"type": "human", "agent": "auditor", "text": f"{name}: {decision}"})
        r.stage_notes["signoff"] = f"{decision} by {name}"

    # ------------------------------------------------------------- replay
    def replay(self, stage: str):
        """Replay a recorded live run's judgments for this stage: its trajectory events, then its files."""
        r = self.r
        src = REPLAY / stage
        traj = src / "trajectory.jsonl"
        if traj.exists():
            for line in traj.read_text(encoding="utf-8").splitlines():
                if r.stop.is_set():
                    raise InterruptedError("run stopped")
                ev = json.loads(line)
                ev["replay"] = True
                r.emit(ev)
                time.sleep(REPLAY_DELAY)
        files = src / "files"
        if files.exists():
            for p in sorted(files.rglob("*")):
                if p.is_file():
                    dst = r.ws / p.relative_to(files)
                    dst.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, dst)
        r.fix_owner()
        cmds = src / "commands.json"
        if cmds.exists():
            for c in json.loads(cmds.read_text()):
                code, _ = r.sh(r.py(*c["args"]), c["label"])
                if code != 0 and c.get("must_pass", True):
                    raise RuntimeError(f"replayed step failed: {c['label']}")
        if stage == "team":
            replay_filter_plan(r.ws, r.emit)
            r.fix_owner()
            code, out = r.sh(r.py(".claude/skills/audit-program/build_pack.py"), "planner: build_pack.py (replayed plan, filtered to your approved scope)")
            if code != 0:
                raise RuntimeError("the replayed plan did not build for this scope")


# =============================================================================== agent team
class Team:
    NAMES = ["planner", "challenger", "qa-reviewer"]

    def __init__(self, run: Run, client, gate_text: str):
        self.r, self.client, self.gate = run, client, gate_text
        self.inbox = {n: queue.Queue() for n in self.NAMES}
        self.done = {"PLANNER DONE": False, "CHALLENGER DONE": False, "QA DONE": False}
        self.finished = threading.Event()
        self.idle = {n: False for n in self.NAMES}
        self.errors = {}
        self.lock = threading.Lock()

    def send(self, frm, to, msg):
        self.r.emit({"type": "message", "agent": frm, "to": to, "text": msg})
        if to == "lead":
            for k in self.done:
                if msg.strip().upper().startswith(k) or k in msg.upper().split("\n")[0]:
                    self.done[k] = True
            if all(self.done.values()):
                self.finished.set()
            return
        self.inbox[to].put((frm, msg))

    def kickoff(self, name):
        others = [n for n in self.NAMES if n != name]
        return (f"You are the teammate '{name}' on the Phase 3 agent team. Your teammates are {others[0]} and {others[1]}; "
                f"the lead is 'lead'. The auditor gate is closed:\n\n{self.gate}\n\n"
                "Message teammates with SendMessage, following the protocol in your instructions exactly "
                "(PACK READY vN, CHALLENGE #n, RESPONSE #n, QA vN: FAIL, and your DONE line to the lead). "
                "Messages from teammates arrive as new turns from the harness. "
                + ("Start now." if name == "planner" else "Wait for the planner's PACK READY v1, which arrives below."))

    def worker(self, name):
        r = self.r
        try:
            a = r.make_agent(r.ws / f".claude/agents/{name}.md", self.client, on_send=self.send)
            first = name == "planner"
            if first:
                a.run(self.kickoff(name))
            while not self.finished.is_set() and not r.stop.is_set():
                msgs = self._drain(name, wait=3.0)
                if not msgs:
                    continue
                text = "\n\n".join(f"Message from {f}:\n{m}" for f, m in msgs)
                if not first:
                    text = self.kickoff(name) + "\n\n" + text
                    first = True
                a.run(text)
        except Exception as e:
            self.errors[name] = f"{type(e).__name__}: {e}"
            r.emit({"type": "error", "agent": name, "text": self.errors[name]})
            self.finished.set()

    def _drain(self, name, wait):
        out = []
        try:
            out.append(self.inbox[name].get(timeout=wait))
            while True:
                out.append(self.inbox[name].get_nowait())
        except queue.Empty:
            pass
        with self.lock:
            self.idle[name] = not out
        return out

    def run(self):
        r = self.r
        r.emit({"type": "lead", "agent": "lead", "text": "spawning planner, challenger and qa-reviewer as teammates"})
        threads = [threading.Thread(target=self.worker, args=(n,), daemon=True) for n in self.NAMES]
        for t in threads:
            t.start()
        start, nudges, idle_since = time.time(), 0, None
        while not self.finished.is_set():
            time.sleep(5)
            if r.stop.is_set():
                break
            if time.time() - start > TEAM_TIMEOUT_S:
                self.errors["lead"] = "team timed out"
                break
            all_idle = all(self.idle.values()) and all(q.empty() for q in self.inbox.values())
            idle_since = (idle_since or time.time()) if all_idle else None
            if idle_since and time.time() - idle_since > 20:
                if nudges >= 3:
                    self.errors["lead"] = "team stalled: no messages and not every teammate reported DONE"
                    break
                nudges += 1
                missing = [k for k, v in self.done.items() if not v]
                for n in self.NAMES:
                    self.send("lead", n, f"Lead: the team is idle but these have not reported yet: {', '.join(missing)}. "
                                         "Continue your protocol: if you are waiting on a teammate, message them; if your part is "
                                         "finished, send your DONE line to the lead.")
                idle_since = None
        self.finished.set()
        for t in threads:
            t.join(timeout=30)
        r.emit({"type": "lead", "agent": "lead", "text": "team shut down: " + ", ".join(f"{k}={'yes' if v else 'no'}" for k, v in self.done.items())})
        if self.errors:
            raise RuntimeError("; ".join(f"{k}: {v}" for k, v in self.errors.items()))


# =============================================================================== shared helpers
def write_decisions(path: Path, reviewer: str, decisions: dict):
    """The human gate: write the auditor's decisions into the builder's template, nothing else."""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"^Reviewer:.*$", f"Reviewer: {reviewer}", text, count=1, flags=re.M)
    text = re.sub(r"^Date:.*$", f"Date: {datetime.date.today()}", text, count=1, flags=re.M)
    lines = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"R-\d+", cells[0]) and cells[0] in decisions:
            d = decisions[cells[0]]
            dec = d.get("decision", "").strip().lower()
            if dec not in ("approve", "amend", "reject", ""):
                raise ValueError(f"{cells[0]}: decision must be approve, amend or reject")
            comment = (d.get("comment") or "").replace("|", "/").replace("\n", " ").strip()
            if d.get("likelihood") or d.get("impact"):
                comment = (comment + f" (set likelihood {d.get('likelihood') or 'unchanged'}, impact {d.get('impact') or 'unchanged'})").strip()
            if dec in ("amend", "reject") and not comment:
                raise ValueError(f"{cells[0]}: amend and reject need a comment")
            cells[4], cells[5] = dec, comment
            line = "| " + " | ".join(cells[:6]) + " |"
        lines.append(line)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def replay_apply_decisions(ws: Path, decisions: dict, emit):
    """Replay-mode risk-assessor revision: apply the decisions mechanically (no model)."""
    p = ws / "outputs/risk-ratings.json"
    R = json.loads(p.read_text(encoding="utf-8"))
    state = json.loads((ws / "outputs/.register-state.json").read_text())
    rev = R.get("revision") or {"number": 0, "changed": []}
    changed = {c["id"]: c["change"] for c in rev.get("changed", [])}
    keep = []
    for risk in R["risks"]:
        d = decisions.get(risk["id"], {})
        dec = (d.get("decision") or "").lower()
        if dec == "reject":
            R.setdefault("excluded", []).append({"id": risk["id"], "theme": risk["title"],
                                                 "reason": f"rejected by the auditor at the gate: {d.get('comment', '').strip()}"})
            changed[risk["id"]] = "rejected"
            emit({"type": "tool_call", "agent": "risk-assessor", "tool": "Edit", "input": f"outputs/risk-ratings.json: move {risk['id']} to excluded", "replay": True})
            continue
        if dec == "amend" and risk.get("auditor_override"):
            keep.append(risk)  # already applied in an earlier revision; keep it as amended
            continue
        if dec == "amend":
            for part, key in (("likelihood", "likelihood"), ("impact", "impact")):
                v = d.get(key)
                if v:
                    risk[part]["score"] = int(v)
            risk["likelihood"]["justification"] = f"Auditor override: \"{d.get('comment', '').strip()}\" " + risk["likelihood"]["justification"]
            risk["auditor_override"] = True
            changed[risk["id"]] = "amended"
            emit({"type": "tool_call", "agent": "risk-assessor", "tool": "Edit", "input": f"outputs/risk-ratings.json: amend {risk['id']} as the auditor asked", "replay": True})
        keep.append(risk)
    R["risks"] = keep
    R["revision"] = {"number": state.get("revision", 0) + 1, "changed": [{"id": k, "change": v} for k, v in changed.items()]}
    p.write_text(json.dumps(R, indent=2, ensure_ascii=False), encoding="utf-8")


def replay_filter_plan(ws: Path, emit):
    """Replay-mode planner: keep the recorded plan's entries for the risks you approved;
    rules only those dropped entries cited are listed as not tested with that reason."""
    out = subprocess.run([str(ws / ".venv/bin/python"), ".claude/skills/audit-program/build_pack.py", "--gate"],
                         cwd=ws, capture_output=True, text=True, env=tool_env(), **as_sandbox()).stdout
    m = re.search(r"approved, in scope: (.*)", out)
    approved = set(re.findall(r"R-\d+", m.group(1))) if m else set()
    p = ws / "outputs/audit-plan.json"
    P = json.loads(p.read_text(encoding="utf-8"))
    dropped = [x for x in P["risks"] if x["id"] not in approved]
    P["risks"] = [x for x in P["risks"] if x["id"] in approved]
    missing = sorted(approved - {x["id"] for x in P["risks"]})
    if missing:
        raise RuntimeError(f"the recorded plan has no entry for {', '.join(missing)}; run in live mode to plan them")
    if dropped:
        ratings = json.loads((ws / "outputs/risk-ratings.json").read_text())
        cited = set(re.findall(r"rule:(CPR-\d+)", json.dumps(ratings["risks"]) + json.dumps(P["risks"])))
        listed = {x for g in P["rules_not_tested"] for x in g["rule_ids"]}
        orphan = sorted({x for r in dropped for x in re.findall(r"rule:(CPR-\d+)", json.dumps(r))} - cited - listed)
        if orphan:
            P["rules_not_tested"].append({"reason": "cited only by a risk the auditor did not approve for this audit", "rule_ids": orphan})
        emit({"type": "text", "agent": "planner", "replay": True,
              "text": f"Dropped plan entries for risks not approved at your gate: {', '.join(x['id'] for x in dropped)}."})
    p.write_text(json.dumps(P, indent=2, ensure_ascii=False), encoding="utf-8")


def write_review(ws: Path, check_output: str):
    """Replay-mode qa-reviewer: write review.md from the checks exactly as printed."""
    table = "\n".join(l for l in check_output.splitlines() if l.startswith("|"))
    verdict = next((l for l in check_output.splitlines() if l.startswith("VERDICT")), "VERDICT: BLOCKED")
    fails = [l.strip() for l in check_output.splitlines() if l.strip().startswith("FAIL")]
    text = (f"# QA review\n\nPack checked: replayed plan for this run's approved scope. Date: {datetime.date.today()}. "
            "Checks run with `.venv/bin/python scripts/checks/run_checks.py` by the harness.\n\n"
            f"{table}\n\n{verdict}\n\n" + ("## Failures\n\n" + "\n".join(f"- {f}" for f in fails) + "\n\n" if fails else "") +
            "## Auditor sign-off\n\nSigned off by:\nDate:\nDecision (sign off / return to the team):\nComment:\n")
    (ws / "outputs/review.md").write_text(text, encoding="utf-8")
