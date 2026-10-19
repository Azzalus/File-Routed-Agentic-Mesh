#!/usr/bin/env python3
"""
ICM-OKF Coupling & Initialization Engine (FRAM v2).

Detects FRAM workspace state, scaffolds missing structures, provisions personas
and OKF knowledge catalogs. Supports interactive persona interview, multiple
harness targets, and deterministic self-check verification.

Usage:
    uv run icm_okf_coupler.py --mode init
    uv run icm_okf_coupler.py --mode init --non-interactive
    uv run icm_okf_coupler.py --mode init --harness generic
    uv run icm_okf_coupler.py --mode audit
    uv run icm_okf_coupler.py --mode self-check
"""

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_PERSONAS = {
    "orchestrator": {
        "role": "Orchestration, planning, routing, final compilation",
        "temperature": 0.2,
        "prompt_path": ".profiles/orchestrator.md",
        "permissions": {
            "read": "allow",
            "edit": {
                "*active-tasks*query.md": "allow",
                "*active-tasks*BLACKBOARD.md": "allow",
            },
            "bash": {
                "dir*": "allow",
                "git status*": "allow",
                "git diff*": "allow",
                "uv run *validate*": "allow",
            },
        },
    },
    "investigator": {
        "role": "Plan red-team review, analysis, risk assessment",
        "temperature": 0.0,
        "prompt_path": ".profiles/investigator.md",
        "permissions": {
            "read": "allow",
            "edit": {
                "*active-tasks*BLACKBOARD.md": "allow",
                "*active-tasks*mcp-scratchpad*": "allow",
            },
            "bash": {
                "dir*": "allow",
                "dumpbin*": "allow",
                "python *": "allow",
                "uv run *": "allow",
                "strings*": "allow",
            },
        },
    },
    "programmer": {
        "role": "Implementation, build, verification",
        "temperature": 0.5,
        "prompt_path": ".profiles/programmer.md",
        "permissions": {
            "read": "allow",
            "edit": {
                "*active-tasks*-source*": "allow",
                "*active-tasks*-output*": "allow",
                "*active-tasks*BLACKBOARD.md": "allow",
                "*active-tasks*mcp-scratchpad*": "allow",
            },
            "bash": {
                "g++ *": "allow",
                "gcc *": "allow",
                "clang *": "allow",
                "dir*": "allow",
                "git status*": "allow",
                "uv run *": "allow",
                "python *": "allow",
            },
        },
    },
}

DEFAULT_KNOWLEDGE_INVARIANTS = {
    "sandbox-rule.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "inv-sandbox", "domain": "fram", "version": "1.0"},
        "type": "invariant",
        "properties": {
            "name": "Sandbox Rule",
            "description": "shared-software/ and target-software/ are READ-ONLY for all personas.",
            "enforced_by": ["orchestrator", "investigator", "programmer"],
            "violation_action": "halt task, report to user",
        },
        "relations": [{"source": "inv-sandbox", "target": "schema-fram-layout", "type": "CONSTRAINS"}],
        "invariants": [],
    },
    "deterministic-gate.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "inv-det-gate", "domain": "fram", "version": "1.0"},
        "type": "invariant",
        "properties": {
            "name": "Deterministic Gate",
            "description": "No task may complete through probabilistic assertions alone. Exit code 0 required.",
            "enforced_by": ["orchestrator", "investigator", "programmer"],
            "violation_action": "block stage completion, require re-verification",
        },
        "relations": [{"source": "inv-det-gate", "target": "schema-task-lifecycle", "type": "GOVERNS"}],
        "invariants": [],
    },
    "blackboard-protocol.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "inv-blackboard", "domain": "fram", "version": "1.0"},
        "type": "invariant",
        "properties": {
            "name": "Blackboard Protocol",
            "description": "Agents communicate only through BLACKBOARD.md. No direct inter-agent communication.",
            "enforced_by": ["orchestrator", "investigator", "programmer"],
            "violation_action": "halt task, redirect communication to BLACKBOARD.md",
        },
        "relations": [{"source": "inv-blackboard", "target": "schema-fram-layout", "type": "GOVERNS"}],
        "invariants": [],
    },
}

