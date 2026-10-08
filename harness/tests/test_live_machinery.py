"""Offline tests for the live-mode machinery: the agent loop, tools, sandbox and team mailbox.

A scripted fake client stands in for the Claude API, so these run without a key:
    .venv/bin/python -m harness.tests.test_live_machinery
"""
import itertools
import json
import shutil
import tempfile
import threading
from pathlib import Path
from types import SimpleNamespace as NS

from harness.runtime import orchestrator as orch
from harness.runtime.agent import Agent
from harness.runtime.tools import Sandbox, ToolError

_ids = itertools.count()


def tool_use(name, **inp):
    return NS(type="tool_use", id=f"tu_{next(_ids)}", name=name, input=inp)


def text(t):
    return NS(type="text", text=t)


def msg(*content, stop="tool_use"):
    return NS(content=list(content), stop_reason=stop,
              usage=NS(input_tokens=1000, output_tokens=200, cache_read_input_tokens=0, cache_creation_input_tokens=0))


class FakeClient:
    """Returns scripted responses per agent (keyed by the first line of the system prompt's role)."""
    def __init__(self, scripts):
        self.scripts = {k: iter(v) for k, v in scripts.items()}
        self.calls = []
        self.lock = threading.Lock()
        self.beta = NS(messages=NS(stream=self._stream))

    def _stream(self, **kw):
        sysp = kw["system"][0]["text"]
        key = next(k for k in self.scripts if k in sysp[:400])
        with self.lock:
            self.calls.append((key, kw))
            resp = next(self.scripts[key])
        return NS(__enter__=lambda *a: NS(get_final_message=lambda: resp), __exit__=lambda *a: False)


class CM:
    def __init__(self, resp): self.resp = resp
    def __enter__(self): return NS(get_final_message=lambda: self.resp)
    def __exit__(self, *a): return False


def patch_stream(fc):
    def stream(**kw):
        sysp = kw["system"][0]["text"]
        key = next(k for k in fc.scripts if k in sysp[:400])
        with fc.lock:
            fc.calls.append((key, kw))
            return CM(next(fc.scripts[key]))
    fc.beta = NS(messages=NS(stream=stream))
    return fc


def test_sandbox(ws):
    sb = Sandbox(root=ws)
    for bad, why in [("../x.txt", "outside"), ("data/contract-rules.pdf", "read-only")]:
        try:
            sb.write(bad, "x"); raise AssertionError(f"write to {bad} was allowed")
        except ToolError as e:
            assert why in str(e), e
    for cmd in ["rm -rf outputs", "curl http://example.com", "cat /etc/passwd", "python3 -c 'import os' > ../x", "env", "echo $(whoami)"]:
        try:
            sb.bash(cmd); raise AssertionError(f"command allowed: {cmd}")
        except ToolError:
            pass
    out = sb.bash(".venv/bin/python -c \"import os; print('KEY' in str(os.environ.get('ANTHROPIC_API_KEY')))\"")
    assert out.endswith("False"), out
    assert "[exit 0]" in sb.bash("pdfinfo data/contract-rules.pdf | head -3")
    print("sandbox: path guards, read-only data, command allowlist and key scrubbing OK")


def test_agent_loop(ws):
    fc = patch_stream(FakeClient({"You are the spend analyst": [
        msg(text("Writing a file and running it."), tool_use("Write", file_path=".scratch/hello.py", content="print(6*7)")),
        msg(tool_use("Bash", command=".venv/bin/python .scratch/hello.py"), tool_use("Read", file_path="nope.txt")),
        msg(tool_use("Write", file_path="x.txt")),                       # invalid input: missing content
        msg(text("Done: 42."), stop="end_turn"),
    ]}))
    events = []
    a = Agent.from_file(ws / ".claude/agents/spend-analyst.md", ws, fc, events.append, sandbox=Sandbox(root=ws))
    assert a.tools == ["Bash", "Read", "Write", "Edit", "Glob", "Grep"], a.tools
    final = a.run("Run the spend-analyst.")
    assert final == "Done: 42.", final
    results = [b for m in a.messages if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"]]
    assert "42" in results[1]["content"] and results[2]["is_error"] and results[3]["is_error"], results
    sysp = fc.calls[0][1]["system"][0]["text"]
    assert "CLAUDE.md" in sysp and "Harness environment" in sysp and "agent-memory/spend-analyst" in sysp
    kw = fc.calls[0][1]
    assert kw["model"] == "claude-opus-5-5" and kw["thinking"] == {"type": "adaptive"} and kw["fallbacks"] == "default"
    assert all(t["eager_input_streaming"] for t in kw["tools"])
    print(f"agent loop: {len(fc.calls)} model calls, parallel tool results, schema rejection, error results OK")


def test_team(ws):
    run = orch.Run("live", "test-team-" + next(iter([str(next(_ids))])))
    run.dir = ws.parent / "teamrun"; run.dir.mkdir(exist_ok=True); run.ws = ws
    fc = patch_stream(FakeClient({
        "You are the planner": [
            msg(tool_use("SendMessage", to="challenger", message="PACK READY v1"), tool_use("SendMessage", to="qa-reviewer", message="PACK READY v1")),
            msg(text("waiting"), stop="end_turn"),
            msg(tool_use("SendMessage", to="challenger", message="RESPONSE #1: accepted")),
            msg(tool_use("SendMessage", to="qa-reviewer", message="PACK READY v2"), tool_use("SendMessage", to="challenger", message="PACK READY v2")),
            msg(tool_use("SendMessage", to="lead", message="PLANNER DONE v2")),
            msg(text("done"), stop="end_turn"),
        ] + [msg(text("idle"), stop="end_turn")] * 5,
        "You are the challenger": [
            msg(tool_use("SendMessage", to="planner", message="CHALLENGE #1 [sample] R-02: thin. Evidence: T-02.1. Ask: more.")),
            msg(text("waiting for v2"), stop="end_turn"),
            msg(tool_use("SendMessage", to="lead", message="CHALLENGER DONE · 1 resolved")),
            msg(text("done"), stop="end_turn"),
        ] + [msg(text("idle"), stop="end_turn")] * 5,
        "You are the qa-reviewer": [
            msg(text("v1 checked; waiting"), stop="end_turn"),
            msg(tool_use("SendMessage", to="lead", message="QA DONE: READY FOR SIGN-OFF")),
            msg(text("done"), stop="end_turn"),
        ] + [msg(text("idle"), stop="end_turn")] * 5,
    }))
    t = orch.Team(run, fc, "gate closed: test")
    t.run()
    assert all(t.done.values()), t.done
    msgs = [e for e in run.events if e["type"] == "message"]
    print(f"team: {len(msgs)} messages routed, all three DONE lines reached the lead, shut down cleanly")


def main():
    tmp = Path(tempfile.mkdtemp())
    try:
        orch.RUNS = tmp / "runs"
        r = orch.Run("live", "machinery-test")
        r.create_workspace()
        test_sandbox(r.ws)
        test_agent_loop(r.ws)
        test_team(r.ws)
        print("ALL MACHINERY TESTS PASSED")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
