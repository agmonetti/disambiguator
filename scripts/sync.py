#!/usr/bin/env python3
"""Disambiguator Anti-Drift Synchronization Engine.

Treats `system-prompt.md` as the single canonical source of truth.
Generates or verifies all agent harness rules and context files:
  - AGENTS.md
  - SKILL.md (root)
  - skills/disambiguator/SKILL.md
  - .cursor/rules/disambiguator.mdc
  - .windsurf/rules/disambiguator.md
  - .clinerules
  - .github/copilot-instructions.md
  - .kiro/steering/disambiguator.md

Usage:
  python3 scripts/sync.py          # Generate and synchronize all targets
  python3 scripts/sync.py --check  # Verify all targets are in sync (CI mode)
"""

import argparse
import json
from pathlib import Path
import re
import sys

HEADER_COMMENT = "<!-- Generated automatically by scripts/sync.py from system-prompt.md. Do not edit directly. -->\n\n"
HOOKS_MANIFEST = """{
  "disambiguator-mode-tracker": {
    "PreInvocation": [
      {
        "type": "command",
        "command": "node ./hooks/antigravity-mode-tracker.js",
        "timeout": 5
      }
    ]
  }
}
"""


CURSOR_FRONTMATTER = (
    "---\n"
    "description: Disambiguator cognitive gatekeeper. Halts on ambiguous instructions and provides multiple-choice options before modifying code.\n"
    "globs: *\n"
    "alwaysApply: true\n"
    "---\n"
)

def skill_frontmatter(name: str, description: str, package_version: str) -> str:
    """Build skill metadata from the package's published version."""
    return (
        "---\n"
        f"name: {name}\n"
        f"description: {json.dumps(description)}\n"
        "license: MIT\n"
        "metadata:\n"
        "  author: agmonetti\n"
        f'  version: "{package_version}"\n'
        "---\n"
    )


SKILL_OFF_BODY = (
    "# ==========================================\n"
    "# DISAMBIGUATOR — OFF MODE\n"
    "# ==========================================\n"
    "# CONFIGURATION\n"
    "# MODE: off\n"
    "# ==========================================\n\n"
    "Disambiguator cognitive gatekeeper is temporarily deactivated (MODE: off).\n\n"
    "1. Do NOT halt or prompt for multiple-choice disambiguation.\n"
    "2. Do NOT intercept instructions or ask ambiguity clarification questions.\n"
    "3. Proceed directly with standard tool execution, code modification, and requested actions.\n"
)

SKILL_STATUS_BODY = (
    "# ==========================================\n"
    "# DISAMBIGUATOR — STATUS\n"
    "# ==========================================\n\n"
    "Report the current Disambiguator operational mode (strict, soft, or off).\n"
    "Respond with the status confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.\n"
)

COMMAND_DISAMBIGUATOR_CONTENT = (
    "---\n"
    "description: Set Disambiguator operational mode (strict|soft|status|off)\n"
    "---\n\n"
    "Inspect or switch Disambiguator mode according to $ARGUMENTS.\n"
    "- If the argument is \"soft\", switch to soft mode (halt on Type A & high-risk Type B; assume safest standard for Type C & low-risk Type B).\n"
    "- If the argument is \"strict\", switch to strict mode (halt on all Type A, B, and C ambiguities before taking action).\n"
    "- If the argument is \"off\", disable Disambiguator gatekeeper prompt injection.\n"
    "- If the argument is \"status\" or empty, display the current active mode.\n\n"
    "Respond with the corresponding confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt the resulting mode for all subsequent turns.\n"
)

COMMAND_STRICT_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to STRICT mode (halts on all ambiguities before action)\n"
    "---\n\n"
    "Switch Disambiguator to strict mode. All ambiguities (Type A, B, and C) will halt execution for clarification before any changes are made. Respond with the strict confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.\n"
)

