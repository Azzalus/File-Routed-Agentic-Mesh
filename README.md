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
`system-start.py`, and the bundled `icm-okf-gates` skill.

**TL;DR:**
```bash
# Method 1 (Python)
mkdir -p ~/my-workspace
cd fram-python
python setup.py --target ~/my-workspace --non-interactive

# Method 2 (skill command)
#   install fram-bootstrap/ as a skill, then type /fram-bootstrap in your agent
```

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

Core concepts, one line each:

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

There are two ways to install. Both create the same scaffold; pick the one that
matches your environment.

### Section A — Method 1: Python installer (`fram-python/`)

The Python installer is a single raw-Python script, `setup.py`, with **no third-party
dependencies**. It copies the FRAM engine, persona templates, and OKF knowledge
defaults into a target directory, then runs the coupling engine to initialize the
workspace and self-check the result.

#### Prerequisites

- **Python 3.8+** — standard library only. No `pip install` step, no `requirements.txt`,
  no virtual environment required.
- **(Optional) `uv`** — if `uv` is on your `PATH`, the installer uses it to run the
  coupler with `pyyaml` auto-provisioned. If `uv` is not present, plain Python is used
  and the coupler falls back to a built-in minimal YAML writer — either way, no manual
  dependency setup.

#### Step-by-step

1. **Copy the repo** (or just the `fram-python/` folder) to the machine where the
   workspace will live.
2. **Create the target directory** — the installer installs *into* an existing
   directory and will exit with an error if the target does not exist:
   ```bash
   mkdir ~/my-workspace
   ```
3. **Run the installer**:
   ```bash
   # Install into the current directory
   python setup.py

   # Install into a specific directory (non-interactive, accepts all defaults)
   python setup.py --target ~/my-workspace --non-interactive

   # Install with interactive persona interview (no --non-interactive)
   python setup.py --target ~/my-workspace
   ```
4. **Flags**:
   - `--target <path>` — where to install (default: current directory). Must exist.
   - `--non-interactive` — skip the interactive persona interview; writes the default
     persona/model skeleton.
   - `--harness {opencode,generic}` — `opencode` (default) generates `opencode.jsonc`;
     `generic` generates `README-HARNESS.md` instead for non-opencode harnesses.
   - `--skip-init` — copy the engine, personas, templates, and knowledge defaults only;
     skip coupler initialization and self-check.

#### What the installer does

1. **Copies the engine**: `bin/` scripts land in
   `.agents/skills/icm-okf-gates/scripts/` (as `icm_okf_coupler.py` and
   `system-start.py`) and `system-start.py` is also copied to the workspace root as the
   boot entry point.
2. **Copies persona templates** to `.profiles/` (`orchestrator.md`,
   `investigator.md`, `programmer.md`).
3. **Copies OKF templates and the harness README** into the skill's
   `resources/templates/` directory.
4. **Copies default OKF knowledge entities** — invariants, relations, and schemas —
   into `knowledge/`.
5. **Runs the coupler in `init` mode**: detects the target's state, generates
   `AGENTS.md`, `manifest.yaml`, `opencode.jsonc`, writes `knowledge/index.md`, and
   creates the `active-tasks/shared-software/` sandbox directory.
6. **Runs the coupler in `self-check` mode**: verifies every required file exists and
   is valid, and returns **exit code 0** only on success.

#### Post-install configuration

The installer writes placeholder model names so that no interactive probing is
required:

1. Edit `manifest.yaml` — set `project_name` and replace each `<your-<persona>-model>`
   with the real model identifiers you will route to.
2. Edit `opencode.jsonc` — set the provider `baseURL` and `apiKey` for your serving
   endpoint, and replace the model placeholders (including the top-level `"model"`
   default).
3. Start opencode in the workspace root (it reads `AGENTS.md`, `opencode.jsonc`, and
   `manifest.yaml` at startup), or wire `.profiles/*.md` into any other harness
   (see the bundled `README-HARNESS.template.md`).
4. Boot the system: `uv run system-start.py`.
5. Create your first task: `active-tasks/<task-name>/query.md`.

#### Troubleshooting

- **`pyyaml` availability** — the coupler prefers
  `uv run --with pyyaml python ...`, which auto-provisions `pyyaml` with no virtual
  environment work. With plain `python` (no `uv`, no `pyyaml`), the coupler uses its
  built-in minimal YAML writer, so installs still succeed — the generated YAML is
  slightly simpler but fully parseable.
- **"Target directory does not exist"** — the installer never creates the target
  itself; create it first with `mkdir`.
- **Non-zero exit code** — the installer stops and prints the failing step. If it was
  the self-check, read the reported missing/invalid files and re-run; the installer is
  non-destructive (it never overwrites existing files).

### Section B — Method 2: skill command (`fram-bootstrap/`)

The bootstrap skill performs the same scaffolding as the Python installer using
only file-tool operations (read / write / copy) inside an agent harness. No Python
runtime, no `setup.py`, no package installation.

