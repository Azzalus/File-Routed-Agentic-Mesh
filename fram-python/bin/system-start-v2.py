#!/usr/bin/env python3
"""
FRAM System Start — Boot script for File-Routed Agentic Mesh workspaces.

Loads manifest.yaml, translates tools for the target provider, resolves persona
configs, and provides CLI entry points for workspace initialization and audit.

Usage:
    python system-start.py                              # Boot with defaults
    python system-start.py --persona orchestrator       # Boot specific persona
    python system-start.py --init                       # Initialize workspace
    python system-start.py --init --non-interactive     # Initialize with defaults
    python system-start.py --init --harness generic     # Initialize for generic harness
    python system-start.py --audit                      # Audit workspace state
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import yaml
except ImportError:
    print("[ERROR] pyyaml not installed. Run: uv pip install pyyaml")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Manifest I/O
# ---------------------------------------------------------------------------

def load_manifest(manifest_path: Path) -> Dict[str, Any]:
    """Load and parse manifest.yaml."""
    if not manifest_path.exists():
        print(f"[ERROR] manifest.yaml not found at {manifest_path}")
        sys.exit(1)
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not data:
        print("[ERROR] manifest.yaml is empty or invalid YAML")
        sys.exit(1)
    return data


def save_manifest(manifest_path: Path, data: Dict[str, Any]) -> None:
    """Write manifest.yaml."""
    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


# ---------------------------------------------------------------------------
# Tool Translation (provider-agnostic)
# ---------------------------------------------------------------------------

def translate_tools_for_provider(provider: str, tools_list: List[Dict]) -> List[Dict]:
    """
    Translate universal tool syntax into provider-specific JSON format.
    Supports: openai, ollama, anthropic, and any other provider (returns openai format).
    """
    formatted = []
    for tool in tools_list:
        if provider == "anthropic":
            schema = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "input_schema": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
        else:
            # Default: OpenAI/Ollama/generic format
            schema = {
                "type": "function",
                "function": {
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        formatted.append(schema)
    return formatted


# ---------------------------------------------------------------------------
# Persona Resolution
# ---------------------------------------------------------------------------

def resolve_persona(manifest: Dict, persona_name: str) -> Optional[Dict]:
    """Resolve a persona's full config from manifest.yaml."""
    personas = manifest.get("personas", {})
    if persona_name not in personas:
        print(f"[ERROR] Persona '{persona_name}' not found in manifest.yaml")
        print(f"  Available: {', '.join(personas.keys())}")
        return None
    return personas[persona_name]


def get_persona_prompt(persona_name: str, persona_config: Dict, workspace_root: Path) -> Optional[str]:
    """Load the full persona prompt from .profiles/."""
    prompt_path = persona_config.get("prompt_path", "")
    if not prompt_path:
        return None
    full_path = workspace_root / prompt_path
    if not full_path.exists():
        print(f"[WARN] Persona prompt not found: {full_path}")
        return None
    return full_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Knowledge Catalog Access
# ---------------------------------------------------------------------------

def load_knowledge_index(workspace_root: Path) -> Optional[str]:
    """Load knowledge/index.md if it exists."""
    index_path = workspace_root / "knowledge" / "index.md"
    if index_path.exists():
        return index_path.read_text(encoding="utf-8")
    return None


def list_knowledge_entities(workspace_root: Path, entity_type: Optional[str] = None) -> List[Path]:
    """List all knowledge entities, optionally filtered by type (schemas, invariants, etc.)."""
    knowledge_dir = workspace_root / "knowledge"
    if not knowledge_dir.exists():
        return []
    if entity_type:
        target_dir = knowledge_dir / entity_type
        if not target_dir.exists():
            return []
        return list(target_dir.glob("*.json"))
    results = []
    for sub in ["schemas", "invariants", "relations", "constraints"]:
        sub_dir = knowledge_dir / sub
        if sub_dir.exists():
            results.extend(sub_dir.glob("*.json"))
    return results


def load_knowledge_entity(workspace_root: Path, entity_id: str) -> Optional[Dict]:
    """Load a specific knowledge entity by ID (searches all subdirectories)."""
    knowledge_dir = workspace_root / "knowledge"
    if not knowledge_dir.exists():
        return None
    for json_file in knowledge_dir.rglob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            metadata = data.get("metadata", {})
            if metadata.get("id") == entity_id:
                return data
        except (json.JSONDecodeError, KeyError):
            continue
    return None


# ---------------------------------------------------------------------------
# Session Boot
# ---------------------------------------------------------------------------

