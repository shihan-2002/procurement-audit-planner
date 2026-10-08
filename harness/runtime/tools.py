"""Sandboxed tools for harness agents.

Every path is resolved inside the run's workspace; nothing outside it can be
read or written. Bash runs an allowlist of commands with a scrubbed
environment (no API keys), a timeout, and, in the container, as an
unprivileged user so a script cannot read the server's environment.
"""
from __future__ import annotations

import fnmatch
import os
import re
import shlex
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MAX_OUT = 20_000
READ_LINES = 2_000
BASH_TIMEOUT = 600

ALLOWED_CMDS = {
    ".venv/bin/python", "python", "python3", "pdftotext", "pdfinfo", "ls", "head", "tail", "wc",
    "cat", "grep", "find", "mkdir", "cp", "echo", "which", "sed", "sort", "uniq", "cut", "diff", "test", "true",
}
FORBIDDEN = re.compile(r"`|\$\(|\$\{|\bsudo\b|\brm\b|\bcurl\b|\bwget\b|\bssh\b|\bnc\b|\benv\b|\bprintenv\b|/proc/|~|\.\./")


class ToolError(Exception):
    """A tool failure the model can act on: a stable code, a message, and whether retrying can help."""
    def __init__(self, message: str, code: str = "invalid_request", retryable: bool = False):
        super().__init__(message)
        self.code, self.retryable = code, retryable


