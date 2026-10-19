# FRAM Workspace — Harness Wiring Guide

This workspace uses the **File-Routed Agentic Mesh (FRAM)** architecture with ICM/OKF extensions. This guide explains how to wire the persona files into any coding harness.

## Workspace Structure

```
<workspace-root>/
├── AGENTS.md                    # Workspace identity and rules (Layer 0)
├── manifest.yaml                # OKF persona registry + skill catalog (Layer 1)
├── system-start.py              # FRAM boot script (provider detection, tool translation)
├── .profiles/                   # Full persona prompts (loaded on-demand per agent)
│   ├── orchestrator.md
│   ├── investigator.md
│   └── programmer.md
├── knowledge/                   # OKF knowledge catalog (Layer 2)
│   ├── index.md
│   ├── schemas/
│   ├── invariants/
│   ├── relations/
│   └── constraints/
└── active-tasks/                # Task execution environment
```

## Wiring Instructions

### For opencode
The workspace includes `opencode.jsonc` with agent definitions already bound to `.profiles/*.md`. No additional wiring needed — just start opencode in this directory.

### For LM Studio Bionic
1. Create an agent for each persona in Bionic's agent editor.
2. Copy the contents of each `.profiles/*.md` file into the corresponding agent's system prompt.
3. Set the model and temperature per `manifest.yaml` persona entries.
4. Point each agent's workspace to this directory.

### For Cursor / Continue / Other AI Code Editors
1. Create a rule file (e.g., `.cursorrules`) that loads `AGENTS.md` as the base context.
2. For each persona, create a separate rule or prompt preset using the `.profiles/*.md` content.
3. Configure the editor to switch personas based on task context (manual or automated).

### For Custom / Homegrown Harnesses
1. Read `manifest.yaml` to discover available personas and their configurations.
2. Load `AGENTS.md` as the base system prompt for all agents.
3. For the active persona, load its `.profiles/*.md` file as the agent-specific prompt.
4. Use `system-start.py` to translate tool definitions for your provider:
   ```bash
   python system-start.py
   ```
   This returns the provider-specific tool schema (OpenAI, Anthropic, or custom format).

## Persona Roles

| Persona | Role | Temperature | When Active |
|:---|:---|:---|:---|
| **Orchestrator** | Plans work, routes through gates, compiles final answer | 0.2 | Every task |
| **Investigator** | Red-teams plans, flags risks, handles analysis | 0.0 | After Orchestrator drafts plan |
| **Programmer** | Implements code, builds, verifies | 0.5 | After Investigator approves plan |

## OKF Knowledge Access

Personas access domain knowledge from `knowledge/`:
- `knowledge/index.md` — master index of all entities
- `knowledge/schemas/` — domain concept descriptions
- `knowledge/invariants/` — rules that must hold true
- `knowledge/relations/` — entity connections and data flow
- `knowledge/constraints/` — hard limits and boundaries

Load only the knowledge relevant to the current task to minimize token usage.

## Adding Custom Personas

1. Create a new `.md` file in `.profiles/` with sections: `## Role`, `## Workflow`, `## Constraints`, `## Tools`.
2. Add an entry to `manifest.yaml` under `personas:` with `role`, `provider`, `model`, `temperature`, `prompt_path`, `permissions`.
3. Add a corresponding agent definition in your harness config.

## Adding Custom Knowledge

1. Create a new `.json` file in the appropriate `knowledge/` subdirectory.
2. Follow the OKF schema: `$schema`, `metadata`, `type`, `properties`, `relations`.
3. Add an entry to `knowledge/index.md` linking to the new entity.
