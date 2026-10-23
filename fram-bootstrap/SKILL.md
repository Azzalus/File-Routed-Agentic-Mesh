---
name: fram-bootstrap
description: >-
  File-Routed Agentic Mesh (FRAM) v2 workspace installer with NO Python dependency.
  Use to scaffold a complete FRAM v2 workspace (AGENTS.md, manifest.yaml, opencode.jsonc,
  .profiles/, knowledge/, system-start.py, and the bundled icm-okf-gates, grilling, and
  vocabulary skills) in any
  target directory using only file read/write/copy tools. Works in opencode, Claude Code,
  Codex, or any agent harness that can read and write files. Complementary to the Python
  setup.py installer: use this skill when Python is unavailable or for a guided,
  agent-driven bootstrap.
---

# fram-bootstrap — FRAM v2 Workspace Installer (No Python)

Copies a self-contained FRAM v2 payload into a target directory and assembles the
workspace scaffold using **only file-tool operations** (read / write / copy).
No Python runtime, `setup.py`, or package installation is required.

This skill bundles the same payload as the Python installer (`setup.py` layer 1 files)
plus static config skeletons the coupler would otherwise generate interactively.

---

## 1. Prerequisites

- An agent with **file tools** (read, write, copy, mkdir/list). No shell build steps needed.
- A **target directory** (usually the project root where the workspace should live).
- Read permission on this skill's `resources/` tree.

---

## 2. Target State Detection (non-destructive)

Before touching anything, inspect `<target>`:

| State | Condition | Action |
| :--- | :--- | :--- |
| **Empty / Clean** | No `AGENTS.md`, `manifest.yaml`, `.profiles/`, `knowledge/`, `opencode.jsonc` | Full scaffold, all steps below. |
| **Partial** | Some of the above exist | **Non-destructive merge**: run every step, but **never overwrite an existing file** — record conflicts and continue with the missing pieces. |
| **Complete** | All scaffolding exists | Do nothing; report "already bootstrapped" and stop. |

> **Non-destructive invariant:** if a destination file already exists, do NOT overwrite it.
> Skip it, add it to the conflict list, and continue. Report the conflict list at the end.

---

## 3. Scaffold Procedure

Let `<target>` = the workspace root you are installing into, and
`<resources>` = this skill's `resources/` directory.
Create paths as needed (all copies below are content-identical copies; all writes are
new file creation).

### Step A — Create the folder structure

- `<target>/.profiles/`
- `<target>/knowledge/invariants/`
- `<target>/knowledge/relations/`
- `<target>/knowledge/schemas/`
- `<target>/active-tasks/shared-software/`
- `<target>/.agents/skills/icm-okf-gates/scripts/`
- `<target>/.agents/skills/icm-okf-gates/resources/templates/knowledge/`
- `<target>/.agents/skills/grilling/`
- `<target>/.agents/skills/vocabulary/scripts/`
- `<target>/.agents/skills/vocabulary/fixtures/`
- `<target>/.agents/skills/vocabulary/resources/`

### Step B — Copy bundled payload (exact mappings)

