# Procurement Audit Planner: Skills, Sub-agents, Human Gates and an Agent Team

This project builds an agent system that plans an internal audit of West Berkshire Council's procurement from its public data. It follows the step-by-step guide at [procurement-audit-planner.vercel.app](https://procurement-audit-planner.vercel.app/).

- **Part A** is the Claude Code project: `CLAUDE.md`, three skills, six agents, the project's scripts, and the outputs of a full run.
- **Part B** is `harness/`, an independent agent harness. It runs the same skills and agents through the Claude API from a deployable web app, with no dependency on Claude Code or a local machine.

The data is public, but it is real. Every output describes **risk indicators to investigate, never findings of wrongdoing**.

---

## Part A: Skills and agents

### The flow

```
contract-rules.pdf ──/extract-rules (SKILL, main context)──▶ rules.json
                                   │
          ┌────────────────────────┴────────────────────────┐
  spend-analyst (SUB-AGENT)                      findings-analyst (SUB-AGENT)
  spend xlsx + contracts.csv → Python            committee PDFs → sourced record
          │  analytics.json                               │  history.json
          └────────────────────────┬────────────────────────┘
              risk-assessor (SUB-AGENT, loads the risk-assessment SKILL)
                                   │  risk-register.md + auditor-comments.md
                     HUMAN GATE: approve / amend / reject each risk
                                   │  register revision
         AGENT TEAM: planner ⇄ challenger ⇄ qa-reviewer (uses the audit-program SKILL)
                                   │  planning-memo · risk-control-matrix · audit-program · challenges · review
                       HUMAN GATE: auditor sign-off in review.md
```

### Skills (`.claude/skills/`)

| Skill | Who runs it | What it does | Its script |
|---|---|---|---|
| `extract-rules` | You, with `/extract-rules`, in the main context | Turns the Contract Rules PDF into `outputs/rules.json`. Each testable rule has its clause, page, type, thresholds and a verbatim quote. Unstated thresholds go into null `parameters`, and every other clause is excluded with a reason. | `verify_quotes.py` checks the schema and sequential IDs, and that every quote is on its stated PDF page. |
| `risk-assessment` | Loaded by the `risk-assessor` sub-agent | The rating method: the council's own 5×5 scale, a likelihood rubric, the impact method, the repeat-finding uplift, and the rule that every rating cites evidence. The agent writes only its judgments, in `risk-ratings.json`. | `build_register.py` resolves every citation, fills every figure, computes scores and bands, and writes `risk-register.md` and `auditor-comments.md`. On a revision it refuses unapplied decisions and unrequested changes. |
| `audit-program` | Loaded by the `planner` teammate | Turns each approved risk into an expected control, a test step and a sample recipe, plus the list of documents to request from the council. The planner writes only `audit-plan.json`. | `build_pack.py` checks the gate, draws every sample from `analytics-full/`, verifies every transaction, accounts for every rule, and renders the three documents. |

### Agents (`.claude/agents/`)

| Agent | Kind | Tools | Owns | Job |
|---|---|---|---|---|
| `spend-analyst` | Sub-agent | Bash, Read, Write, Edit, Glob, Grep | `scripts/clean.py`, `analyse.py`, `selfcheck.py`, `common.py`; `analytics.json`; `analytics-full/` | Tests every payment over £500 against the thresholds in `rules.json`. Python computes every number. It runs 7 tests and every flagged row carries its workbook row ID. |
| `findings-analyst` | Sub-agent | Bash, Read, Write, Glob, Grep | `history.json` | Records audit opinions, gaps and discrepancies from the committee papers, plus the council's scoring method. It records and never judges, and `verify_history.py` checks every quote. |
| `risk-assessor` | Sub-agent | Bash, Read, Write, Edit, Glob, Grep | `risk-ratings.json` | Merges rules, analytics and history into rated risks using the risk-assessment skill. It re-runs after the gate to apply the auditor's decisions as a revision. |
| `planner` | Teammate | Bash, Read, Write, Edit, Glob, Grep (+ messages) | `audit-plan.json` | Plans the approved risks with the audit-program skill. It answers every challenge and QA failure, then rebuilds the pack. |
| `challenger` | Teammate | Read, Write, Glob, Grep (+ messages) | `challenges.md` | Sends evidence-cited challenges to the planner, at most two rounds. Points about ratings and scope are marked *for the auditor*. |
| `qa-reviewer` | Teammate | Bash, Read, Write, Glob, Grep (+ messages) | `review.md` | Runs `scripts/checks/run_checks.py` (quotes, numbers, trace, samples). It blocks sign-off until all four pass. |

