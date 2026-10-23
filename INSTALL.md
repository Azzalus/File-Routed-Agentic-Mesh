# INSTALL.md — File-Routed Agentic Mesh (FRAM)

Two independent install methods produce the same FRAM workspace scaffold.
Run every shell block below from the **repository root** (the directory that
contains `fram-python/` and `fram-bootstrap/`). Blocks within a section run
sequentially in the same shell session.

| Method | Folder | What you need |
|:---|:---|:---|
| **Method 1 — Python installer** | [`fram-python/`](fram-python/) | Python 3.8+ (standard library only); `uv` optional |
| **Method 2 — skill command** | [`fram-bootstrap/`](fram-bootstrap/) | Any agent harness with file read/write/copy tools — no Python at all |

---

## Method 1 — Python installer (`fram-python/`)

### Prerequisites

- **Python 3.8+** — standard library only. No `pip install`, no `requirements.txt`,
  no virtual environment.
- **(Optional) `uv`** — if `uv` is on your `PATH`, the installer runs the coupler
  with `pyyaml` auto-provisioned. Without `uv`, plain Python is used and the coupler
  falls back to a built-in minimal YAML writer. Either way, no manual dependency
  setup.

### Install

1. Create the target directory — the installer installs *into* an existing directory
   and exits with an error if the target does not exist.
2. Run the installer:

```bash
mkdir fram-workspace
python fram-python\setup.py --target fram-workspace --non-interactive
```

Flags:

- `--target <path>` — where to install (default: current directory). The directory
  must already exist.
- `--non-interactive` — skip the persona interview; write the default persona/model
  skeleton.
- `--harness {opencode,generic}` — `opencode` (default) generates `opencode.jsonc`;
  `generic` generates `README-HARNESS.md` for non-opencode harnesses.
- `--skip-init` — copy files only; skip coupler initialization and self-check.

Interactive alternative (prompts for personas and models):
`python fram-python\setup.py --target fram-workspace`

What the installer does:

1. Copies the engine scripts into `.agents/skills/icm-okf-gates/scripts/`
   (installed as `icm_okf_coupler.py` and `system-start.py`) and copies
   `system-start.py` to the workspace root as the boot entry point.
2. Copies persona templates to `.profiles/` (orchestrator, investigator, programmer).
3. Copies OKF knowledge templates and the harness README into the skill's
   `resources/templates/` directory.
4. Copies the bundled skills from `templates/skills/` recursively into
   `.agents/skills/` (`icm-okf-gates`, `grilling`, `vocabulary`).
5. Copies default OKF knowledge entities (invariants, relations, schemas —
   including `workspace-vocabulary.json` and `ste-consistency.json`) into `knowledge/`.
6. Runs the coupler in `init` mode: generates `AGENTS.md`, `manifest.yaml`,
   `opencode.jsonc` (Layer 0/1 files gated `"ask"`), writes `knowledge/index.md`,
   registers the bundled skills in `manifest.yaml`, and creates the
   `active-tasks/shared-software/` sandbox directory.
7. Runs the coupler in `self-check` mode: verifies required files exist and are
   valid, and returns **exit code 0** only on success.

### Verify and boot

Run from the repository root, immediately after the install block:

```bash
cd fram-workspace
python .agents\skills\icm-okf-gates\scripts\icm_okf_coupler.py --mode self-check
uv run --with pyyaml python system-start.py
cd ..
```

- The coupler accepts only `--mode`, `--harness`, `--non-interactive`, and
  `--domain`. There is no `--target` flag: the coupler always operates on the
  current working directory, so run it with `cwd` = the workspace root.
- Boot with `uv run --with pyyaml python system-start.py` from the workspace root.
  A bare `python system-start.py` fails if `pyyaml` is not installed in the current
  interpreter.

### First-use smoke task

```bash
cd fram-workspace
if not exist active-tasks\smoke-task mkdir active-tasks\smoke-task
echo Replace this line with your task goal. > active-tasks\smoke-task\query.md
cd ..
```

Open `active-tasks\smoke-task\query.md` and replace the placeholder line with a
real goal, then start your harness in the workspace root.

---

## Method 2 — skill command (`fram-bootstrap/`)

### Prerequisites

- Any agent harness with file **read / write / copy** tools — opencode, Claude Code,
  Codex, etc.
- A target directory (usually your project root).

### Install the skill

**Global install (opencode)** — copy the entire `fram-bootstrap/` folder
(`SKILL.md` + `resources/`) into the opencode skills directory:

- Windows: `C:\Users\<you>\.config\opencode\skills\fram-bootstrap\`
- macOS / Linux: `~/.config/opencode/skills/fram-bootstrap/`

Restart opencode (or reload skills), then invoke with `/fram-bootstrap`.

**Per-project (any harness)** — copy the entire `fram-bootstrap/` folder into
`<project>/.agents/skills/fram-bootstrap/`. For opencode, ensure `skills.paths`
includes `./.agents/skills` in your project `opencode.jsonc` (the FRAM scaffold
template ships with this already).

### Scaffold

Type `/fram-bootstrap` in a chat session and name the target directory
(for example `fram-workspace`). The agent follows the skill's Step A/B/C tables
with file tools only: it creates the folder structure, copies the engine scripts,
persona templates, config skeletons (`AGENTS.md`, `manifest.yaml`, `opencode.jsonc`),
OKF defaults (including `workspace-vocabulary.json` and `ste-consistency.json`),
the `grilling` and `vocabulary` skills, and writes `knowledge/index.md`. No shell
commands are required for the scaffold itself.

### Verify and boot

Run these from the repository root once the skill reports the scaffold complete:

```bash
cd fram-workspace
python .agents\skills\icm-okf-gates\scripts\icm_okf_coupler.py --mode self-check
uv run --with pyyaml python system-start.py
cd ..
```

The coupler accepts only `--mode`, `--harness`, `--non-interactive`, and `--domain`
(no `--target` flag — it operates on the current working directory). The verification
commands above are optional post-install tooling: the scaffold itself never needs
Python.

### First-use smoke task

```bash
cd fram-workspace
if not exist active-tasks\smoke-task mkdir active-tasks\smoke-task
echo Replace this line with your task goal. > active-tasks\smoke-task\query.md
cd ..
```

---

## Post-install configuration (both methods)

1. Edit `manifest.yaml` — replace `<your-project-name>` and each
   `<your-<persona>-model>` placeholder with the real model identifiers you route to.
2. Edit `opencode.jsonc` — replace the provider `baseURL` and `apiKey` for your
   serving endpoint, and replace the model placeholders (including the top-level
   `"model"` default).
3. Start opencode in the workspace root (it reads `AGENTS.md`, `opencode.jsonc`, and
   `manifest.yaml` at startup), or wire `.profiles/*.md` into any other harness
   (see the bundled `README-HARNESS.template.md`).
4. Boot: `uv run --with pyyaml python system-start.py` from the workspace root.
5. Create your first task: `active-tasks/<task-name>/query.md`.

Layer 0/1 files (`AGENTS.md`, `manifest.yaml`, `opencode.jsonc`) are editable only
when you have defined the new entries beforehand and have explicitly authorized the
edit — the runtime `"ask"` permission patterns in `opencode.jsonc` enforce this.

---

## Bundled skills

Every installed workspace contains these skills under `.agents/skills/`:

| Skill | Location | Purpose |
|:---|:---|:---|
| `icm-okf-gates` | `.agents/skills/icm-okf-gates/` | Workspace initialization, ICM/OKF coupling, deterministic gates (coupler: `init`, `audit`, `self-check`; boot script). |
| `grilling` | `.agents/skills/grilling/` | Relentless design interview for Stage 01: asks the whole frontier in one question round, halts when ambiguity survives two rounds, mandates the grilling log. |
| `vocabulary` | `.agents/skills/vocabulary/` | Controlled term capture: SKILL body, conformance checker (`scripts/conformance_checker.py`), fixtures, and the per-task vocabulary template. |

`knowledge/index.md` lists the workspace catalog entities, including
`schemas/workspace-vocabulary.json` and `invariants/ste-consistency.json`.

---

## Verification commands (summary)

All commands run with `cwd` = the installed workspace root:

- File presence: `.agents/skills/icm-okf-gates/SKILL.md`,
  `.agents/skills/grilling/SKILL.md`, `.agents/skills/vocabulary/SKILL.md`,
  `knowledge/schemas/workspace-vocabulary.json`,
  `knowledge/invariants/ste-consistency.json` must all exist.
- Coupler self-check: `python .agents\skills\icm-okf-gates\scripts\icm_okf_coupler.py --mode self-check`
  → exit code 0.
- Boot: `uv run --with pyyaml python system-start.py` → exit code 0.
- Conformance checker (optional, from the workspace root):
  `python .agents\skills\vocabulary\scripts\conformance_checker.py --self-test`
  → exit code 0.

---

## Notes

- **Non-destructive:** neither installer overwrites an existing file. Re-running an
  install (or the bootstrap skill's partial-merge path) skips files that are already
  present and reports them as conflicts; your edits are never clobbered.