DEFAULT_KNOWLEDGE_RELATIONS = {
    "persona-flow.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "rel-persona-flow", "domain": "fram", "version": "1.0"},
        "type": "relation",
        "properties": {
            "name": "Default Persona Flow",
            "description": "Orchestrator -> Investigator (red-team gate) -> Programmer -> Orchestrator (compile).",
            "source": "orchestrator",
            "target": "programmer",
            "relation_type": "SEQUENTIAL_WITH_GATE",
            "gate": "investigator",
        },
        "relations": [],
        "invariants": [],
    },
}

DEFAULT_KNOWLEDGE_SCHEMAS = {
    "fram-layout.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "schema-fram-layout", "domain": "fram", "version": "1.0"},
        "type": "schema",
        "properties": {
            "name": "FRAM Workspace Layout",
            "description": "The canonical File-Routed Agentic Mesh directory structure.",
            "fields": [
                {"name": "AGENTS.md", "role": "Layer 0: Workspace identity and hard rules"},
                {"name": "manifest.yaml", "role": "Layer 1: OKF persona registry + skill catalog"},
                {"name": ".profiles/", "role": "Full persona prompt files (loaded on-demand)"},
                {"name": "active-tasks/", "role": "Task execution environment"},
                {"name": "knowledge/", "role": "OKF knowledge catalog (Layer 2)"},
            ],
        },
        "relations": [],
        "invariants": ["inv-sandbox", "inv-blackboard"],
    },
    "task-lifecycle.json": {
        "$schema": "https://schema.okf.org/v1/knowledge.json",
        "metadata": {"id": "schema-task-lifecycle", "domain": "fram", "version": "1.0"},
        "type": "schema",
        "properties": {
            "name": "FRAM Task Lifecycle",
            "description": "4-stage workflow with Investigator red-team gate.",
            "fields": [
                {"stage": "01_planning", "owner": "orchestrator"},
                {"stage": "02_red_team", "owner": "investigator"},
                {"stage": "03_implementation", "owner": "programmer"},
                {"stage": "04_compilation", "owner": "orchestrator"},
            ],
        },
        "relations": [],
        "invariants": ["inv-det-gate"],
    },
}


def yaml_dump_minimal(data: Any, indent: int = 0) -> str:
    """Minimal YAML writer for the manifest structures we generate (no pyyaml needed)."""
    lines = []
    prefix = " " * indent
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.append(yaml_dump_minimal(value, indent + 2))
            elif isinstance(value, list):
                if not value:
                    lines.append(f"{prefix}{key}: []")
                else:
                    lines.append(f"{prefix}{key}:")
                    for item in value:
                        if isinstance(item, dict):
                            lines.append(f"{prefix}-")
                            lines.append(yaml_dump_minimal(item, indent + 4))
                        else:
                            lines.append(f"{prefix}- {yaml_scalar(item)}")
            else:
                lines.append(f"{prefix}{key}: {yaml_scalar(value)}")
    return "\n".join(lines)