COMMAND_SOFT_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to SOFT mode (halts on Type A & high-risk Type B; assumes safest for Type C)\n"
    "---\n\n"
    "Switch Disambiguator to soft mode. Halt on Type A & high-risk Type B ambiguities; assume the safest standard path (Option a) for Type C & low-risk Type B. Respond with the soft confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.\n"
)

COMMAND_OFF_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to OFF mode (disables ambiguity interception)\n"
    "---\n\n"
    "Switch Disambiguator to off mode. Disable Disambiguator cognitive gatekeeper prompt interception. Respond with the off confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.\n"
)

COMMAND_STATUS_CONTENT = (
    "---\n"
    "description: Show current Disambiguator operational mode (strict, soft, or off)\n"
    "---\n\n"
    "Report the current Disambiguator operational mode (strict, soft, or off) using the status confirmation block from the Disambiguator Runtime Mode Control Protocol.\n"
)

COMMAND_HELP_CONTENT = (
    "---\n"
    "description: Quick reference for Disambiguator modes, active status, and commands\n"
    "---\n\n"
    "Show the Disambiguator quick reference card. One shot, change nothing: do not modify code, execute tools, or persist state changes.\n\n"
    "Display:\n"
    "1. Active Status: Report the current Disambiguator operational mode (strict / soft / off).\n"
    "2. Operational Modes:\n"
    "   - strict (default): Halts on all Type A (Subjectivity), Type B (Scope), and Type C (Context assumptions) ambiguities before taking action.\n"
    "   - soft: Halts on Type A & high-risk Type B (destructive changes); automatically assumes the safest standard path (Option a) for Type C & low-risk Type B and proceeds.\n"
    "   - off: Temporarily disables Disambiguator cognitive gatekeeper prompt injection.\n"
    "3. Available Commands:\n"
    "   - /disambiguator [strict|soft|status|off]: Switch or inspect operational mode.\n"
    "   - /disambiguator-help: Display this quick reference card.\n"
)


def get_targets(canonical_content: str, package_version: str) -> dict[str, str]:
    """Return map of relative target paths to their full generated content."""
    clean_canonical = canonical_content.strip() + "\n"
    strict_canonical = re.sub(r"# MODE:\s*(strict|soft|off)", "# MODE: strict", clean_canonical)
    soft_canonical = re.sub(r"# MODE:\s*(strict|soft|off)", "# MODE: soft", clean_canonical)

    return {
        "AGENTS.md": HEADER_COMMENT + clean_canonical,
        ".agents/rules/disambiguator.md": HEADER_COMMENT + clean_canonical,
        "SKILL.md": skill_frontmatter(
            "disambiguator",
            "Intercepts ambiguous instructions before action, surfaces multiple-choice options, and prevents wasted tokens or unintended code changes.",
            package_version,
        ) + HEADER_COMMENT + clean_canonical,
        "skills/disambiguator/SKILL.md": skill_frontmatter(
            "disambiguator",
            "Intercepts ambiguous instructions before action, surfaces multiple-choice options, and prevents wasted tokens or unintended code changes.",
            package_version,
        ) + HEADER_COMMENT + clean_canonical,
        "skills/disambiguator-strict/SKILL.md": skill_frontmatter(
            "disambiguator-strict",
            "Disambiguator STRICT mode: halts on all Type A, B, and C ambiguities before taking action.",
            package_version,
        ) + HEADER_COMMENT + strict_canonical,
        "skills/disambiguator-soft/SKILL.md": skill_frontmatter(
            "disambiguator-soft",
            "Disambiguator SOFT mode: halts on Type A & high-risk Type B; assumes safest path for Type C & low-risk B.",
            package_version,
        ) + HEADER_COMMENT + soft_canonical,
        "skills/disambiguator-off/SKILL.md": skill_frontmatter(
            "disambiguator-off",
            "Disambiguator OFF mode: temporarily disables cognitive gatekeeper interception.",
            package_version,
        ) + HEADER_COMMENT + SKILL_OFF_BODY,
        "skills/disambiguator-status/SKILL.md": skill_frontmatter(
            "disambiguator-status",
            "Show current Disambiguator operational mode (strict, soft, or off).",
            package_version,
        ) + HEADER_COMMENT + SKILL_STATUS_BODY,
        ".cursor/rules/disambiguator.mdc": CURSOR_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        ".windsurf/rules/disambiguator.md": HEADER_COMMENT + clean_canonical,
        ".clinerules": HEADER_COMMENT + clean_canonical,
        ".github/copilot-instructions.md": HEADER_COMMENT + clean_canonical,
        ".kiro/steering/disambiguator.md": HEADER_COMMENT + clean_canonical,
        "commands/disambiguator.md": COMMAND_DISAMBIGUATOR_CONTENT,
        "commands/disambiguator-strict.md": COMMAND_STRICT_CONTENT,
        "commands/disambiguator-soft.md": COMMAND_SOFT_CONTENT,
        "commands/disambiguator-off.md": COMMAND_OFF_CONTENT,
        "commands/disambiguator-status.md": COMMAND_STATUS_CONTENT,
        ".opencode/command/disambiguator.md": COMMAND_DISAMBIGUATOR_CONTENT,
        ".opencode/command/disambiguator-help.md": COMMAND_HELP_CONTENT,
        "hooks.json": HOOKS_MANIFEST,
        ".agents/hooks.json": HOOKS_MANIFEST,
    }