| Source (under `<resources>`) | Destination |
| :--- | :--- |
| `scripts/icm_okf_coupler.py` | `<target>/.agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py` |
| `scripts/system-start.py` | `<target>/.agents/skills/icm-okf-gates/scripts/system-start.py` |
| `scripts/system-start.py` | `<target>/system-start.py` |
| `templates/personas/orchestrator.md` | `<target>/.profiles/orchestrator.md` |
| `templates/personas/investigator.md` | `<target>/.profiles/investigator.md` |
| `templates/personas/programmer.md` | `<target>/.profiles/programmer.md` |
| `templates/knowledge/schema.template.json` | `<target>/.agents/skills/icm-okf-gates/resources/templates/knowledge/schema.template.json` |
| `templates/knowledge/invariant.template.json` | `<target>/.agents/skills/icm-okf-gates/resources/templates/knowledge/invariant.template.json` |
| `templates/knowledge/relation.template.json` | `<target>/.agents/skills/icm-okf-gates/resources/templates/knowledge/relation.template.json` |
| `templates/knowledge/constraint.template.json` | `<target>/.agents/skills/icm-okf-gates/resources/templates/knowledge/constraint.template.json` |
| `templates/README-HARNESS.template.md` | `<target>/.agents/skills/icm-okf-gates/resources/templates/README-HARNESS.template.md` |
| `templates/skills/grilling/SKILL.md` | `<target>/.agents/skills/grilling/SKILL.md` |
| `templates/skills/vocabulary/SKILL.md` | `<target>/.agents/skills/vocabulary/SKILL.md` |
| `templates/skills/vocabulary/scripts/conformance_checker.py` | `<target>/.agents/skills/vocabulary/scripts/conformance_checker.py` |
| `templates/skills/vocabulary/fixtures/artifact-good.md` | `<target>/.agents/skills/vocabulary/fixtures/artifact-good.md` |
| `templates/skills/vocabulary/fixtures/grilling-log-good.json` | `<target>/.agents/skills/vocabulary/fixtures/grilling-log-good.json` |
| `templates/skills/vocabulary/fixtures/mutations.json` | `<target>/.agents/skills/vocabulary/fixtures/mutations.json` |
| `templates/skills/vocabulary/fixtures/vocabulary.json` | `<target>/.agents/skills/vocabulary/fixtures/vocabulary.json` |
| `templates/skills/vocabulary/resources/vocabulary-task.template.json` | `<target>/.agents/skills/vocabulary/resources/vocabulary-task.template.json` |
| `templates/AGENTS.md` | `<target>/AGENTS.md` |
| `templates/manifest.yaml` | `<target>/manifest.yaml` |
| `templates/opencode.jsonc` | `<target>/opencode.jsonc` |
| `defaults/knowledge/invariants/blackboard-protocol.json` | `<target>/knowledge/invariants/blackboard-protocol.json` |
| `defaults/knowledge/invariants/deterministic-gate.json` | `<target>/knowledge/invariants/deterministic-gate.json` |
| `defaults/knowledge/invariants/sandbox-rule.json` | `<target>/knowledge/invariants/sandbox-rule.json` |
| `defaults/knowledge/relations/persona-flow.json` | `<target>/knowledge/relations/persona-flow.json` |
| `defaults/knowledge/schemas/fram-layout.json` | `<target>/knowledge/schemas/fram-layout.json` |
| `defaults/knowledge/schemas/task-lifecycle.json` | `<target>/knowledge/schemas/task-lifecycle.json` |
| `defaults/knowledge/schemas/workspace-vocabulary.json` | `<target>/knowledge/schemas/workspace-vocabulary.json` |
| `defaults/knowledge/invariants/ste-consistency.json` | `<target>/knowledge/invariants/ste-consistency.json` |

### Step C — Write generated files (new content, from the constants below)

1. `<target>/knowledge/index.md` — the OKF catalog master index (content below).
2. `<target>/.agents/skills/icm-okf-gates/SKILL.md` — minimal skill marker (content below).

`<target>/knowledge/index.md` content:

````markdown
# OKF Knowledge Catalog

## Invariants
- `invariants/sandbox-rule.json` — Sandbox Rule (READ-ONLY sandboxes)
- `invariants/deterministic-gate.json` — Deterministic Gate (exit code 0)
- `invariants/blackboard-protocol.json` — Blackboard Protocol (inter-agent comms)
- `invariants/ste-consistency.json` — STE Consistency (canonical terms, one meaning per sentence)

## Relations
- `relations/persona-flow.json` — Default persona workflow

## Schemas
- `schemas/fram-layout.json` — FRAM workspace directory structure
- `schemas/task-lifecycle.json` — 4-stage task lifecycle
- `schemas/workspace-vocabulary.json` — Controlled workspace vocabulary catalog
````

`<target>/.agents/skills/icm-okf-gates/SKILL.md` content:

````markdown
# icm-okf-gates - ICM/OKF Deterministic Gating & Initialization

## Commands

```bash
# Initialize a FRAM workspace (interactive)
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode init

# Initialize with defaults (non-interactive)
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode init --non-interactive

# Audit workspace coupling
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode audit

# Verify workspace integrity
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode self-check

# Boot the FRAM system
uv run system-start.py
```

## Personas

- **Orchestrator**: Plans work, routes through Investigator gate, compiles final answer.
- **Investigator**: Red-teams plans, flags risks, handles analysis.
- **Programmer**: Implements code from approved plan, builds, verifies.

## OKF Knowledge

The `knowledge/` catalog stores task-scoped domain knowledge as structured JSON entities:
- `schemas/` - domain concept descriptions
- `invariants/` - rules that must hold true
- `relations/` - entity connections
- `constraints/` - hard limits
````

### Step D — Hand the workspace to the user (do NOT run scripts)

