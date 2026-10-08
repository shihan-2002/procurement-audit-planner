"""The agent loop: one Claude conversation with sandboxed tools.

An Agent is built from a markdown definition (frontmatter: name, description,
tools; body: the system prompt), the same files Claude Code reads from
.claude/agents/. The project's CLAUDE.md and the agent's memory file are
added to the system prompt, as Claude Code does. The loop is a manual
tool-use loop over the Messages API (streamed, so long file writes do not
hit HTTP timeouts), appending every response unchanged so the conversation
stays append-only.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .hooks import Hooks, error_json
from .tools import TOOL_SPECS, Sandbox, ToolError, validate

MODEL = os.environ.get("HARNESS_MODEL", "claude-opus-5-5")
EFFORT = os.environ.get("HARNESS_EFFORT", "high")
MAX_TOKENS = int(os.environ.get("HARNESS_MAX_TOKENS", "64000"))
MAX_TURNS = int(os.environ.get("HARNESS_MAX_TURNS", "80"))
USE_FALLBACKS = os.environ.get("HARNESS_FALLBACKS", "1") == "1"
# $ per 1M tokens for the cost meter (input, output, cache read, cache write)
PRICES = {"claude-opus-5-5": (4.0, 20.0, 0.20, 5.0), "claude-sonnet-5-5": (2.0, 10.0, 0.20, 2.5),
          "claude-haiku-5-5": (0.10, 0.50, 0.01, 0.125), "claude-fable-5-1": (10.0, 50.0, 0.25, 12.5)}


class BudgetExceeded(Exception):
    pass


def parse_agent_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    if not m:
        return {"name": path.stem, "description": "", "tools": [], "body": text}
    meta = {}
    for line in m.group(1).splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip()] = v.strip()
    tools = [t.strip() for t in meta.get("tools", "").split(",") if t.strip()]
    return {"name": meta.get("name", path.stem), "description": meta.get("description", ""),
            "tools": tools, "memory": meta.get("memory"), "body": m.group(2)}


@dataclass
class Usage:
    input: int = 0
    output: int = 0
    cache_read: int = 0
    cache_write: int = 0

    def add(self, u) -> None:
        self.input += getattr(u, "input_tokens", 0) or 0
        self.output += getattr(u, "output_tokens", 0) or 0
        self.cache_read += getattr(u, "cache_read_input_tokens", 0) or 0
        self.cache_write += getattr(u, "cache_creation_input_tokens", 0) or 0

    def usd(self, model: str = MODEL) -> float:
        pi, po, pr, pw = PRICES.get(model, PRICES["claude-opus-5-5"])
        return (self.input * pi + self.output * po + self.cache_read * pr + self.cache_write * pw) / 1e6


@dataclass
class Agent:
    name: str
    system: str
    tools: list
    sandbox: Sandbox
    client: object
    emit: Callable[[dict], None]
    budget: Callable[[], None] = lambda: None
    on_send: Callable[[str, str, str], None] | None = None
    messages: list = field(default_factory=list)
    usage: Usage = field(default_factory=Usage)
    stop_flag: threading.Event = field(default_factory=threading.Event)
    turns: int = 0
    last_text: str = ""
    hooks: object = None

    # ---------------------------------------------------------------- build
    @classmethod
    def from_file(cls, agent_md: Path, workspace: Path, client, emit, extra_system: str = "", **kw) -> "Agent":
        spec = parse_agent_file(agent_md)
        tools = [t for t in spec["tools"] if t in TOOL_SPECS]
        if kw.get("on_send") and "SendMessage" not in tools:
            tools.append("SendMessage")  # teammates always get the team's messaging tool, as in Claude Code agent teams
        return cls(name=spec["name"], system=build_system(workspace, spec["name"], spec["body"], tools, extra_system),
                   tools=tools, sandbox=kw.pop("sandbox"), client=client, emit=emit, **kw)

    def tool_defs(self) -> list:
        return [TOOL_SPECS[t] for t in self.tools]

    # ---------------------------------------------------------------- loop
    def run(self, user_text: str) -> str:
        """Add a user turn and run until the model ends its turn. Returns the final text."""
        self.messages.append({"role": "user", "content": user_text})
        self.emit({"type": "agent_turn", "agent": self.name, "text": user_text[:2000]})
        while True:
            if self.stop_flag.is_set():
                raise InterruptedError("stopped")
            if self.turns >= MAX_TURNS:
                raise RuntimeError(f"{self.name}: exceeded {MAX_TURNS} model turns")
            self.budget()
            self.turns += 1
            resp = self._call()
            self.usage.add(resp.usage)
            self.messages.append({"role": "assistant", "content": resp.content})
            texts = [b.text for b in resp.content if b.type == "text" and b.text.strip()]
            for t in texts:
                self.emit({"type": "text", "agent": self.name, "text": t})
            if texts:
                self.last_text = texts[-1]
            self.emit({"type": "usage", "agent": self.name, "input": self.usage.input + self.usage.cache_read + self.usage.cache_write,
                       "output": self.usage.output, "usd": round(self.usage.usd(), 4),
                       "context": (resp.usage.input_tokens or 0) + (getattr(resp.usage, "cache_read_input_tokens", 0) or 0)
                                  + (getattr(resp.usage, "cache_creation_input_tokens", 0) or 0)})
            if resp.stop_reason == "refusal":
                raise RuntimeError(f"{self.name}: the model declined this request (stop_reason=refusal)")
            if resp.stop_reason == "pause_turn":
                self.messages.append({"role": "user", "content": "Continue."})
                continue
            uses = [b for b in resp.content if b.type == "tool_use"]
            if not uses:
                if resp.stop_reason == "max_tokens":
                    self.messages.append({"role": "user", "content": "Your reply hit the output limit. Continue from where you stopped."})
                    continue
                return self.last_text
            results = []
            for b in uses:
                if resp.stop_reason == "max_tokens":
                    results.append(self._err(b, "truncated_input", "Your tool call was cut off at the output limit and was not run.",
                                             retryable=True, hint="Write large files in smaller parts (Write a first part, then Edit to append)."))
                    continue
                results.append(self._exec(b))
            self.messages.append({"role": "user", "content": results})

    def _call(self):
        kw = dict(model=MODEL, max_tokens=MAX_TOKENS, system=[{"type": "text", "text": self.system}],
                  messages=self.messages, tools=self.tool_defs(), cache_control={"type": "ephemeral"},
                  thinking={"type": "adaptive"}, output_config={"effort": EFFORT})
        if USE_FALLBACKS:
            kw.update(betas=["server-side-fallback-2026-07-01"], fallbacks="default")
        delay = 5
        for attempt in range(4):
            try:
                with self.client.beta.messages.stream(**kw) as stream:
                    return stream.get_final_message()
            except ValueError as e:  # tool input JSON the SDK could not parse at all
                self.emit({"type": "warn", "agent": self.name, "text": f"unparseable tool input, retrying: {e}"})
                time.sleep(1)
            except Exception as e:  # rate limits and 5xx are retried by the SDK; surface anything else after a few tries
                import anthropic
                if isinstance(e, (anthropic.RateLimitError, anthropic.APIConnectionError, anthropic.InternalServerError)) and attempt < 3:
                    self.emit({"type": "warn", "agent": self.name, "text": f"{type(e).__name__}; retrying in {delay}s"})
                    time.sleep(delay); delay *= 2
                    continue
                raise
        raise RuntimeError(f"{self.name}: model call failed repeatedly")

    def _err(self, b, code, message, retryable=False, **extra):
        """Typed error result: the model sees a stable code and whether a retry can help, not prose."""
        content = error_json(code, message, retryable, **extra)
        self.emit({"type": "tool_error", "agent": self.name, "tool": b.name, "text": content})
        return {"type": "tool_result", "tool_use_id": b.id, "content": content, "is_error": True}

    def _exec(self, b) -> dict:
        args = b.input if isinstance(b.input, dict) else {}
        problem = validate(b.name, b.input)
        if b.name not in self.tools:
            return self._err(b, "tool_not_available", f"tool {b.name} is not available to {self.name}")
        if problem:
            return self._err(b, "invalid_input", problem, retryable=True, hint="Re-issue the call with input that matches the tool schema.")
        if self.hooks is None:
            self.hooks = Hooks(self.sandbox.root, self.name)
        blocked = self.hooks.pre_tool_use(b.name, args)          # PreToolUse: before anything runs
        if blocked:
            self.emit({"type": "hook", "agent": self.name, "tool": b.name, "text": f"PreToolUse blocked: {blocked['message']}"})
            return self._err(b, blocked["error"], blocked["message"], blocked["retryable"], hint=blocked.get("hint", ""))
        self.emit({"type": "tool_call", "agent": self.name, "tool": b.name, "input": summarize_input(b.name, args)})
        try:
            out = self.hooks.post_tool_use(b.name, args, self._dispatch(b.name, args))   # PostToolUse: normalise
            self.emit({"type": "tool_result", "agent": self.name, "tool": b.name, "text": out[:1500]})
            return {"type": "tool_result", "tool_use_id": b.id, "content": out}
        except ToolError as e:
            return self._err(b, e.code, str(e), e.retryable)
        except Exception as e:  # never crash the loop on a tool failure
            return self._err(b, "internal_error", f"{type(e).__name__}: {e}", retryable=True)

    def _dispatch(self, name, a) -> str:
        s = self.sandbox
        if name == "Read":
            return s.read(a["file_path"], a.get("offset", 1), a.get("limit", 2000))
        if name == "Write":
            return s.write(a["file_path"], a["content"])
        if name == "Edit":
            return s.edit(a["file_path"], a["old_string"], a["new_string"], a.get("replace_all", False))
        if name == "Glob":
            return s.glob(a["pattern"])
        if name == "Grep":
            return s.grep(a["pattern"], a.get("path", "."), a.get("glob"))
        if name == "Bash":
            return s.bash(a["command"], a.get("timeout", 600))
        if name == "SendMessage":
            if not self.on_send:
                raise ToolError("messaging is only available to agent-team members")
            self.on_send(self.name, a["to"], a["message"])
            return f"sent to {a['to']}"
        raise ToolError(f"unknown tool {name}")


def summarize_input(name, a) -> str:
    if name == "Write":
        return f"{a.get('file_path')} ({len(a.get('content', ''))} chars)"
    if name == "Edit":
        return f"{a.get('file_path')}"
    if name == "Bash":
        return a.get("command", "")[:400]
    if name == "SendMessage":
        return f"→ {a.get('to')}: {a.get('message', '')[:400]}"
    return json.dumps(a)[:300]


def build_system(workspace: Path, name: str, body: str, tools: list, extra: str = "") -> str:
    claude_md = (workspace / "CLAUDE.md").read_text(encoding="utf-8") if (workspace / "CLAUDE.md").exists() else ""
    mem_file = workspace / ".claude" / "agent-memory" / name / "MEMORY.md"
    memory = mem_file.read_text(encoding="utf-8") if mem_file.exists() else "(empty)"
    env = f"""# Harness environment

You are running inside the Procurement Audit Planner harness, a web
application that runs this project's skills and agents through the Claude
API. You are not in Claude Code, and no human is watching your turns; work
autonomously and finish the job.

- Project root: the current directory. Every path is relative to it.
- Your tools: {', '.join(tools)}.
- Python: `.venv/bin/python` (pandas, openpyxl, pypdf installed). `pdftotext` and `pdfinfo` are on the PATH.
- `<scratchpad>` in any instruction means `.scratch/` in the project root.
- Your persistent memory file is `.claude/agent-memory/{name}/MEMORY.md` (how-to lessons only, as your instructions say).
- `data/` is read-only. Write large files in parts if needed (Write the first part, then Edit to append).
- Keep the final report to the length your instructions ask for.
"""
    return (f"{body.strip()}\n\n{env}\n# Project instructions (CLAUDE.md)\n\n{claude_md}\n\n"
            f"# Your memory (MEMORY.md)\n\n{memory}\n{extra}")