def normalize(text: str) -> str:
    """Normalize line endings and outer whitespace for robust comparison."""
    return text.replace("\r\n", "\n").strip()


def run_sync(repo_root: Path) -> None:
    canonical_file = repo_root / "system-prompt.md"
    if not canonical_file.is_file():
        print(f"[ERROR] Canonical prompt not found at: {canonical_file}", file=sys.stderr)
        sys.exit(1)

    canonical_content = canonical_file.read_text(encoding="utf-8")
    package_data = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
    targets = get_targets(canonical_content, package_data["version"])

    print(f"Synchronizing {len(targets)} harness adapters from system-prompt.md...")
    for rel_path, content in targets.items():
        target_path = repo_root / rel_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_text(content, encoding="utf-8")
        print(f"  [SYNCED] {rel_path}")

    print("[SUCCESS] All adapters successfully synchronized.")


def run_check(repo_root: Path) -> None:
    canonical_file = repo_root / "system-prompt.md"
    if not canonical_file.is_file():
        print(f"[ERROR] Canonical prompt not found at: {canonical_file}", file=sys.stderr)
        sys.exit(1)

    canonical_content = canonical_file.read_text(encoding="utf-8")
    package_data = json.loads((repo_root / "package.json").read_text(encoding="utf-8"))
    targets = get_targets(canonical_content, package_data["version"])

    failed: list[str] = []
    for rel_path, expected_content in targets.items():
        target_path = repo_root / rel_path
        if not target_path.is_file():
            print(f"  [FAIL] Missing target: {rel_path}", file=sys.stderr)
            failed.append(rel_path)
            continue

        existing_content = target_path.read_text(encoding="utf-8")
        if normalize(existing_content) != normalize(expected_content):
            print(f"  [FAIL] Drift detected in: {rel_path}", file=sys.stderr)
            failed.append(rel_path)
        else:
            print(f"  [PASS] In sync: {rel_path}")

    if failed:
        print(f"\n[DRIFT CHECK FAILED] {len(failed)} adapter(s) out of sync with system-prompt.md.", file=sys.stderr)
        print("Run 'python3 scripts/sync.py' to synchronize all adapter files.", file=sys.stderr)
        sys.exit(1)

    print(f"\n[SUCCESS] All {len(targets)} adapters are perfectly in sync with system-prompt.md.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Disambiguator multi-harness sync engine")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check whether all adapter files match system-prompt.md (fails if drift detected)",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parent.parent
    if args.check:
        run_check(repo_root)
    else:
        run_sync(repo_root)


if __name__ == "__main__":
    main()