def yaml_scalar(value: Any) -> str:
    """Render a scalar value as a YAML string."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    s = str(value)
    # Quote if the string contains YAML-special characters
    if any(c in s for c in ":#{}[],&*!|>'\"%@`") or s.startswith((" ", "-", "?")):
        return f'"{s}"'
    return s


# ---------------------------------------------------------------------------
# Workspace State Detection
# ---------------------------------------------------------------------------

def detect_fram_state(root: Path) -> str:
    """Detect which FRAM state the workspace is in."""
    has_agents = (root / "AGENTS.md").exists()
    has_manifest = (root / "manifest.yaml").exists()
    has_profiles = (root / ".profiles").exists()
    has_context = (root / ".context").exists()
    profiles_dir = root / ".profiles"
    has_persona_files = profiles_dir.exists() and any(profiles_dir.glob("*.md"))

    if has_agents and has_manifest and has_profiles and has_persona_files:
        if has_context:
            return "Hybrid"
        return "FRAM Complete"
    elif has_agents or has_manifest:
        return "FRAM Partial"
    elif has_context and not has_agents:
        return "Legacy ICM"
    else:
        return "FRAM Clean"


# ---------------------------------------------------------------------------
# Interactive Persona Interview
# ---------------------------------------------------------------------------

def run_persona_interview(default_personas: Dict) -> Dict:
    """Interactive interview to configure personas."""
    print("\n" + "=" * 60)
    print("PERSONA INTERVIEW")
    print("=" * 60)

    configured = {}

    # 1. Persona names
    default_names = list(default_personas.keys())
    print(f"\nDefault personas: {', '.join(default_names)}")
    custom = input("Customize roles? (n/default): ").strip().lower()

    if custom in ("y", "yes"):
        names_input = input(f"Persona names (comma-separated, default: {','.join(default_names)}): ").strip()
        if names_input:
            names = [n.strip() for n in names_input.split(",") if n.strip()]
        else:
            names = default_names
    else:
        names = default_names

    # 2. Provider setup
    print("\nProvider setup:")
    provider = input("LLM provider name (e.g., lmstudio, openai, anthropic, ollama): ").strip()
    if not provider:
        provider = "lmstudio"

    base_url = input(f"Base URL for {provider} (default: http://localhost:11434/v1): ").strip()
    if not base_url:
        base_url = "http://localhost:11434/v1"

    # 3. Model names per persona
    print(f"\nModel configuration (provider: {provider}):")
    for name in names:
        default_model = default_personas.get(name, {}).get("model", f"{name}-model")
        model = input(f"  Model for {name} (default: {default_model}): ").strip()
        if not model:
            model = default_model

        temp_default = default_personas.get(name, {}).get("temperature", 0.5)
        temp_input = input(f"  Temperature for {name} (default: {temp_default}): ").strip()
        temperature = float(temp_input) if temp_input else temp_default

        configured[name] = {
            "role": default_personas.get(name, {}).get("role", f"{name} role"),
            "provider": provider,
            "model": model,
            "temperature": temperature,
            "prompt_path": f".profiles/{name}.md",
            "permissions": default_personas.get(name, {}).get("permissions", {}),
        }

    # 4. Skill selection
    print("\nSkills:")
    skills_input = input("Skills to install (default: icm-okf-gates): ").strip()
    skills = [s.strip() for s in skills_input.split(",") if s.strip()] if skills_input else ["icm-okf-gates"]

    # 5. Domain knowledge
    print("\nDomain Knowledge (Layer 2):")
    print("  You can describe schemas, constraints, or rules to pre-load.")
    print("  Press Enter with empty input when done.")
    custom_knowledge = []
    while True:
        entity_name = input("  Knowledge entity name (empty to skip): ").strip()
        if not entity_name:
            break
        entity_desc = input(f"  Description of {entity_name}: ").strip()
        entity_type = input(f"  Type (schema/invariant/constraint, default: schema): ").strip() or "schema"
        custom_knowledge.append({"name": entity_name, "description": entity_desc, "type": entity_type})

    return {
        "personas": configured,
        "provider": provider,
        "base_url": base_url,
        "skills": skills,
        "custom_knowledge": custom_knowledge,
    }


def non_interactive_defaults() -> Dict:
    """Generate sensible defaults without prompts."""
    configured = {}
    for name, defaults in DEFAULT_PERSONAS.items():
        configured[name] = {
            **defaults,
            "provider": "lmstudio",
            "model": f"<your-{name}-model>",
        }
    return {
        "personas": configured,
        "provider": "lmstudio",
        "base_url": "http://localhost:11434/v1",
        "skills": ["icm-okf-gates"],
        "custom_knowledge": [],
    }


# ---------------------------------------------------------------------------
# Initialization
# ---------------------------------------------------------------------------

def find_templates_dir() -> Optional[Path]:
    """Locate the skill's templates directory (multiple search paths for robustness)."""
    script_dir = Path(__file__).resolve().parent
    candidates = [
        # Deployed location: .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py
        script_dir.parent / "resources" / "templates",
        # Development location: <source>/icm_okf_coupler.py with templates beside it
        script_dir / "templates",
        script_dir.parent / "templates",
        # Workspace-relative
        Path.cwd() / ".agents" / "skills" / "icm-okf-gates" / "resources" / "templates",
    ]
    for c in candidates:
        if c.exists() and c.is_dir():
            return c
    return None