### How they work together

- **Files are the interface.** Each stage writes files the next stage reads, and the agents never pass data in conversation. The JSON summaries hold counts and top-20 lists, and full lists stay in `analytics-full/`, so no context window holds a dataset.
- **The model judges; Python computes.** Every figure in the register and the pack is a `{{$.path}}` placeholder filled by a builder. Builders refuse typed figures, uncited ratings and untraceable samples.
- **Sub-agents isolate context.** Each analyst reads its own sources in its own window and returns a summary. The two analysts are independent and can run in parallel. The risk-assessor sees only the three summaries.
- **Skills make methods repeatable.** The same rating method and planning method apply on every run, and each skill ships with a script that enforces it.
- **Two human gates.** Nothing reaches the team until every risk has an auditor decision, which `build_pack.py --gate` enforces. Nothing is final until the auditor signs `review.md`, and only after QA reports READY FOR SIGN-OFF.
- **The team argues with itself.** The planner, challenger and QA reviewer message each other directly using the protocol `PACK READY vN`, `CHALLENGE #n`, `RESPONSE #n`, `QA vN: FAIL` and `… DONE`. The lead only routes and waits.
- **Memory holds how-to only.** `.claude/agent-memory/<agent>/MEMORY.md` records lessons such as format quirks and builder pitfalls. It never stores figures or findings.

### How the design maps to Module 2