#### Prerequisites

- Any agent harness with file **read / write / copy** tools — opencode, Claude Code,
  Codex, etc.
- A target directory (usually your project root).
- Read permission on the skill's bundled `resources/` tree.

#### Install the skill

**Global install (opencode)** — copy the entire `fram-bootstrap/` folder (this
`SKILL.md` + `resources/`) into the opencode skills directory:

- Windows: `C:\Users\<you>\.config\opencode\skills\fram-bootstrap\`
- macOS / Linux: `~/.config/opencode/skills/fram-bootstrap/`

Restart opencode (or reload skills), then invoke with `/fram-bootstrap`.

**Per-project (any harness)** — copy the entire `fram-bootstrap/` folder into
`<project>/.agents/skills/fram-bootstrap/`. For opencode, ensure `skills.paths`
includes `./.agents/skills` in your project `opencode.jsonc` (the FRAM scaffold
template ships with this already). For other harnesses, copy the folder to wherever
that harness loads skills/prompts from.

#### Invoke

Type `/fram-bootstrap` in a chat session, optionally naming the target directory.
The agent then:

1. **Detects target state** (non-destructive): empty → full scaffold; partial → merge,
   never overwriting existing files (conflicts are recorded and reported); complete →
   stop with "already bootstrapped".
2. **Creates the folder structure** — `.profiles/`, `knowledge/` subfolders,
   `active-tasks/shared-software/`, and the `icm-okf-gates` skill tree.
3. **Copies the bundled payload** — engine scripts, persona templates, OKF knowledge
   templates/defaults, and the config skeletons (`AGENTS.md`, `manifest.yaml`,
   `opencode.jsonc`) using exact source→destination mappings (see `SKILL.md` §3).
4. **Writes generated files** — `knowledge/index.md` and the minimal
   `.agents/skills/icm-okf-gates/SKILL.md` marker.
5. **Verifies deterministically** — a file inventory checklist (every required file
   present), plus config sanity: `manifest.yaml` has a `personas:` section with a
   `prompt_path` per persona, and `opencode.jsonc` parses as strict JSON.
6. **Reports** — installed file count, conflict list (if any), and verification result.

The scaffold is complete the moment the skill finishes. The bundled engine scripts
(`.agents/skills/icm-okf-gates/scripts/`) are optional **post-install tooling**: once
Python is available you can run the coupler's `self-check` or `uv run system-start.py`
from the workspace, but the workspace itself never requires them.

#### Post-install configuration

1. Edit `<target>/manifest.yaml` — replace `<your-project-name>` and each
   `<your-<persona>-model>` placeholder with real model names.
2. Edit `<target>/opencode.jsonc` — replace the provider `baseURL`, the model
   placeholders, and the top-level `"model"` default with your actual model ids.
3. Create your first task: `active-tasks/<task-name>/query.md`.

### Section C — Which method should you use?

| Dimension | Method 1 — `fram-python/` | Method 2 — `fram-bootstrap/` |
|:---|:---|:---|
| **Runtime** | Python 3.8+ (stdlib only; `uv` optional) | None — agent file tools only |
| **Prerequisites** | Python; existing target directory | Agent harness with read/write/copy tools |
| **Interactivity** | `--non-interactive` for unattended; interactive persona interview otherwise | Agent-guided: state detection, non-destructive merge, conflict report |
| **Verification** | Coulper `self-check`, exit code 0 | Deterministic file inventory + config parse checklist |
| **Repeatability** | Fully scriptable / CI-able | Guided but agent-mediated |
| **Scaffold produced** | Identical file inventory | Identical file inventory |
| **When to use** | You have Python and want a scripted, repeatable, unattended install | You have no Python runtime, or you want a guided install driven by your agent |

**In short:** running `python setup.py --target <dir> --non-interactive` and invoking
`/fram-bootstrap` produce the same FRAM workspace. Use the Python method when you
want a deterministic command you can re-run and log; use the skill method when you are
already inside an agent and do not want to leave it — or when Python is unavailable.

---

## Repository layout

```
File-Routed-Agentic-Mesh/
├── README.md                     This file
├── LICENSE                       MIT license
├── .gitignore                    Standard ignores
├── fram-python/                  Method 1: Python installer (no dependencies)
│   ├── setup.py                  Raw-Python installer entry point
│   ├── bin/                      FRAM engine (icm_okf_coupler_v2.py, system-start-v2.py)
│   ├── templates/                Persona prompts, OKF templates, README-HARNESS template
│   └── defaults/                 Default OKF knowledge entities
└── fram-bootstrap/               Method 2: skill command (no Python)
    ├── SKILL.md                  Skill instructions + scaffold procedure
    └── resources/                Bundled payload (scripts, templates, defaults)
```

## License

MIT — see [LICENSE](LICENSE). The methodology (ICM) is also published under the MIT
license by its authors (arXiv:2603.16021v2).