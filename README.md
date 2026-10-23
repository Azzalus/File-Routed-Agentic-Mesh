# note from creator

this shit is something i made for fun just to understand llm's. im not maintaining it or fixing reported issues. if you use it and theres issues or it destroys your computer, its your problem not mine.

# File-Routed Agentic Mesh (FRAM)

A GitHub-ready distribution of the FRAM workspace installer. This repo combines
two independent ways to bootstrap a complete File-Routed Agentic Mesh workspace:

| Delivery method | Folder | What you need |
|:---|:---|:---|
| **Method 1 — Python installer** | [`fram-python/`](fram-python/) | Python 3.8+ (standard library only, no packages) |
| **Method 2 — skill command** | [`fram-bootstrap/`](fram-bootstrap/) | Any agent harness with file read/write/copy tools — **no Python at all** |

Both methods produce the same FRAM workspace scaffold (identical file inventory):
`AGENTS.md`, `manifest.yaml`, `opencode.jsonc`, `.profiles/` persona prompts
(orchestrator, investigator, programmer), the `knowledge/` OKF catalog,
`system-start.py`, and the bundled `icm-okf-gates`, `grilling`, and `vocabulary`
skills.

**TL;DR:**
```bash
# Method 1 (Python)
mkdir fram-workspace
python fram-python\setup.py --target fram-workspace --non-interactive

# Method 2 (skill command)
#   install fram-bootstrap/ as a skill, then type /fram-bootstrap in your agent
```

Full install instructions, verification commands, and a first-use smoke task:
[INSTALL.md](INSTALL.md).

---

## Part 1 — What is FRAM?

File-Routed Agentic Mesh (FRAM) is a workspace architecture in which the folder
structure itself dictates agent identity, boundaries, and communication pipeline.
There is no orchestration code, no multi-agent framework, no deployment step. The
filesystem is the control surface: agents are routed by where they are and by which
files they are told to read.

FRAM is an implementation of Interpretable Context Methodology (ICM) folder
structure as agent architecture from:

> Van Clief, J., & McDermott, D., *Interpretable Context Methodology: Folder Structure
> as Agent Architecture*, arXiv:2603.16021v2.

ICM's core move is to replace framework-level orchestration with filesystem structure:
numbered stages, plain-text interfaces, and layered context loading, so that one
agent, reading the right files at the right moment, does what would otherwise require
a multi-agent framework. FRAM layers a **persona registry**, **OKF knowledge
entities**, and **deterministic verification gates** on top of that idea to produce a
self-contained, inspectable, human-in-the-loop workspace.

Core concepts:

- **Layer 0 — `AGENTS.md`** — workspace identity and hard rules; every agent and
  harness reads it first.
- **Layer 1 — `manifest.yaml` + `opencode.jsonc`** — declarative persona registry
  (roles, models, temperatures, permissions) + runtime binding that routes models to
  personas.
- **Layer 2 — `active-tasks/<task>/`** — `query.md` is the task contract;
  `BLACKBOARD.md` is shared memory; per-task `knowledge/`, `*-source/`, `*-output/`,
  `target-software/` hold the work.
- **Personas** — **Orchestrator** (plans, routes through the review gate, compiles the
  final answer; never writes source), **Investigator** (red-teams plans, flags risks,
  analyzes), **Programmer** (implements from an approved plan, builds, verifies). One
  model family can play all three; the folder structure decides which context each
  role sees.
- **Blackboard Protocol** — agents never talk directly; every intermediate finding is
  written to `BLACKBOARD.md` and consumed from there.
- **Sandbox Rule** — `shared-software/` and `target-software/` are **read-only**;
  agents may copy or read them, never modify them.
- **OKF knowledge** — schemas, invariants, relations, and constraints as JSON entities
  in `knowledge/`, referenced by id instead of pasted into prompts.
- **Deterministic gates** — no stage completes on model assertion; every stage ends
  with a deterministic command that returns exit code 0.
- **ICM traceability block** — before any build, the operator states **Observed
  State / Interpreted Gap / Proposed Logic Milestone / Verification Strategy**.

---

## Part 2 — Benefits and drawbacks

### Benefits

- **Portability** — a workspace is a folder: copy it, `git` it, zip it, email it
  (§3.4). No server to configure, no environment to replicate, no deployment step.
- **Inspectability** — every intermediate output is a readable plain-text file
  (§3.1). Open the folder and read the state; nothing is hidden (§5.3).
