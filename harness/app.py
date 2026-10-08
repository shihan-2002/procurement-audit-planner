"""Procurement Audit Planner harness: the web server.

Run locally:  .venv/bin/uvicorn harness.app:app --port 8000
Container:    see Dockerfile (serves the UI and the API on $PORT).

The API key lives only in this process's environment (ANTHROPIC_API_KEY). It is
never sent to the browser, never written to a run workspace, and stripped from the
environment of every script an agent runs.
"""
from __future__ import annotations

import asyncio
import datetime
import io
import json
import os
import re
import secrets
import threading
import zipfile
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse

from .runtime.agent import EFFORT, MODEL
from .runtime.orchestrator import MAX_RUN_USD, ROOT, RUNS, STAGES, Orchestrator, Run

WEB = Path(__file__).resolve().parent / "web"
PASSCODE = os.environ.get("HARNESS_PASSCODE", "")
MAX_LIVE_PER_DAY = int(os.environ.get("HARNESS_MAX_LIVE_RUNS_PER_DAY", "5"))

app = FastAPI(title="Procurement Audit Planner harness", docs_url=None, redoc_url=None)
RUNS.mkdir(parents=True, exist_ok=True)
_runs: dict[str, Run] = {}
_lock = threading.Lock()
_live_count = {"day": "", "n": 0}


def client():
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        return None
    import anthropic
    return anthropic.Anthropic(max_retries=4, timeout=900.0)


_client = client()


def get_run(run_id: str) -> Run:
    if not re.fullmatch(r"[\w-]{6,64}", run_id):
        raise HTTPException(404, "no such run")
    with _lock:
        r = _runs.get(run_id)
        if r is None and (RUNS / run_id / "run.json").exists():
            r = load_run(run_id)
            _runs[run_id] = r
    if r is None:
        raise HTTPException(404, "no such run")
    return r


def load_run(run_id: str) -> Run:
    meta = json.loads((RUNS / run_id / "run.json").read_text())
    r = Run(meta["mode"], run_id)
    r.created = meta.get("created", r.created)
    for s in meta.get("stages", []):
        st = s["status"]
        r.status[s["id"]] = "failed" if st == "running" else st
        r.stage_notes[s["id"]] = s.get("note", "")
    ev = RUNS / run_id / "events.jsonl"
    if ev.exists():
        r.events = [json.loads(l) for l in ev.read_text(encoding="utf-8").splitlines() if l.strip()]
    return r


@app.get("/", response_class=HTMLResponse)
def index():
    return FileResponse(WEB / "index.html")


@app.get("/healthz")
def healthz():
    return {"ok": True}


@app.get("/api/config")
def config():
    return {"live_available": _client is not None, "passcode_required": bool(PASSCODE), "model": MODEL, "effort": EFFORT,
            "usd_cap": MAX_RUN_USD, "max_live_runs_per_day": MAX_LIVE_PER_DAY, "stages": STAGES}


@app.get("/api/project")
def project():
    """The skills and agents this harness runs: the Part A files, read from disk."""
    items = []
    for p in sorted((ROOT / ".claude/skills").glob("*/SKILL.md")):
        items.append({"kind": "skill", "name": p.parent.name, "path": p.relative_to(ROOT).as_posix(),
                      "files": sorted(x.name for x in p.parent.iterdir() if x.is_file())})
    for p in sorted((ROOT / ".claude/agents").glob("*.md")):
        head = p.read_text(encoding="utf-8").split("---")[1] if p.read_text(encoding="utf-8").startswith("---") else ""
        tools = re.search(r"^tools:\s*(.*)$", head, re.M)
        items.append({"kind": "agent", "name": p.stem, "path": p.relative_to(ROOT).as_posix(),
                      "tools": tools.group(1) if tools else ""})
    return {"items": items}


@app.get("/api/project/file")
def project_file(path: str):
    allowed = path == "CLAUDE.md" or re.fullmatch(r"\.claude/(skills/[\w-]+/[\w.-]+|agents/[\w-]+\.md)", path)
    p = (ROOT / path).resolve()
    if not allowed or not p.is_file():
        raise HTTPException(404, "not found")
    return {"path": path, "text": p.read_text(encoding="utf-8")}


@app.get("/api/runs")
def list_runs():
    out = []
    for d in sorted(RUNS.glob("*/run.json"), reverse=True)[:20]:
        try:
            m = json.loads(d.read_text())
            out.append({"id": m["id"], "mode": m["mode"], "created": m["created"],
                        "done": sum(1 for s in m["stages"] if s["status"] == "done"), "stages": len(m["stages"])})
        except (OSError, KeyError, json.JSONDecodeError):
            continue
    return {"runs": out}