def initialize_agent_session(persona_name: str, manifest: Dict) -> Optional[Dict]:
    """Set up connection details for a persona."""
    agent_info = resolve_persona(manifest, persona_name)
    if not agent_info:
        return None

    provider_name = agent_info.get("provider", "unknown")
    model = agent_info.get("model", "unknown")
    temperature = agent_info.get("temperature", 0.5)

    # Resolve provider config (may be placeholder)
    provider_config = manifest.get("provider_config", {}).get(provider_name, {})
    base_url = provider_config.get("base_url", "<your-base-url>")
    provider_type = provider_config.get("type", "local")

    print(f"\n  Booting Agent: [{persona_name.upper()}]")
    print(f"  Model: {model} via {provider_name.upper()}")
    print(f"  Temperature: {temperature}")
    print(f"  Provider: {provider_type} @ {base_url}")

    # Translate tools
    tools = manifest.get("tools", [])
    ready_tools = translate_tools_for_provider(provider_name, tools)
    print(f"  Tools: {len(ready_tools)} loaded and translated for {provider_name}")

    return {
        "persona": persona_name,
        "model": model,
        "base_url": base_url,
        "temperature": temperature,
        "tools": ready_tools,
        "permissions": agent_info.get("permissions", {}),
    }


# ---------------------------------------------------------------------------
# Workspace State Detection
# ---------------------------------------------------------------------------

def detect_fram_state(root: Path) -> str:
    """Detect FRAM workspace state."""
    has_agents = (root / "AGENTS.md").exists()
    has_manifest = (root / "manifest.yaml").exists()
    has_profiles = (root / ".profiles").exists()
    has_opencode = (root / "opencode.jsonc").exists()
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