- **Editability** — anyone with a text editor can change prompts, context, and stage
  behavior; non-technical users have done so in practice without a developer (§4.5).
- **No framework overhead** — no orchestration code, no dependency graph of agent
  classes, no redeploy step (§1).
- **Human-in-the-loop** — review gates at every stage boundary; the human edits the
  previous stage's output before the next stage reads it (§3.3).
- **Model-agnostic** — the protocol is folder structure, file formats, and naming
  conventions; it works with opencode, Claude Code, Codex, or any harness that can
  read and write files (§4.1).
- **Low token cost** — layered context loading delivers only the context a stage
  needs (roughly 2k–8k focused tokens/stage instead of a 30k–50k monolithic window)
  (§3.2).
- **Self-documenting** — instructions and documentation are the same markdown files;
  a new reader can understand the whole pipeline without running it (§3.3).
- **Two install methods** — a Python installer for scripted, repeatable installs, and
  a skill command that needs no Python at all.

### Drawbacks

- **Sequential by design** — stages run one after another; there is no concurrent
  execution (Table 1).
- **No programmatic conditional branching** — the human decides between stages;
  automated branching would require scripting that turns FRAM into a framework (Table
  1, §5.2).
- **No built-in retry/fallback/error recovery** — a failed stage is re-run manually
  (Table 1).
- **External service integration requires local scripts or MCP connections** — there
  is no framework-level adapters layer (Table 1).
- **Not suited for complex concurrent multi-agent systems** that need framework-level
  coordination, real-time message passing, or high-concurrency server infra (§5.2).
- **Method 2 ships static config skeletons** — the skill writes placeholder model
  names; you must edit `manifest.yaml` and `opencode.jsonc` after install.

---

## Part 3 — Installing a FRAM workspace

Full instructions for both methods — prerequisites, flags, verification commands,
and the first-use smoke task — live in **[INSTALL.md](INSTALL.md)**. Quick start:

1. **Choose a method** — Python installer (`fram-python/`) or skill command
   (`fram-bootstrap/`); both produce the same scaffold, including the bundled
   `icm-okf-gates`, `grilling`, and `vocabulary` skills.
2. **Method 1 (Python):** create the target, then run the installer from the
   repository root:
   ```bash
   mkdir fram-workspace
   python fram-python\setup.py --target fram-workspace --non-interactive
   ```
3. **Method 2 (skill):** copy `fram-bootstrap/` into your harness's skills directory
   (global) or into the project's `.agents/skills/` (per-project), then type
   `/fram-bootstrap` and name the target directory (for example `fram-workspace`).
4. **Configure:** edit `manifest.yaml` (set `project_name` and replace each
   `<your-<persona>-model>` placeholder) and `opencode.jsonc` (provider `baseURL`,
   model placeholders, top-level `"model"` default).
5. **Verify** (from the workspace root):
   `python .agents\skills\icm-okf-gates\scripts\icm_okf_coupler.py --mode self-check`
   must return exit code 0.
6. **Boot** (from the workspace root):
   `uv run --with pyyaml python system-start.py`.
7. **Create your first task:** `active-tasks/<task-name>/query.md`, then start your
   harness in the workspace root.

For the method comparison table, troubleshooting, bundled-skills table, and the
non-destructive overwrite behavior, see [INSTALL.md](INSTALL.md).

---

## Repository layout

```
File-Routed-Agentic-Mesh/
├── README.md                     This file
├── INSTALL.md                    Install instructions for both methods
├── LICENSE                       MIT license
├── .gitignore                    Standard ignores
├── fram-python/                  Method 1: Python installer (no dependencies)
│   ├── setup.py                  Raw-Python installer entry point
│   ├── bin/                      FRAM engine (icm_okf_coupler_v2.py, system-start-v2.py)
│   ├── templates/                Persona prompts, OKF templates, README-HARNESS template
│   │   └── skills/               Bundled skills: grilling/, vocabulary/ (SKILL.md, scripts/, fixtures/, resources/)
│   └── defaults/                 Default OKF knowledge entities (incl. workspace-vocabulary, ste-consistency)
└── fram-bootstrap/               Method 2: skill command (no Python)
    ├── SKILL.md                  Skill instructions + scaffold procedure
    └── resources/                Bundled payload (scripts, templates, defaults)
        └── templates/skills/     Byte-identical mirror of fram-python/templates/skills/
```

## License

MIT — see [LICENSE](LICENSE). The methodology (ICM) is also published under the MIT
license by its authors (arXiv:2603.16021v2).