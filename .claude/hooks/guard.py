#!/usr/bin/env python3
"""PreToolUse guard: file ownership and read-only inputs, enforced rather than requested.

Claude Code passes the tool call on stdin. Inside a sub-agent the input carries
`agent_type` (the agent's name); in the main session it is absent. Policy lives in
policy.json next to this file, shared with the Part B harness.
  - data/ is read-only for everyone.
  - Sub-agents and teammates never write skills, agent definitions, hooks, the
    check scripts or the auditor's decision file, and write only the files they own.
  - Bash commands that delete recursively, reach the network, or write into data/ are denied.
Denies with permissionDecision "deny" and a reason the agent can act on.
"""
import fnmatch, json, os, re, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
POLICY = json.loads((HERE / "policy.json").read_text())
ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or HERE.parents[1]).resolve()


def match(rel, globs):
    return any(fnmatch.fnmatch(rel, g) or rel == g.rstrip("/*") for g in globs)


def rel_path(p):
    q = Path(p)
    q = (ROOT / q) if not q.is_absolute() else q
    try:
        return q.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return None


def check(tool, inp, agent):
    """Return a reason to deny, or None to allow."""
    if tool in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        rel = rel_path(inp.get("file_path") or inp.get("notebook_path") or "")
        if rel is None:
            return "writes outside the project folder are not allowed"
        if match(rel, POLICY["read_only"]):
            return f"{rel} is read-only input data"
        if agent:
            if match(rel, POLICY["everyone"]):
                return None
            if match(rel, POLICY["agents_never_write"]):
                return f"{agent} may not modify {rel}; it belongs to the project or to the auditor"
            owned = POLICY["owners"].get(agent)
            if owned is not None and not match(rel, owned):
                return f"{agent} owns only {', '.join(owned)}; {rel} belongs to another agent"
    if tool == "Bash":
        cmd = inp.get("command", "")
        for pat in POLICY["bash_deny"]:
            if re.search(pat, cmd):
                return f"command blocked by project policy ({pat})"
    return None


def main():
    d = json.load(sys.stdin)
    reason = check(d.get("tool_name", ""), d.get("tool_input") or {}, d.get("agent_type"))
    if reason:
        print(json.dumps({"hookSpecificOutput": {"hookEventName": "PreToolUse", "permissionDecision": "deny",
                                                 "permissionDecisionReason": f"Blocked by .claude/hooks/guard.py: {reason}"}}))
    sys.exit(0)


if __name__ == "__main__":
    main()