The scaffold is now complete. Tell the user:

1. Edit `<target>/manifest.yaml` — replace `<your-project-name>` and each
   `<your-*-model>` placeholder with their real model names.
2. Edit `<target>/opencode.jsonc` — replace the provider `baseURL` and the model
   placeholders (and the `"model"` default) with the actual model IDs served by their
   provider.
3. When Python is available, the bundled engine is already installed at
   `.agents/skills/icm-okf-gates/scripts/` (coupler + boot). They can run
   `uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode self-check`
   or `uv run system-start.py` from the workspace to operate it. **The scaffold itself
   never requires this — those scripts are optional, post-install tooling.**
4. Create their first task: `active-tasks/<task-name>/query.md`.

---

## 4. Verification (deterministic)

After all steps, confirm with file tools (list/read), not model assertion:

### File inventory checklist

All of the following must exist under `<target>`:

- `AGENTS.md`
- `manifest.yaml`
- `opencode.jsonc`
- `.profiles/orchestrator.md`
- `.profiles/investigator.md`
- `.profiles/programmer.md`
- `system-start.py`
- `knowledge/index.md`
- `knowledge/invariants/blackboard-protocol.json`
- `knowledge/invariants/deterministic-gate.json`
- `knowledge/invariants/sandbox-rule.json`
- `knowledge/relations/persona-flow.json`
- `knowledge/schemas/fram-layout.json`
- `knowledge/schemas/task-lifecycle.json`
- `knowledge/schemas/workspace-vocabulary.json`
- `knowledge/invariants/ste-consistency.json`
- `.agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py`
- `.agents/skills/icm-okf-gates/scripts/system-start.py`
- `.agents/skills/icm-okf-gates/resources/templates/knowledge/` (4 template JSON files)
- `.agents/skills/icm-okf-gates/resources/templates/README-HARNESS.template.md`
- `.agents/skills/grilling/SKILL.md`
- `.agents/skills/vocabulary/SKILL.md`
- `.agents/skills/vocabulary/scripts/conformance_checker.py`
- `.agents/skills/vocabulary/fixtures/` (artifact-good.md, grilling-log-good.json, mutations.json, vocabulary.json)
- `.agents/skills/vocabulary/resources/vocabulary-task.template.json`
- `active-tasks/shared-software/` (directory)

### Config sanity

- `manifest.yaml` — contains a `personas:` section with entries for `orchestrator`,
  `investigator`, and `programmer`, each with a `prompt_path`. If your harness offers a
  YAML parse check, run it; otherwise confirm the file matches the bundled template for
  every field except the placeholders the user edited.
- `opencode.jsonc` — must parse as JSON (it is strict JSON; do not introduce trailing
  commas or comments). Use whatever JSON validation tool your harness provides, or read
  it back and confirm structure matches the template.

### Conflict report

List any destination that already existed and was therefore skipped. If conflicts were
only placeholders the user still needs to edit, note that too.

---

## 5. Installing THIS skill

### Global (opencode)

Copy the entire `fram-bootstrap/` folder (this `SKILL.md` + `resources/`) into the
opencode skill directory:

- Windows: `C:\Users\<you>\.config\opencode\skills\fram-bootstrap\`
- macOS / Linux: `~/.config/opencode/skills/fram-bootstrap\`

Restart opencode (or reload skills). Invoke with `/fram-bootstrap`.

### Per-project (any harness)

1. Copy the entire `fram-bootstrap/` folder into the project under
   `.<project>/.agents/skills/fram-bootstrap/`.
2. For opencode: `skills.paths` must include `./.agents/skills` in the project
   `opencode.jsonc` (the FRAM scaffold template ships with this already — see Step B).
3. Invoke the skill per the project's skill-loading convention.

### Other harnesses (Claude Code, Codex, etc.)

- Copy the folder to whatever location that harness loads skills/prompts from.
- The workspace's `README-HARNESS.template.md` (bundled into every scaffolded workspace,
  see Step B) documents how to wire the resulting `.profiles/*.md` personas into any
  harness manually. This skill's instructions are intentionally harness-agnostic: every
  step is plain file reading, writing, and copying.

---

## 6. Usage

When the user types **`/fram-bootstrap`**:

1. Set `<target>` = the directory the user wants to bootstrap (current project root
   unless they specify another).
2. Follow Section 2 (detect state) → Section 3 (scaffold) → Section 4 (verify).
3. Report: installed file count, conflict list (if any), and the verification result.