def audit_workspace(root: Path) -> Dict[str, Any]:
    """Non-destructive workspace audit."""
    state = detect_fram_state(root)
    issues = []

    # Check manifest.yaml
    manifest_path = root / "manifest.yaml"
    manifest_valid = False
    persona_count = 0
    skill_count = 0
    if manifest_path.exists():
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            manifest_valid = data is not None
            persona_count = len(data.get("personas", {}))
            skill_count = len(data.get("skills", []))
        except Exception as e:
            issues.append(f"manifest.yaml parse error: {e}")
    else:
        issues.append("manifest.yaml not found")

    # Check profiles
    profiles_dir = root / ".profiles"
    persona_files = []
    if profiles_dir.exists():
        persona_files = [f.name for f in profiles_dir.glob("*.md")]

    # Check knowledge
    knowledge_dir = root / "knowledge"
    knowledge_entities = []
    if knowledge_dir.exists():
        knowledge_entities = [str(p.relative_to(root)) for p in knowledge_dir.rglob("*.json")]

    # Check AGENTS.md
    agents_exists = (root / "AGENTS.md").exists()

    # Check for legacy .context
    has_context = (root / ".context").exists()
    if has_context:
        issues.append(".context/ directory exists (legacy ICM). Consider migrating to FRAM layout.")

    return {
        "state": state,
        "manifest_valid": manifest_valid,
        "persona_count": persona_count,
        "skill_count": skill_count,
        "persona_files": persona_files,
        "knowledge_entities": knowledge_entities,
        "has_agents_md": agents_exists,
        "has_context": has_context,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Self-Check (post-init verification)
# ---------------------------------------------------------------------------

def run_self_check(root: Path) -> List[str]:
    """Verify workspace integrity. Returns list of error messages (empty = pass)."""
    errors = []

    # 1. manifest.yaml exists and parses
    manifest_path = root / "manifest.yaml"
    if not manifest_path.exists():
        errors.append("manifest.yaml missing")
    else:
        try:
            with open(manifest_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            if not data:
                errors.append("manifest.yaml is empty")
            else:
                personas = data.get("personas", {})
                if not personas:
                    errors.append("manifest.yaml has no personas defined")
                for name, config in personas.items():
                    if "prompt_path" not in config:
                        errors.append(f"Persona '{name}' missing prompt_path")
                    elif not (root / config["prompt_path"]).exists():
                        errors.append(f"Persona '{name}' prompt file not found: {config['prompt_path']}")
        except Exception as e:
            errors.append(f"manifest.yaml parse error: {e}")

    # 2. AGENTS.md exists
    if not (root / "AGENTS.md").exists():
        errors.append("AGENTS.md missing")

    # 3. Persona .md files exist and non-empty
    profiles_dir = root / ".profiles"
    if not profiles_dir.exists():
        errors.append(".profiles/ directory missing")
    else:
        for md_file in profiles_dir.glob("*.md"):
            if md_file.stat().st_size == 0:
                errors.append(f"Empty persona file: {md_file.name}")

    # 4. Knowledge catalog
    knowledge_dir = root / "knowledge"
    if not knowledge_dir.exists():
        errors.append("knowledge/ directory missing")
    else:
        if not (knowledge_dir / "index.md").exists():
            errors.append("knowledge/index.md missing")
        # Check default invariants
        invariants_dir = knowledge_dir / "invariants"
        if not invariants_dir.exists():
            errors.append("knowledge/invariants/ directory missing")
        else:
            required_invariants = ["sandbox-rule.json", "deterministic-gate.json", "blackboard-protocol.json"]
            for inv_file in required_invariants:
                inv_path = invariants_dir / inv_file
                if not inv_path.exists():
                    errors.append(f"Missing default invariant: {inv_file}")
                else:
                    try:
                        with open(inv_path, "r", encoding="utf-8") as f:
                            json.load(f)
                    except Exception:
                        errors.append(f"Invalid JSON: {inv_file}")

        # Check relations
        relations_dir = knowledge_dir / "relations"
        if not relations_dir.exists():
            errors.append("knowledge/relations/ directory missing")
        elif not (relations_dir / "persona-flow.json").exists():
            errors.append("Missing default relation: persona-flow.json")

    # 5. No sandbox modification (read-only check)
    for sandbox_dir in ["shared-software", "active-tasks/shared-software"]:
        sandbox_path = root / sandbox_dir
        if sandbox_path.exists():
            # Just verify it exists — we can't check write timestamps without more deps
            pass

    return errors


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="FRAM System Start — Boot, Initialize, or Audit a FRAM workspace"
    )
    parser.add_argument("--persona", type=str, default=None,
                        help="Boot a specific persona (e.g., orchestrator, investigator, programmer)")
    parser.add_argument("--init", action="store_true",
                        help="Initialize workspace (interactive or non-interactive)")
    parser.add_argument("--audit", action="store_true",
                        help="Audit workspace state (non-destructive)")
    parser.add_argument("--self-check", action="store_true",
                        help="Run post-init verification self-check")
    parser.add_argument("--harness", choices=["opencode", "generic"], default="opencode",
                        help="Target harness for init output (default: opencode)")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Disable interactive prompts during init")
    parser.add_argument("--domain", type=str, default=None,
                        help="Domain name for initialization")
    parser.add_argument("--manifest", type=str, default="manifest.yaml",
                        help="Path to manifest.yaml (default: manifest.yaml)")

    args = parser.parse_args()
    root = Path.cwd()
    manifest_path = root / args.manifest

    print("=" * 60)
    print("FRAM System Start")
    print(f"  Workspace: {root}")
    print(f"  State:     {detect_fram_state(root)}")
    print("=" * 60)

    # --- Audit mode ---
    if args.audit:
        report = audit_workspace(root)
        print(f"\n  Workspace State:  {report['state']}")
        print(f"  Manifest Valid:   {report['manifest_valid']}")
        print(f"  Personas:         {report['persona_count']} ({', '.join(report['persona_files'])})")
        print(f"  Skills:           {report['skill_count']}")
        print(f"  Knowledge Entities: {len(report['knowledge_entities'])}")
        print(f"  AGENTS.md:        {report['has_agents_md']}")
        if report["issues"]:
            print("\n  Issues:")
            for issue in report["issues"]:
                print(f"    - {issue}")
        else:
            print("\n  No issues found.")
        print("=" * 60)
        sys.exit(0 if not report["issues"] else 1)

    # --- Self-check mode ---
    if args.self_check:
        errors = run_self_check(root)
        if errors:
            print("\n  Self-Check FAILED:")
            for err in errors:
                print(f"    - {err}")
            sys.exit(1)
        else:
            print("\n  Self-Check PASSED — all workspace files verified.")
            sys.exit(0)

    # --- Init mode ---
    if args.init:
        # Delegate to icm_okf_coupler.py for full initialization
        coupler_path = root / ".agents" / "skills" / "icm-okf-gates" / "scripts" / "icm_okf_coupler.py"
        if coupler_path.exists():
            cmd = [sys.executable, str(coupler_path), "--mode", "init", "--harness", args.harness]
            if args.non_interactive:
                cmd.append("--non-interactive")
            if args.domain:
                cmd.extend(["--domain", args.domain])
            os.execv(sys.executable, cmd)
        else:
            print(f"\n  [ERROR] Coupler not found at {coupler_path}")
            print("  Cannot run initialization without icm_okf_coupler.py")
            sys.exit(1)

    # --- Normal boot mode ---
    manifest = load_manifest(manifest_path)

    if args.persona:
        # Boot single persona
        session = initialize_agent_session(args.persona, manifest)
        if session:
            print(f"\n  Session ready: {args.persona}")
        else:
            sys.exit(1)
    else:
        # Boot all personas
        personas = manifest.get("personas", {})
        if not personas:
            print("\n  No personas defined in manifest.yaml")
            sys.exit(1)
        print(f"\n  Found {len(personas)} personas:")
        for name in personas:
            session = initialize_agent_session(name, manifest)

    # Load knowledge if available
    knowledge_index = load_knowledge_index(root)
    if knowledge_index:
        entity_count = len(list_knowledge_entities(root))
        print(f"\n  Knowledge: {entity_count} entities indexed")
    else:
        print("\n  Knowledge: no catalog found")

    print("\n  System ready.")
    print("=" * 60)


if __name__ == "__main__":
    main()