@dataclass
class Sandbox:
    root: Path
    readonly: tuple = ("data/",)
    sandbox_user: str | None = None
    written: list = field(default_factory=list)

    def resolve(self, p: str, write: bool = False) -> Path:
        if not p:
            raise ToolError("empty path", "invalid_request")
        q = Path(p)
        q = (self.root / q).resolve() if not q.is_absolute() else q.resolve()
        root = self.root.resolve()
        if q != root and root not in q.parents:
            raise ToolError(f"path outside the workspace: {p}", "path_outside_workspace")
        rel = q.relative_to(root).as_posix()
        if write and any(rel == r.rstrip("/") or rel.startswith(r) for r in self.readonly):
            raise ToolError(f"{rel} is read-only input data", "read_only")
        if write and (rel.startswith(".venv") or rel == "CLAUDE.md"):
            raise ToolError(f"{rel} may not be modified", "read_only")
        return q

    def rel(self, q: Path) -> str:
        return q.resolve().relative_to(self.root.resolve()).as_posix()

    # ------------------------------------------------------------- file tools
    def read(self, path: str, offset: int = 1, limit: int = READ_LINES) -> str:
        q = self.resolve(path)
        if not q.exists():
            raise ToolError(f"file not found: {path}", "not_found")
        if q.is_dir():
            raise ToolError(f"{path} is a directory; use Glob or Bash ls", "is_directory")
        if q.suffix.lower() in (".pdf", ".xlsx", ".xls"):
            raise ToolError(f"{path} is binary; extract it with pdftotext or read it with pandas via Bash", "binary_file")
        lines = q.read_text(encoding="utf-8", errors="replace").splitlines()
        start = max(int(offset or 1), 1)
        chunk = lines[start - 1:start - 1 + int(limit or READ_LINES)]
        out = "\n".join(f"{i:6d}\t{l}" for i, l in enumerate(chunk, start))
        more = len(lines) - (start - 1 + len(chunk))
        if more > 0:
            out += f"\n... {more} more lines; call Read with offset={start + len(chunk)}"
        return out[:MAX_OUT * 3] or "(empty file)"

    def write(self, path: str, content: str) -> str:
        q = self.resolve(path, write=True)
        q.parent.mkdir(parents=True, exist_ok=True)
        q.write_text(content, encoding="utf-8")
        self._own(q)
        self.written.append(self.rel(q))
        return f"wrote {self.rel(q)} ({len(content.encode())} bytes)"

    def edit(self, path: str, old_string: str, new_string: str, replace_all: bool = False) -> str:
        q = self.resolve(path, write=True)
        if not q.exists():
            raise ToolError(f"file not found: {path}", "not_found")
        text = q.read_text(encoding="utf-8")
        n = text.count(old_string)
        if n == 0:
            raise ToolError("old_string not found in the file", "edit_no_match")
        if n > 1 and not replace_all:
            raise ToolError(f"old_string occurs {n} times; make it unique or set replace_all", "edit_ambiguous")
        q.write_text(text.replace(old_string, new_string) if replace_all else text.replace(old_string, new_string, 1), encoding="utf-8")
        self.written.append(self.rel(q))
        return f"edited {self.rel(q)} ({n if replace_all else 1} replacement(s))"

    def glob(self, pattern: str) -> str:
        root = self.root.resolve()
        hits = []
        for p in sorted(root.rglob("*")):
            r = p.relative_to(root).as_posix()
            if r.startswith((".venv", ".git", ".scratch/cache")):
                continue
            if fnmatch.fnmatch(r, pattern) or fnmatch.fnmatch(r, pattern.lstrip("./")):
                hits.append(r + ("/" if p.is_dir() else ""))
        return "\n".join(hits[:500]) or "(no matches)"

    def grep(self, pattern: str, path: str = ".", glob: str | None = None) -> str:
        base = self.resolve(path)
        try:
            rx = re.compile(pattern)
        except re.error as e:
            raise ToolError(f"invalid regex: {e}", "invalid_request")
        files = [base] if base.is_file() else [p for p in sorted(base.rglob("*")) if p.is_file()]
        out = []
        for f in files:
            r = self.rel(f)
            if r.startswith((".venv", ".git")) or f.suffix.lower() in (".pdf", ".xlsx"):
                continue
            if glob and not fnmatch.fnmatch(f.name, glob):
                continue
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").splitlines(), 1):
                    if rx.search(line):
                        out.append(f"{r}:{i}: {line[:300]}")
                        if len(out) >= 300:
                            return "\n".join(out) + "\n... (truncated at 300 matches)"
            except OSError:
                continue
        return "\n".join(out) or "(no matches)"

    # ------------------------------------------------------------- bash
    def check_command(self, command: str) -> None:
        if FORBIDDEN.search(command):
            raise ToolError("command uses a construct the harness does not allow (backticks, $(), rm, network tools, env, ~, ../, /proc)", "command_not_allowed")
        try:
            lex = shlex.shlex(command, posix=True, punctuation_chars=";&|<>")
            lex.whitespace_split = True
            all_toks = list(lex)
        except ValueError as e:
            raise ToolError(f"cannot parse command: {e}", "invalid_command")
        segments, cur = [], []
        for t in all_toks:
            if t in (";", "&&", "||", "|", "&"):
                segments.append(cur); cur = []
            else:
                cur.append(t)
        segments.append(cur)
        for toks in segments:
            toks = [t for t in toks if t not in (">", ">>", "<", "2>", "2>&1")]
            while toks and re.fullmatch(r"[A-Z_]+=\S*", toks[0]):
                if not toks[0].startswith(("PYTHONPATH=", "MPLBACKEND=")):
                    raise ToolError("only PYTHONPATH= or MPLBACKEND= may prefix a command", "command_not_allowed")
                toks = toks[1:]
            if not toks:
                continue
            cmd = toks[0]
            if cmd not in ALLOWED_CMDS:
                raise ToolError(f"'{cmd}' is not on the harness allowlist: {sorted(ALLOWED_CMDS)}", "command_not_allowed")
            for t in toks[1:]:
                if t.startswith("/") and not t.startswith("/dev/null"):
                    raise ToolError("absolute paths are not allowed; use paths relative to the project folder", "path_outside_workspace")
        for m in re.finditer(r">>?\s*([^\s|&;]+)", command):
            target = m.group(1)
            if target.startswith("&") or target == "/dev/null":
                continue
            self.resolve(target, write=True)

    def bash(self, command: str, timeout: int = BASH_TIMEOUT) -> str:
        self.check_command(command)
        env = {"PATH": os.environ.get("HARNESS_TOOL_PATH", os.environ.get("PATH", "/usr/bin:/bin")),
               "HOME": str(self.root / ".scratch"), "LANG": "C.UTF-8", "PYTHONIOENCODING": "utf-8",
               "MPLBACKEND": "Agg", "TMPDIR": str(self.root / ".scratch")}
        (self.root / ".scratch").mkdir(exist_ok=True)
        kw = {}
        if self.sandbox_user and hasattr(os, "geteuid") and os.geteuid() == 0:
            kw["user"] = self.sandbox_user
            kw["group"] = self.sandbox_user
        try:
            p = subprocess.run(command, shell=True, cwd=self.root, env=env, capture_output=True, text=True,
                               timeout=min(int(timeout or BASH_TIMEOUT), BASH_TIMEOUT), **kw)
        except subprocess.TimeoutExpired:
            raise ToolError(f"command timed out after {timeout}s", "timeout", retryable=True)
        out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr.strip() else "")
        if len(out) > MAX_OUT:
            out = out[:MAX_OUT // 2] + f"\n... [{len(out) - MAX_OUT} chars truncated] ...\n" + out[-MAX_OUT // 2:]
        return f"[exit {p.returncode}]\n{out}".rstrip()

    def _own(self, q: Path) -> None:
        if self.sandbox_user and hasattr(os, "geteuid") and os.geteuid() == 0:
            try:
                import pwd
                pw = pwd.getpwnam(self.sandbox_user)
                os.chown(q, pw.pw_uid, pw.pw_gid)
            except (KeyError, OSError):
                pass


# --------------------------------------------------------------------------- schemas
def _tool(name, desc, props, required):
    return {"name": name, "description": desc, "eager_input_streaming": True,
            "input_schema": {"type": "object", "properties": props, "required": required, "additionalProperties": False}}


TOOL_SPECS = {
    "Read": _tool("Read", "Read a text file in the project folder, with line numbers. Paths are relative to the project root.",
                  {"file_path": {"type": "string"}, "offset": {"type": "integer"}, "limit": {"type": "integer"}}, ["file_path"]),
    "Write": _tool("Write", "Create or overwrite a text file in the project folder with the full content given.",
                   {"file_path": {"type": "string"}, "content": {"type": "string"}}, ["file_path", "content"]),
    "Edit": _tool("Edit", "Replace an exact string in a file. old_string must be unique unless replace_all is true.",
                  {"file_path": {"type": "string"}, "old_string": {"type": "string"}, "new_string": {"type": "string"},
                   "replace_all": {"type": "boolean"}}, ["file_path", "old_string", "new_string"]),
    "Glob": _tool("Glob", "List project files matching a glob pattern such as 'outputs/*.json' or '**/*.md'.",
                  {"pattern": {"type": "string"}}, ["pattern"]),
    "Grep": _tool("Grep", "Search text files for a regular expression; returns file:line: text.",
                  {"pattern": {"type": "string"}, "path": {"type": "string"}, "glob": {"type": "string"}}, ["pattern"]),
    "Bash": _tool("Bash", "Run a shell command in the project root. Allowed commands: .venv/bin/python, python3, pdftotext, pdfinfo, "
                          "ls, head, tail, wc, cat, grep, find, mkdir, cp, echo, which, sed, sort, uniq, cut, diff. Pipes and && are allowed; "
                          "no network, no rm, no absolute paths. Use .scratch/ for working files.",
                  {"command": {"type": "string"}, "timeout": {"type": "integer"}}, ["command"]),
    "SendMessage": _tool("SendMessage", "Send a short message to a teammate (planner, challenger, qa-reviewer) or to the lead.",
                         {"to": {"type": "string", "enum": ["planner", "challenger", "qa-reviewer", "lead"]},
                          "message": {"type": "string"}}, ["to", "message"]),
}


def validate(name: str, args) -> str | None:
    """Return an error string if args do not satisfy the tool schema (eager streaming skips server validation)."""
    spec = TOOL_SPECS.get(name)
    if spec is None:
        return f"unknown tool {name}"
    if not isinstance(args, dict):
        return "tool input is not a JSON object"
    schema = spec["input_schema"]
    for r in schema["required"]:
        if r not in args:
            return f"missing required field '{r}'"
    for k, v in args.items():
        if k not in schema["properties"]:
            return f"unexpected field '{k}'"
        t = schema["properties"][k].get("type")
        ok = {"string": isinstance(v, str), "integer": isinstance(v, int) and not isinstance(v, bool),
              "boolean": isinstance(v, bool)}.get(t, True)
        if not ok:
            return f"field '{k}' must be {t}"
        enum = schema["properties"][k].get("enum")
        if enum and v not in enum:
            return f"field '{k}' must be one of {enum}"
    return None