@app.post("/api/runs")
async def create_run(req: Request):
    body = await req.json()
    mode = body.get("mode", "replay")
    if mode not in ("live", "replay"):
        raise HTTPException(400, "mode must be live or replay")
    if mode == "live":
        if _client is None:
            raise HTTPException(400, "live mode is not configured on this server (no API key); use replay")
        if PASSCODE and not secrets.compare_digest(str(body.get("passcode", "")), PASSCODE):
            raise HTTPException(403, "wrong passcode for live mode")
        today = datetime.date.today().isoformat()
        with _lock:
            if _live_count["day"] != today:
                _live_count.update(day=today, n=0)
            if _live_count["n"] >= MAX_LIVE_PER_DAY:
                raise HTTPException(429, "today's live-run limit is reached; try replay mode")
            if any(r.mode == "live" and r.busy for r in _runs.values()):
                raise HTTPException(409, "another live run is in progress")
            _live_count["n"] += 1
    r = Run(mode)
    await asyncio.to_thread(r.create_workspace)
    with _lock:
        _runs[r.id] = r
    return r.state()


@app.get("/api/runs/{run_id}")
def run_state(run_id: str):
    return get_run(run_id).state()


@app.post("/api/runs/{run_id}/stages/{stage}")
async def start_stage(run_id: str, stage: str, req: Request):
    r = get_run(run_id)
    if stage not in [s["id"] for s in STAGES]:
        raise HTTPException(404, "no such stage")
    try:
        payload = await req.json()
    except Exception:
        payload = {}
    if r.mode == "live" and stage != "signoff":
        if PASSCODE and not secrets.compare_digest(str(payload.get("passcode", "")), PASSCODE):
            raise HTTPException(403, "wrong passcode for live mode")
    try:
        Orchestrator(r, _client if r.mode == "live" else None).start(stage, payload)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(409, str(e))
    return r.state()


@app.post("/api/runs/{run_id}/stop")
def stop(run_id: str):
    r = get_run(run_id)
    r.stop.set()
    return {"stopping": True}


@app.get("/api/runs/{run_id}/events")
async def events(run_id: str, request: Request, after: int = -1):
    r = get_run(run_id)

    async def gen():
        i = after + 1
        idle = 0
        while True:
            if await request.is_disconnected():
                return
            batch = r.events[i:]
            if batch:
                for ev in batch:
                    yield f"id: {ev['seq']}\ndata: {json.dumps(ev, default=str)}\n\n"
                i += len(batch)
                yield f"event: state\ndata: {json.dumps(r.state(), default=str)}\n\n"
                idle = 0
            else:
                idle += 1
                if idle % 30 == 0:
                    yield ": keep-alive\n\n"
                await asyncio.sleep(0.5)

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/api/runs/{run_id}/file")
def run_file(run_id: str, path: str):
    r = get_run(run_id)
    if not path.startswith("outputs/") or ".." in path:
        raise HTTPException(404, "only outputs/ can be read")
    try:
        text = r.file(path)
    except FileNotFoundError:
        raise HTTPException(404, "not found")
    return {"path": path, "text": text[:2_000_000]}


@app.get("/api/runs/{run_id}/gate")
def gate_data(run_id: str):
    """The register's summary rows and the decisions already recorded, for the gate form."""
    r = get_run(run_id)
    try:
        reg = r.file("outputs/risk-register.md")
        com = r.file("outputs/auditor-comments.md")
    except FileNotFoundError:
        raise HTTPException(409, "the register does not exist yet")
    rows, in_sum = [], False
    for line in reg.splitlines():
        if line.startswith("## "):
            in_sum = line.strip() == "## Summary"
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if in_sum and len(c) >= 9 and re.fullmatch(r"R-\d+", c[0]):
            rows.append({"id": c[0], "title": c[1], "L": c[2], "I": c[3], "score": c[4], "label": c[5], "band": c[6], "scope": c[8]})
    dec = {}
    for line in com.splitlines():
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 6 and re.fullmatch(r"R-\d+", c[0]):
            dec[c[0]] = {"decision": c[4], "comment": c[5]}
    head = reg.split("## Summary")[0]
    return {"rows": rows, "decisions": dec, "header": head}


@app.get("/api/runs/{run_id}/download")
def download(run_id: str):
    r = get_run(run_id)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted((r.ws / "outputs").rglob("*")):
            if p.is_file() and "analytics-full" not in p.parts:
                z.write(p, f"{r.id}/{p.relative_to(r.ws).as_posix()}")
        if (r.dir / "events.jsonl").exists():
            z.write(r.dir / "events.jsonl", f"{r.id}/trajectory/events.jsonl")
    buf.seek(0)
    return StreamingResponse(buf, media_type="application/zip",
                             headers={"Content-Disposition": f"attachment; filename=audit-pack-{r.id}.zip"})


@app.exception_handler(Exception)
async def unhandled(request: Request, exc: Exception):
    return JSONResponse({"detail": f"{type(exc).__name__}: {exc}"}, status_code=500)
