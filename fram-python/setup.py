#!/usr/bin/env python3
"""
FRAM v2 Installer - Bootstrap a fresh File-Routed Agentic Mesh workspace.

Copies the FRAM v2 engine (coupler + system-start), persona templates, and
OKF knowledge defaults into the target directory, then runs initialization
and self-check verification.

Usage:
    python setup.py                          # Install into current directory
    python setup.py --target <path>          # Install into specific directory
    python setup.py --non-interactive        # Skip interactive prompts
    python setup.py --harness generic        # Generate generic harness output
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

INSTALLER_DIR = Path(__file__).resolve().parent


def copy_file(src: Path, dst: Path) -> bool:
    """Copy a single file. Returns True if copied."""
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    return True


def install_engine(target: Path) -> List[str]:
    """Install the FRAM v2 engine scripts into the target workspace."""
    installed = []

    # 1. Copy bin scripts to .agents/skills/icm-okf-gates/scripts/
    skill_scripts = target / ".agents" / "skills" / "icm-okf-gates" / "scripts"
    skill_scripts.mkdir(parents=True, exist_ok=True)

    coupler_src = INSTALLER_DIR / "bin" / "icm_okf_coupler_v2.py"
    system_start_src = INSTALLER_DIR / "bin" / "system-start-v2.py"

    if copy_file(coupler_src, skill_scripts / "icm_okf_coupler.py"):
        installed.append(".agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py")
    if copy_file(system_start_src, skill_scripts / "system-start.py"):
        installed.append(".agents/skills/icm-okf-gates/scripts/system-start.py")

    # 2. Copy system-start.py to workspace root (boot entry point)
    if copy_file(system_start_src, target / "system-start.py"):
        installed.append("system-start.py")

    # 3. Copy persona templates to .profiles/
    personas_src = INSTALLER_DIR / "templates" / "personas"
    profiles_dir = target / ".profiles"
    profiles_dir.mkdir(parents=True, exist_ok=True)
    for persona_file in personas_src.glob("*.md"):
        if copy_file(persona_file, profiles_dir / persona_file.name):
            installed.append(f".profiles/{persona_file.name}")

    # 4. Copy knowledge entity templates to skill resources
    knowledge_templates_src = INSTALLER_DIR / "templates" / "knowledge"
    knowledge_templates_dst = target / ".agents" / "skills" / "icm-okf-gates" / "resources" / "templates" / "knowledge"
    knowledge_templates_dst.mkdir(parents=True, exist_ok=True)
    for template_file in knowledge_templates_src.glob("*.json"):
        if copy_file(template_file, knowledge_templates_dst / template_file.name):
            installed.append(f".agents/skills/icm-okf-gates/resources/templates/knowledge/{template_file.name}")

    # 5. Copy README-HARNESS template to skill resources
    readme_src = INSTALLER_DIR / "templates" / "README-HARNESS.template.md"
    readme_dst = target / ".agents" / "skills" / "icm-okf-gates" / "resources" / "templates" / "README-HARNESS.template.md"
    if copy_file(readme_src, readme_dst):
        installed.append(".agents/skills/icm-okf-gates/resources/templates/README-HARNESS.template.md")

    # 6. Copy default knowledge entities to knowledge/
    defaults_src = INSTALLER_DIR / "defaults" / "knowledge"
    knowledge_dir = target / "knowledge"
    knowledge_dir.mkdir(parents=True, exist_ok=True)
    for sub in ["invariants", "relations", "schemas"]:
        sub_src = defaults_src / sub
        sub_dst = knowledge_dir / sub
        sub_dst.mkdir(parents=True, exist_ok=True)
        for entity_file in sub_src.glob("*.json"):
            if copy_file(entity_file, sub_dst / entity_file.name):
                installed.append(f"knowledge/{sub}/{entity_file.name}")

    # 7. Copy SKILL.md (create a minimal one if not present)
    skill_md = target / ".agents" / "skills" / "icm-okf-gates" / "SKILL.md"
    if not skill_md.exists():
        skill_md.parent.mkdir(parents=True, exist_ok=True)
        skill_md.write_text(
            "# icm-okf-gates - ICM/OKF Deterministic Gating & Initialization\n\n"
            "## Commands\n\n"
            "```bash\n"
            "# Initialize a FRAM workspace (interactive)\n"
            "uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode init\n\n"
            "# Initialize with defaults (non-interactive)\n"
            "uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode init --non-interactive\n\n"
            "# Audit workspace coupling\n"
            "uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode audit\n\n"
            "# Verify workspace integrity\n"
            "uv run .agents/skills/icm-okf-gates/scripts/icm_okf_coupler.py --mode self-check\n\n"
            "# Boot the FRAM system\n"
            "uv run system-start.py\n"
            "```\n\n"
            "## Personas\n\n"
            "- **Orchestrator**: Plans work, routes through Investigator gate, compiles final answer.\n"
            "- **Investigator**: Red-teams plans, flags risks, handles analysis.\n"
            "- **Programmer**: Implements code from approved plan, builds, verifies.\n\n"
            "## OKF Knowledge\n\n"
            "The `knowledge/` catalog stores task-scoped domain knowledge as structured JSON entities:\n"
            "- `schemas/` - domain concept descriptions\n"
            "- `invariants/` - rules that must hold true\n"
            "- `relations/` - entity connections\n"
            "- `constraints/` - hard limits\n",
            encoding="utf-8",
        )
        installed.append(".agents/skills/icm-okf-gates/SKILL.md")

    return installed


def run_coupler(target: Path, args: List[str]) -> int:
    """Run the coupler script, preferring uv (auto-provisions pyyaml) with plain-python fallback."""
    coupler = target / ".agents" / "skills" / "icm-okf-gates" / "scripts" / "icm_okf_coupler.py"
    if not coupler.exists():
        print(f"\n  [ERROR] Coupler not found at {coupler}")
        return 1

    # Prefer: uv run --with pyyaml python <coupler> ... (auto-provisions pyyaml, no venv needed)
    uv_exe = shutil.which("uv")
    if uv_exe:
        cmd = [uv_exe, "run", "--with", "pyyaml", "python", str(coupler)] + args
        print(f"  Running: {' '.join(cmd)}")
        return subprocess.run(cmd, cwd=str(target)).returncode

    # Fallback: plain python (works if pyyaml is already importable)
    print(f"  Running: python {coupler} {' '.join(args)}")
    return subprocess.run([sys.executable, str(coupler)] + args, cwd=str(target)).returncode


def main():
    parser = argparse.ArgumentParser(description="FRAM v2 Installer")
    parser.add_argument("--target", type=str, default=".",
                        help="Target directory to install into (default: current directory)")
    parser.add_argument("--non-interactive", action="store_true",
                        help="Skip interactive prompts during init")
    parser.add_argument("--harness", choices=["opencode", "generic"], default="opencode",
                        help="Target harness for init output (default: opencode)")
    parser.add_argument("--skip-init", action="store_true",
                        help="Install files only, skip coupler initialization")

    args = parser.parse_args()
    target = Path(args.target).resolve()

    print("=" * 60)
    print("FRAM v2 Installer")
    print(f"  Installer: {INSTALLER_DIR}")
    print(f"  Target:    {target}")
    print("=" * 60)

    if not target.exists():
        print(f"\n  [ERROR] Target directory does not exist: {target}")
        sys.exit(1)

    # Step 1: Install engine files
    print("\n  Installing FRAM v2 engine files...")
    installed = install_engine(target)
    for path in installed:
        print(f"    [+] {path}")
    print(f"  Installed {len(installed)} files.")

    # Step 2: Run coupler initialization
    if not args.skip_init:
        print("\n  Running coupler initialization...")
        init_args = ["--mode", "init", "--harness", args.harness]
        if args.non_interactive:
            init_args.append("--non-interactive")
        result = run_coupler(target, init_args)
        if result != 0:
            print(f"\n  [ERROR] Initialization failed with exit code {result}")
            sys.exit(result)

    # Step 3: Run self-check
    print("\n  Running final self-check...")
    result = run_coupler(target, ["--mode", "self-check"])
    if result != 0:
        print(f"\n  [ERROR] Self-check failed with exit code {result}")
        sys.exit(result)

    print("\n" + "=" * 60)
    print("  FRAM v2 workspace installed successfully!")
    print("=" * 60)
    print("\n  Next steps:")
    print("  1. Edit manifest.yaml to set your model names.")
    print("  2. Edit opencode.jsonc to set your provider base URL.")
    print("  3. Run `uv run system-start.py` to boot the system.")
    print("  4. Create a task: active-tasks/<task-name>/query.md")
    sys.exit(0)


if __name__ == "__main__":
    main()
