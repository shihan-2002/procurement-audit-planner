"""PreToolUse / PostToolUse hooks for the harness, the same policy Claude Code enforces.

The policy file is the project's own `.claude/hooks/policy.json`, so Part A (Claude
Code, via .claude/hooks/guard.py) and Part B (this harness) enforce one rule set:
read-only inputs, files each agent owns, and Bash commands nobody may run.
Prompts suggest; hooks enforce.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

MAX_RESULT = 20_000


def _load_guard(workspace: Path):
    """Import the project's guard.check so the harness and Claude Code share one implementation."""
    guard = workspace / ".claude" / "hooks" / "guard.py"
    if not guard.exists():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"guard_{abs(hash(str(workspace)))}", guard)
    mod = importlib.util.module_from_spec(spec)
    import os
    old = os.environ.get("CLAUDE_PROJECT_DIR")
    os.environ["CLAUDE_PROJECT_DIR"] = str(workspace)
    try:
        spec.loader.exec_module(mod)
    finally:
        if old is None:
            os.environ.pop("CLAUDE_PROJECT_DIR", None)
        else:
            os.environ["CLAUDE_PROJECT_DIR"] = old
    return mod


class Hooks:
    def __init__(self, workspace: Path, agent: str):
        self.agent = None if agent == "main" else agent
        self.guard = _load_guard(workspace)

    def pre_tool_use(self, tool: str, args: dict) -> dict | None:
        """Return a structured error to block the call, or None to allow it."""
        if self.guard is None:
            return None
        reason = self.guard.check(tool, args, self.agent)
        if reason:
            return {"error": "blocked_by_policy", "message": reason, "retryable": False,
                    "hint": "Write only the files you own; data/ is read-only; ask the lead if you need something else."}
        return None

    def post_tool_use(self, tool: str, args: dict, result: str) -> str:
        """Normalise every result before the model sees it: strip ANSI codes, cap the size."""
        result = re.sub(r"\x1b\[[0-9;]*m", "", result)
        if len(result) > MAX_RESULT:
            result = result[:MAX_RESULT // 2] + f"\n... [{len(result) - MAX_RESULT} chars trimmed by PostToolUse] ...\n" + result[-MAX_RESULT // 2:]
        return result


def error_json(code: str, message: str, retryable: bool = False, **extra) -> str:
    return json.dumps({"error": code, "message": message, "retryable": retryable, **extra})