| Module 2 idea | Where it shows up here |
|---|---|
| **Orchestrator + subagents.** The orchestrator coordinates and does not execute. | The lead (Claude Code's main session in Part A, `orchestrator.py` in Part B) decides what runs, launches it, relays reports and enforces the gates. It never rates a risk or drafts a test. |
| **Isolated context windows** | The spend-analyst reads ~10,600 payments and the findings-analyst reads 45 pages of committee papers, each in its own window. Only summaries return, and the risk-assessor sees three JSON summaries, never the raw data. |
| **Sequential where work depends** | rules → analytics → register → gate → pack. Each stage needs the previous stage's file. |
| **Parallel where it doesn't** | The spend-analyst and findings-analyst share no inputs, so they run at the same time. Wall-clock time is the slower of the two. |
| **Shared spec as the coordination layer** | `rules.json`, then the approved register, then `audit-plan.json`. The teammates never edit each other's files; they work from the same spec and talk only through the message protocol. |
| **Specialisation by function, not volume** | Extraction, spend analytics, document reading, rating, planning, challenge and QA are each one agent with clear inputs, outputs and a "Not this agent's job" section. |
| **Agents defined in `.claude/agents/`.** The file *is* the system prompt. | Six definitions, each with tools, owned files, an output contract and memory rules. Part B builds its agents directly from these files. |

The four failure modes from the lesson, and the design move that prevents each here:

| Failure mode | Design fix in this project |
|---|---|
| **Context leakage** | Minimal task briefs ("Run the spend-analyst."). Agents inspect data with aggregates only, full lists go to `analytics-full/`, and memory never carries evidence between runs. |
| **Coordination gaps** | Each file has exactly one owner. The builders refuse inputs that don't trace, for example a plan entry for a risk the auditor did not approve. The team's protocol messages name the pack version. |
| **Cascading failures** | Every stage ends with its own check (verifier, self-check, builder). A failed check stops that stage and reports; it does not pass a bad file downstream. A BLOCKED QA verdict sends the pack back to the team, never to the auditor. |
| **Prompt drift** | Prompts are written as acceptance criteria: exact schemas, citation rules, sample sizing by score, word limits, and scripts that reject anything vague, such as an uncited rating, a typed figure or a missing rule. |

Part B follows the three-layer architecture:
- **Frontend:** a single HTML page with no build step.
- **Backend:** FastAPI for runs, stages, gates, files and the event stream.
- **AI backend:** the Claude API, called by the harness's own agent loop.

In Module 1's terms, the model thinks and the harness does: tools, context, permissions, budgets and the run log.

### Results of the Part A run

| Output | Result |
|---|---|
| `rules.json` | 66 testable rules, 104 excluded clauses, 4 null statutory-threshold parameters; `ALL CHECKS PASSED` |
| `analytics.json` | 10,607 payments → 8,534 tested; 7 tests; self-check 7/7 matched |
| `history.json` | 20 audits, the council's 5×5 scoring method, 11 risk themes, 10 discrepancies; 74/74 quotes verified |
| `risk-register.md` | 10 risks (8 Medium-High, 2 Moderate); revision 2 after the gate |
| Gate | R-01 approve, R-09 amend (likelihood 3), R-10 reject, rest approved |
| Pack | 9 risks, 15 controls, 16 tests, 261 sampled transactions, 18 request items; 39 rules cited, 27 not tested with reasons |
| `challenges.md` | 8 challenges: 6 resolved, 1 declined, 1 for the auditor |
| `review.md` | quotes, numbers, trace and samples all PASS: **READY FOR SIGN-OFF**; signed off |

### Guide steps completed

Every step of the guide's five lessons was carried out in order. Each lesson is one commit, so the history shows the build step by step.

| Lesson | Steps | Evidence |
|---|---|---|
| Setup | 1.1 folder · 1.2 `CLAUDE.md` (verbatim from the guide) · 1.3 `data/` · 1.4 Python env, data checked against the brief · 1.5 folders | commit `d1d11f1` |
| 1 Skills | 2.1 build `extract-rules` (+ verifier tested on a planted-error fixture: 6/6 caught) · 2.2 run `/extract-rules` | commit `cb211d7` |
| 2 Sub-agents | 3.1 build spend-analyst · 3.2 run it · 3.3 build findings-analyst · 3.4 run and check it (planted-error fixture: 3/3 caught) · 3.5 build the risk-assessment skill (good/broken fixture) · 3.6 build risk-assessor · 3.7 run it, confirm no supplier names in risk text | commits `d7540da`, `0b4b56e`, `7e9ce27` |
| 3 Human gate | 4.1 open the template · 4.2 record decisions · 4.3 revise the register (revision 1) | commit `7f03160` |
| 4 Agent teams | 5.1 close the gate (revision 2) · 5.2 enable agent teams in `.claude/settings.json` · 5.3 audit-program skill · 5.4 planner · 5.5 challenger · 5.6 qa-reviewer and checks · 5.7 run the team (pack v1 → v3) · 5.8 sign off | commit `4d5a368` |

Where the guide offered "copy the finished file" or "ask Claude Code to write it", the guide's files were used for:

- `CLAUDE.md`
- the `extract-rules` skill and its verifier
- the six agent definitions
- the `audit-program` skill and `build_pack.py`
- `verify_history.py` and the four QA checks

Claude Code wrote these from the guide's prompts, fitted to the real data:

- the spend-analyst's scripts
- the risk-assessment skill and `build_register.py`
- `rules.json`, `history.json`, the ratings, the plan and the challenges

**How the run was executed.** The build ran in a single Claude Code session, which followed each skill and agent definition in turn and kept every agent's file ownership and message protocol. The definitions run as-is in Claude Code: `/extract-rules`, "Run the spend-analyst", and the agent-team prompt in step 5.7 with `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`. Part B runs them as genuinely separate agents with separate context windows and real team messaging.

### Run Part A yourself

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt   # needs poppler (pdftotext) on PATH
claude                                                                # then follow the guide's prompts
.venv/bin/python scripts/checks/run_checks.py                         # re-verify the committed pack
```

---

## Part B: The independent harness (`harness/`)

A web application that runs the Part A workflow end to end without Claude Code. It provides its own agent loop, tools, sandbox, orchestrator, human-gate UI and run log. Model calls go to the Claude API.

```
browser ──HTTP/SSE──▶ FastAPI (harness/app.py)
                         │
                   Orchestrator (harness/runtime/orchestrator.py)
                         │  stage 1 skill · stage 2 sub-agents in parallel · stage 3 sub-agent
                         │  stage 4 HUMAN gate form → revision · stage 5 agent team · stage 6 HUMAN sign-off
                         ▼
          Agent loop (harness/runtime/agent.py)  ── Claude API (claude-opus-5-5, adaptive thinking,
                         │                            prompt caching, refusal fallbacks, streaming)
                   Sandboxed tools (harness/runtime/tools.py)
                   Read · Write · Edit · Glob · Grep · Bash (allowlist) · SendMessage (team only)
                         ▼
          per-run workspace: copy of CLAUDE.md, data/, scripts/, .claude/  →  outputs/
```

- **Same files, different runtime.** Each agent is built from its `.claude/agents/*.md`: the frontmatter gives its name and tool list, and the body becomes its system prompt, with `CLAUDE.md` and its `MEMORY.md` appended as Claude Code would. The skills are read from `.claude/skills/`.
- **Agent loop.** It is a manual tool-use loop over the Messages API. Requests are streamed, with eager tool-input streaming and schema validation before any tool runs. It handles `max_tokens`, `pause_turn` and `refusal`, keeps the conversation append-only, and records token use and cost per agent.
- **Sub-agents** run in their own threads, each with its own context window. The spend-analyst and findings-analyst run in parallel.
- **Agent team.** Three teammates each have a mailbox, and `SendMessage` routes between them. Messages arrive as new turns. The lead stays out of the conversation: it watches for the three `DONE` lines, nudges a stalled team at most three times, and shuts the team down.
- **Deterministic checks.** After every stage the harness itself runs the project's verifiers and builders: `verify_quotes`, `selfcheck`, `verify_history`, `build_register`, `build_pack --gate` and `run_checks`. A stage that fails its check fails.
- **Human gates.** A form records approve, amend or reject for every risk into `auditor-comments.md`, and the gate stays open until every risk is decided. A second form records the sign-off into `review.md`, and only when QA says READY FOR SIGN-OFF.

### Safety and cost controls

- **The API key** lives only in the server's environment. It is never sent to the browser and never written to a workspace. It is stripped from the environment of every tool call. In the container every tool call runs as an unprivileged `sandbox` user, which cannot read the server's environment.
- **Paths:** tools can touch only the run's workspace, and `data/` is read-only.
- **Bash** runs an allowlist of commands. It refuses `rm`, network tools, `$()`, absolute paths, `../` and `/proc`.
- **Spend:** each run has a spend cap (`HARNESS_MAX_RUN_USD`, default $25). Only one live run happens at a time, with a daily live-run limit and an optional passcode (`HARNESS_PASSCODE`).

### Two modes

- **Live:** Claude makes every judgment. This needs `ANTHROPIC_API_KEY` and takes roughly 30 to 60 minutes per full run.
- **Replay:** this mode makes no API calls. It replays the recorded judgments of the Part A run: `rules.json`, `history.json`, the first ratings, the plan and the challenges.
  - The spend-analyst's scripts, every verifier, both builders and all four QA checks run for real on a fresh workspace.
  - Your gate decisions are applied for real. A rejection drops that risk from the replayed plan, and its rules are listed as not tested with that reason.

### Run locally

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements-harness.txt   # plus poppler: brew install poppler / apt install poppler-utils
export ANTHROPIC_API_KEY=...            # optional; without it only replay mode is offered
.venv/bin/uvicorn harness.app:app --port 8000
.venv/bin/python -m harness.tests.test_live_machinery   # offline tests of the loop, sandbox and team mailbox
```

### Deploy

The repository includes a `Dockerfile` (Python 3.12 + poppler) and a Render Blueprint (`render.yaml`):

1. Push this repository to GitHub.
2. In Render, choose **New → Blueprint** and select the repository.
3. Set `ANTHROPIC_API_KEY`, and optionally `HARNESS_PASSCODE`.
4. Deploy. The app serves the UI at `/` and a health check at `/healthz`.

Any Docker host works the same way (Fly.io, Railway, Cloud Run): build the image, set the environment variables, and expose `$PORT`.

### What was tested

- Two full replay runs through the HTTP API passed every stage with different gate decisions, and QA passed 4/4 both times.
- One replay run went through the UI.
- `harness/tests/test_live_machinery.py` checks the agent loop, tool validation, sandbox refusals, key scrubbing and team message routing against a scripted fake client.
- A live run against the real API and the Docker image build were not run on the build machine, which had no API key and no Docker.
