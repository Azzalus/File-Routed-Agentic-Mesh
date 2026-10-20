# INSTALL — File-Routed Agentic Mesh (FRAM)

This repo ships two independent installers that produce the **same** FRAM workspace
scaffold. Pick one. For the full rationale, see [`README.md`](README.md).

| Method | Folder | Needs |
|:---|:---|:---|
| 1 — Python installer | [`fram-python/`](fram-python/) | Python 3.8+ (stdlib only) |
| 2 — skill command | [`fram-bootstrap/`](fram-bootstrap/) | An agent harness with file read/write/copy tools (no Python) |

Both install into an **existing** target directory. Create the target first.

---

## Method 1 — Python installer

```bash
mkdir ~/my-workspace
cd fram-python
python setup.py --target ~/my-workspace --non-interactive
```

Flags:

- `--target <path>` — install destination (default: current directory). Must exist.
- `--non-interactive` — skip the persona interview; write the default skeleton.
- `--harness {opencode,generic}` — `opencode` (default) writes `opencode.jsonc`;
  `generic` writes `README-HARNESS.md` instead.
- `--skip-init` — copy files only; skip coupler `init` and `self-check`.

The installer finishes by running the coupler in `self-check` mode. Exit code **0**
means success.

## Method 2 — skill command

1. Install the skill:
   - Global (opencode): copy `fram-bootstrap/` to
     `~/.config/opencode/skills/fram-bootstrap/` (Windows:
     `C:\Users\<you>\.config\opencode\skills\fram-bootstrap\`).
   - Per-project: copy `fram-bootstrap/` to `<project>/.agents/skills/fram-bootstrap/`.
2. Invoke `/fram-bootstrap` in a chat session and name the target directory.
3. The skill scaffolds the workspace, then runs a deterministic file-inventory and
   config-parse check.

---

## After install (both methods)

1. Edit `manifest.yaml` — set `project_name` and replace every
   `<your-<persona>-model>` placeholder.
2. Edit `opencode.jsonc` — set the provider `baseURL`, `apiKey`, and model ids.
3. Start opencode in the workspace root, or wire `.profiles/*.md` into another
   harness.
4. Boot: `uv run system-start.py`.
5. Create your first task: `active-tasks/<task-name>/query.md`.

## Bundled skills

Both installers place three skills under `.agents/skills/`:

| Skill | Purpose |
|:---|:---|
| `icm-okf-gates` | ICM/OKF coupling engine (init, audit, self-check). |
| `grilling` | Structured requirement Q&A with a bounded round log. |
| `vocabulary` | Controlled vocabulary capture, STE consistency, conformance checker. |

The `vocabulary` skill ships a deterministic checker:

```bash
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --self-test
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --mutation-test .agents/skills/vocabulary/fixtures
```

Exit code **0** means the check passed.

## Verification commands

Run these after install to confirm the workspace is coherent:

```bash
# Coupler self-check (setup.py path installs land at .agents/skills/icm-okf-gates/scripts/)
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode self-check --target .
uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode audit --target .

# Boot the system and confirm both persona lines print
uv run system-start.py

# Checker contract tests
uv run .agents/skills/vocabulary/scripts/conformance_checker.py --self-test
```

## First-use smoke task (R22)

Create a throwaway task to exercise the grilling and vocabulary skills end to end:

1. Create `active-tasks/smoke-test/query.md` with one line.
2. Run the grilling skill; let it write
   `active-tasks/smoke-test/mcp-scratchpad/grilling-log.json`.
3. Run the checker against that real log:
   ```bash
   uv run .agents/skills/vocabulary/scripts/conformance_checker.py \
     --lint --log active-tasks/smoke-test/mcp-scratchpad/grilling-log.json \
     --mandate .agents/skills/grilling/SKILL.md
   ```
4. Delete the throwaway task. A genuine grilling log cannot exist until the suite is
   used, so this smoke task is the first real-log verification.

## Migrating an existing workspace (OD7-authorized merge)

Both installers are **non-destructive**: they never overwrite an existing file. A
workspace that was bootstrapped before this release keeps its old `AGENTS.md`,
`manifest.yaml`, and `opencode.jsonc`, so the framework-level policy fix never
arrives. To migrate an existing workspace, merge the new policy by hand:

1. **Overwrite asymmetry** — re-running either installer into an existing target
   skips files that already exist. No config file is ever replaced. This is why the
   merge is manual.
2. **Merge the OD7 conditional-edit rule into `AGENTS.md`** — add the Layer 0/1
   conditional-edit rule.
3. **Merge the `"ask"` gating into `opencode.jsonc`** — add the Layer 0/1 `edit`
   patterns (`*opencode.jsonc`, `*opencode.json`, `*manifest.yaml`, `*AGENTS.md`)
   with value `"ask"`, and add the anchored `knowledge/*` and
   `*active-tasks*/knowledge/*` allows.
4. **Merge the write paths into `manifest.yaml`** — add `knowledge/` and
   `active-tasks/*/knowledge/` to `allowed_write_paths`, and register the `grilling`
   and `vocabulary` skills in the `skills:` catalog.
5. **OD7-authorized:** edit Layer 0/1 files only when the user has defined the new
   entries beforehand and has explicitly authorized the edit.

## D-L7 policy-bundle dependency (R34)

`vocabulary/scripts/grilling_suite_gate_policy.json` is a self-contained policy
bundle in the `{"data": ..., "policy": ...}` envelope that `validate_gate.py`
unwraps. **The repo and both installers do not ship `validate_gate.py`** — the
round-trip install will not contain it. Consuming the D-L7 bundle therefore requires a
workspace whose `.agents/skills/icm-okf-gates/scripts/` includes `validate_gate.py`.
A repo-only install ships the bundle without a runner; this is expected.