def copy_if_missing(src: Path, dst: Path) -> bool:
    """Copy file only if destination doesn't exist. Returns True if copied."""
    if dst.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def write_json_entity(path: Path, data: Dict) -> None:
    """Write a JSON knowledge entity."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)


def scaffold_knowledge(root: Path) -> None:
    """Create the knowledge/ directory with default FRAM entities."""
    knowledge_dir = root / "knowledge"

    # Create subdirectories
    for sub in ["schemas", "invariants", "relations", "constraints"]:
        (knowledge_dir / sub).mkdir(parents=True, exist_ok=True)

    # Write default invariants
    for filename, entity in DEFAULT_KNOWLEDGE_INVARIANTS.items():
        write_json_entity(knowledge_dir / "invariants" / filename, entity)

    # Write default relations
    for filename, entity in DEFAULT_KNOWLEDGE_RELATIONS.items():
        write_json_entity(knowledge_dir / "relations" / filename, entity)

    # Write default schemas
    for filename, entity in DEFAULT_KNOWLEDGE_SCHEMAS.items():
        write_json_entity(knowledge_dir / "schemas" / filename, entity)

    # Write index.md
    index_path = knowledge_dir / "index.md"
    if not index_path.exists():
        index_path.write_text(
            "# OKF Knowledge Catalog\n\n"
            "## Invariants\n"
            "- `invariants/sandbox-rule.json` — Sandbox Rule (READ-ONLY sandboxes)\n"
            "- `invariants/deterministic-gate.json` — Deterministic Gate (exit code 0)\n"
            "- `invariants/blackboard-protocol.json` — Blackboard Protocol (inter-agent comms)\n\n"
            "## Relations\n"
            "- `relations/persona-flow.json` — Default persona workflow\n\n"
            "## Schemas\n"
            "- `schemas/fram-layout.json` — FRAM workspace directory structure\n"
            "- `schemas/task-lifecycle.json` — 4-stage task lifecycle\n\n",
            encoding="utf-8",
        )

    # Write log.md
    log_path = knowledge_dir / "log.md"
    if not log_path.exists():
        log_path.write_text(
            "# Knowledge Synchronization Log\n\n"
            "- Initialized FRAM knowledge catalog with default invariants, relations, and schemas.\n",
            encoding="utf-8",
        )


def scaffold_opencode_jsonc(root: Path, config: Dict) -> None:
    """Generate opencode.jsonc for the opencode harness."""
    opencode_path = root / "opencode.jsonc"
    if opencode_path.exists():
        return  # Never overwrite

    personas = config["personas"]
    provider = config["provider"]
    base_url = config["base_url"]

    # Build agent definitions
    agent_defs = {}
    for name, pconfig in personas.items():
        agent_defs[name] = {
            "mode": "primary",
            "description": f"FRAM {name.title()}. {pconfig['role']}.",
            "model": f"{provider}/{pconfig['model']}",
            "temperature": pconfig["temperature"],
            "prompt": f"{{file:./.profiles/{name}.md}}",
            "permission": pconfig.get("permissions", {}),
        }

    opencode_config = {
        "$schema": "https://opencode.ai/config.json",
        "default_agent": "orchestrator",
        "instructions": ["./AGENTS.md"],
        "skills": {"paths": ["./.agents/skills"]},
        "provider": {
            provider: {
                "npm": "@ai-sdk/openai-compatible",
                "name": f"{provider.title()} (Local)",
                "options": {
                    "baseURL": base_url,
                    "apiKey": "none",
                },
                "models": {
                    pconfig["model"]: {
                        "name": pconfig["model"],
                        "supportsToolCalls": True,
                    }
                    for pconfig in personas.values()
                },
            }
        },
        "model": f"{provider}/{list(personas.values())[0]['model']}",
        "shell": "cmd",
        "permission": {
            "bash": {
                "*": "allow",
                "git push*": "deny",
                "git reset --hard*": "deny",
            }
        },
        "agent": agent_defs,
    }

    with open(opencode_path, "w", encoding="utf-8") as f:
        json.dump(opencode_config, f, indent=2)


def scaffold_generic_readme(root: Path) -> None:
    """Generate README-HARNESS.md for generic harness wiring."""
    readme_path = root / "README-HARNESS.md"
    if readme_path.exists():
        return

    templates_dir = find_templates_dir()
    template_path = templates_dir / "README-HARNESS.template.md" if templates_dir else None

    if template_path and template_path.exists():
        shutil.copy2(template_path, readme_path)
    else:
        readme_path.write_text(
            "# FRAM Workspace — Generic Harness Wiring\n\n"
            "See .profiles/*.md for persona prompts.\n"
            "See manifest.yaml for persona configurations.\n"
            "See knowledge/ for OKF knowledge catalog.\n",
            encoding="utf-8",
        )


def scaffold_manifest(root: Path, config: Dict) -> None:
    """Generate or update manifest.yaml with persona registry + skill catalog."""
    manifest_path = root / "manifest.yaml"

    if manifest_path.exists():
        # Merge: only add missing personas
        if HAS_YAML:
            with open(manifest_path, "r", encoding="utf-8") as f:
                existing = yaml.safe_load(f) or {}
        else:
            existing = {}
    else:
        existing = {}

    # Ensure structure
    if "personas" not in existing:
        existing["personas"] = {}
    if "skills" not in existing:
        existing["skills"] = []
    if "tools" not in existing:
        existing["tools"] = []
    if "provider_config" not in existing:
        existing["provider_config"] = {}
    if "environment_policies" not in existing:
        existing["environment_policies"] = {
            "allowed_read_paths": [
                "active-tasks/shared-software/",
                "active-tasks/*/target-software/",
                "active-tasks/*/*-source/",
                "active-tasks/*/*-output/",
                ".profiles/",
            ],
            "allowed_write_paths": [
                "active-tasks/*/BLACKBOARD.md",
                "active-tasks/*/*-source/",
                "active-tasks/*/*-output/",
                "active-tasks/*/mcp-scratchpad/",
            ],
            "sandbox_execution": True,
        }

    # Add personas
    for name, pconfig in config["personas"].items():
        if name not in existing["personas"]:
            existing["personas"][name] = {
                "role": pconfig["role"],
                "provider": pconfig["provider"],
                "model": pconfig["model"],
                "temperature": pconfig["temperature"],
                "prompt_path": pconfig["prompt_path"],
                "permissions": pconfig.get("permissions", {}),
            }

    # Add provider config
    provider = config["provider"]
    if provider not in existing["provider_config"]:
        existing["provider_config"][provider] = {
            "type": "local",
            "base_url": config["base_url"],
            "api_key_env": None,
            "models": {},
        }
    # Add models to provider
    for pconfig in config["personas"].values():
        model = pconfig["model"]
        if model not in existing["provider_config"][provider].get("models", {}):
            existing["provider_config"][provider].setdefault("models", {})[model] = {
                "purpose": pconfig["role"],
            }

    # Add icm-okf-gates skill if not present
    skill_names = [s.get("name") for s in existing["skills"]]
    if "icm-okf-gates" not in skill_names:
        existing["skills"].append({
            "name": "icm-okf-gates",
            "trigger": "workspace initialization, ICM coupling, deterministic gates",
            "path": ".agents/skills/icm-okf-gates",
            "entry_script": "scripts/icm_okf_coupler.py",
            "expanded_prompt": ".agents/skills/icm-okf-gates/SKILL.md",
            "knowledge_refs": [
                "knowledge/schemas/fram-layout.json",
                "knowledge/invariants/sandbox-rule.json",
            ],
        })

    # Write manifest (use pyyaml if available, else minimal fallback writer)
    with open(manifest_path, "w", encoding="utf-8") as f:
        if HAS_YAML:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False, allow_unicode=True)
        else:
            f.write(yaml_dump_minimal(existing))
            f.write("\n")


def scaffold_profiles(root: Path, config: Dict) -> None:
    """Copy persona template files to .profiles/."""
    profiles_dir = root / ".profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)

    templates_dir = find_templates_dir()
    prompts_dir = templates_dir / "prompts" if templates_dir else None

    for name in config["personas"]:
        dest = profiles_dir / f"{name}.md"
        if dest.exists():
            continue  # Never overwrite

        if prompts_dir:
            template = prompts_dir / f"{name}.md"
            if template.exists():
                shutil.copy2(template, dest)
                continue

        # Fallback: generate minimal persona
        pconfig = config["personas"][name]
        dest.write_text(
            f"# {name.title()} — FRAM Agent\n\n"
            f"Role: {pconfig['role']}\n\n"
            f"## Workflow\n"
            f"1. Read BLACKBOARD.md for task context.\n"
            f"2. Perform your role as defined.\n"
            f"3. Write results to BLACKBOARD.md.\n\n"
            f"## Constraints\n"
            f"- Sandbox Rule: never modify shared-software/ or target-software/.\n"
            f"- Blackboard Protocol: communicate only through BLACKBOARD.md.\n",
            encoding="utf-8",
        )


def scaffold_agents_md(root: Path) -> None:
    """Generate AGENTS.md if missing."""
    agents_path = root / "AGENTS.md"
    if agents_path.exists():
        return

    agents_path.write_text(
        "# FRAM Workspace — System Rules\n\n"
        "## Workspace Path Map\n\n"
        "```\n"
        "<workspace-root>/\n"
        "├── AGENTS.md                    Layer 0  Workspace Identity & hard rules\n"
        "├── manifest.yaml                Layer 1  OKF persona registry + skill catalog\n"
        "├── opencode.jsonc               Runtime binding (agents, provider routing)\n"
        "├── system-start.py              FRAM boot script\n"
        "├── .profiles/                   Persona definitions (loaded on-demand)\n"
        "├── knowledge/                   OKF knowledge catalog (Layer 2)\n"
        "│   ├── index.md                 Master index of all entities\n"
        "│   ├── schemas/                 Domain concept descriptions\n"
        "│   ├── invariants/              Rules that must hold true\n"
        "│   ├── relations/               Entity connections\n"
        "│   └── constraints/             Hard limits\n"
        "└── active-tasks/                Task execution environment\n"
        "    ├── shared-software/         READ-ONLY shared binaries\n"
        "    └── <task-name>/             Isolated task\n"
        "        ├── query.md             User's task contract\n"
        "        ├── BLACKBOARD.md        Inter-agent communication\n"
        "        ├── knowledge/           Per-task OKF knowledge\n"
        "        ├── <task>-source/       DEVELOPMENT: mutable source\n"
        "        └── <task>-output/       EXECUTION: build and verify\n"
        "```\n\n"
        "## Agent Personas\n\n"
        "- **Orchestrator**: Plans work, routes through Investigator gate, compiles final answer.\n"
        "- **Investigator**: Red-teams plans, flags risks, handles analysis. Reviews before Programmer.\n"
        "- **Programmer**: Implements code from approved plan, builds, runs verification.\n\n"
        "## Hard Rules\n\n"
        "1. **Sandbox Rule**: `shared-software/` and `target-software/` are READ-ONLY.\n"
        "2. **Blackboard Protocol**: Agents communicate only through `BLACKBOARD.md`.\n"
        "3. **Deterministic Gate**: Every stage must pass a deterministic check (exit code 0).\n"
        "4. **Allowed Scope**: Source in `<task>-source/`, builds in `<task>-output/`.\n"
        "5. **Knowledge Access**: Query `knowledge/index.md` for domain schemas and invariants.\n",
        encoding="utf-8",
    )


def initialize_workspace(root: Path, config: Dict, harness: str) -> None:
    """Full FRAM workspace initialization."""
    state = detect_fram_state(root)
    print(f"\n  State:  {state}")
    print(f"  Harness: {harness}")
    print(f"  Personas: {', '.join(config['personas'].keys())}")
    print()

    # Step 1: AGENTS.md
    scaffold_agents_md(root)
    status = "exists" if (root / "AGENTS.md").exists() else "created"
    print(f"  [{'OK' if status == 'exists' else '+'}] AGENTS.md ({status})")

    # Step 2: manifest.yaml
    scaffold_manifest(root, config)
    print(f"  [+] manifest.yaml (updated)")

    # Step 3: .profiles/
    scaffold_profiles(root, config)
    for name in config["personas"]:
        profile_path = root / ".profiles" / f"{name}.md"
        status = "exists" if profile_path.exists() else "created"
        print(f"  [{'OK' if status == 'exists' else '+'}] .profiles/{name}.md ({status})")

    # Step 4: knowledge/ scaffold
    scaffold_knowledge(root)
    print(f"  [+] knowledge/ (scaffolded with default entities)")

    # Step 5: Harness-specific output
    if harness == "opencode":
        scaffold_opencode_jsonc(root, config)
        status = "exists" if (root / "opencode.jsonc").exists() else "created"
        print(f"  [{'OK' if status == 'exists' else '+'}] opencode.jsonc ({status})")
    else:
        scaffold_generic_readme(root)
        status = "exists" if (root / "README-HARNESS.md").exists() else "created"
        print(f"  [{'OK' if status == 'exists' else '+'}] README-HARNESS.md ({status})")

    # Step 6: active-tasks/ structure
    active_dir = root / "active-tasks"
    shared_dir = active_dir / "shared-software"
    active_dir.mkdir(parents=True, exist_ok=True)
    shared_dir.mkdir(parents=True, exist_ok=True)
    print(f"  [+] active-tasks/shared-software/")

    print("\n  Workspace initialized.")
    print("=" * 60)


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------

def audit_workspace(root: Path) -> int:
    """Non-destructive audit. Returns exit code (0 = clean, 1 = issues)."""
    state = detect_fram_state(root)
    issues = []

    # manifest.yaml
    manifest_path = root / "manifest.yaml"
    persona_count = 0
    if manifest_path.exists():
        if HAS_YAML:
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                persona_count = len(data.get("personas", {}))
                for name, pconfig in data.get("personas", {}).items():
                    if "prompt_path" not in pconfig:
                        issues.append(f"Persona '{name}' missing prompt_path")
                    elif not (root / pconfig["prompt_path"]).exists():
                        issues.append(f"Persona '{name}' prompt file missing: {pconfig['prompt_path']}")
            except Exception as e:
                issues.append(f"manifest.yaml parse error: {e}")
        else:
            # Minimal check without pyyaml
            text = manifest_path.read_text(encoding="utf-8", errors="ignore")
            if "personas:" not in text:
                issues.append("manifest.yaml missing 'personas:' section")
            persona_count = text.count("prompt_path:")
    else:
        issues.append("manifest.yaml not found")

    # .profiles/
    profiles_dir = root / ".profiles"
    persona_files = []
    if profiles_dir.exists():
        persona_files = [f.name for f in profiles_dir.glob("*.md")]
    else:
        issues.append(".profiles/ directory missing")

    # knowledge/
    knowledge_dir = root / "knowledge"
    knowledge_entities = []
    if knowledge_dir.exists():
        knowledge_entities = [str(p.relative_to(root)) for p in knowledge_dir.rglob("*.json")]
        if not (knowledge_dir / "index.md").exists():
            issues.append("knowledge/index.md missing")
        for inv_file in ["sandbox-rule.json", "deterministic-gate.json", "blackboard-protocol.json"]:
            inv_path = knowledge_dir / "invariants" / inv_file
            if not inv_path.exists():
                issues.append(f"Missing default invariant: {inv_file}")
            else:
                try:
                    with open(inv_path, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception:
                    issues.append(f"Invalid JSON: {inv_file}")
        if not (knowledge_dir / "relations" / "persona-flow.json").exists():
            issues.append("Missing default relation: persona-flow.json")
    else:
        issues.append("knowledge/ directory missing")

    # AGENTS.md
    if not (root / "AGENTS.md").exists():
        issues.append("AGENTS.md missing")

    # Legacy .context
    if (root / ".context").exists():
        issues.append(".context/ exists (legacy ICM) — consider migration")

    # Report
    print(f"\n  Workspace State:    {state}")
    print(f"  Personas:           {persona_count} ({', '.join(persona_files)})")
    print(f"  Knowledge Entities: {len(knowledge_entities)}")
    if issues:
        print(f"\n  Issues ({len(issues)}):")
        for issue in issues:
            print(f"    - {issue}")
    else:
        print("\n  No issues found.")
    print("=" * 60)
    return 0 if not issues else 1


# ---------------------------------------------------------------------------
# Self-Check
# ---------------------------------------------------------------------------

def run_self_check(root: Path) -> int:
    """Post-init verification. Returns exit code 0 = pass, 1 = fail."""
    errors = []

    # manifest.yaml
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("manifest.yaml missing")
    else:
        if HAS_YAML:
            try:
                with open(manifest_path, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                if not data or "personas" not in data:
                    errors.append("manifest.yaml has no personas")
                else:
                    for name, config in data["personas"].items():
                        if "prompt_path" not in config:
                            errors.append(f"Persona '{name}' missing prompt_path")
                        elif not (root / config["prompt_path"]).exists():
                            errors.append(f"Persona '{name}' prompt file missing")
            except Exception as e:
                errors.append(f"manifest.yaml parse error: {e}")
        else:
            text = manifest_path.read_text(encoding="utf-8", errors="ignore")
            if "personas:" not in text:
                errors.append("manifest.yaml missing 'personas:' section")

    # AGENTS.md
    if not (root / "AGENTS.md").exists():
        errors.append("AGENTS.md missing")

    # .profiles/
    profiles_dir = root / ".profiles"
    if not profiles_dir.exists():
        errors.append(".profiles/ missing")
    else:
        for md in profiles_dir.glob("*.md"):
            if md.stat().st_size == 0:
                errors.append(f"Empty persona file: {md.name}")

    # knowledge/
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.exists():
        errors.append("knowledge/ missing")
    else:
        if not (knowledge_dir / "index.md").exists():
            errors.append("knowledge/index.md missing")
        for inv in ["sandbox-rule.json", "deterministic-gate.json", "blackboard-protocol.json"]:
            p = knowledge_dir / "invariants" / inv
            if not p.exists():
                errors.append(f"Missing invariant: {inv}")
            else:
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        json.load(f)
                except Exception:
                    errors.append(f"Invalid JSON: {inv}")
        if not (knowledge_dir / "relations" / "persona-flow.json").exists():
            errors.append("Missing relation: persona-flow.json")
        for schema in ["fram-layout.json", "task-lifecycle.json"]:
            p = knowledge_dir / "schemas" / schema
            if not p.exists():
                errors.append(f"Missing schema: {schema}")

    # active-tasks/
    if not (root / "active-tasks").exists():
        errors.append("active-tasks/ missing")
    if not (root / "active-tasks" / "shared-software").exists():
        errors.append("active-tasks/shared-software/ missing")

    if errors:
        print("\n  Self-Check FAILED:")
        for err in errors:
            print(f"    - {err}")
        return 1
    else:
        print("\n  Self-Check PASSED — all workspace files verified.")
        return 0


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="ICM-OKF Coupling & Initialization Engine (FRAM v2)"
    )
    parser.add_argument("--mode", choices=["init", "audit", "self-check"], default="audit",
                        help="Execution mode (default: audit)")
    parser.add_argument("--harness", choices=["opencode", "generic"], default="opencode",
                        help="Target harness for init output (default: opencode)")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Disable interactive prompts during init")
    parser.add_argument("--domain", type=str, default=None,
                        help="Domain name for initialization")

    args = parser.parse_args()
    root = Path.cwd()

    print("=" * 60)
    print("ICM-OKF Coupling & Initialization Engine (FRAM v2)")
    print(f"  Workspace: {root}")
    print("=" * 60)

    if args.mode == "audit":
        sys.exit(audit_workspace(root))

    elif args.mode == "self-check":
        sys.exit(run_self_check(root))

    elif args.mode == "init":
        state = detect_fram_state(root)
        print(f"\n  Detected state: {state}")

        if state == "FRAM Complete":
            print("  Workspace is already complete. Running audit instead.")
            sys.exit(audit_workspace(root))

        if state == "Hybrid":
            print("  WARNING: Both FRAM and legacy .context/ detected.")
            print("  Proceeding with FRAM initialization (non-destructive).")

        # Run interview or use defaults
        if args.non_interactive or not sys.stdin.isatty():
            config = non_interactive_defaults()
            print("\n  Using non-interactive defaults.")
        else:
            config = run_persona_interview(DEFAULT_PERSONAS)

        # Initialize
        initialize_workspace(root, config, args.harness)

        # Self-check
        print("\n  Running post-init verification...")
        exit_code = run_self_check(root)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
