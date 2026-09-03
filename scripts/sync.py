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
from pathlib import Path
import re
import sys

HEADER_COMMENT = "<!-- Generated automatically by scripts/sync.py from system-prompt.md. Do not edit directly. -->\n\n"

CURSOR_FRONTMATTER = (
    "---\n"
    "description: Disambiguator cognitive gatekeeper. Halts on ambiguous instructions and provides multiple-choice options before modifying code.\n"
    "globs: *\n"
    "alwaysApply: true\n"
    "---\n"
)

SKILL_FRONTMATTER = (
    "---\n"
    "name: disambiguator\n"
    "description: Intercepts ambiguous instructions before action, surfaces multiple-choice options, and prevents wasted tokens or unintended code changes.\n"
    "license: MIT\n"
    "metadata:\n"
    "  author: agmonetti\n"
    "  version: \"1.0.0\"\n"
    "---\n"
)

SKILL_STRICT_FRONTMATTER = (
    "---\n"
    "name: disambiguator-strict\n"
    "description: \"Disambiguator STRICT mode: halts on all Type A, B, and C ambiguities before taking action.\"\n"
    "license: MIT\n"
    "metadata:\n"
    "  author: agmonetti\n"
    "  version: \"1.0.0\"\n"
    "---\n"
)

SKILL_SOFT_FRONTMATTER = (
    "---\n"
    "name: disambiguator-soft\n"
    "description: \"Disambiguator SOFT mode: halts on Type A & high-risk Type B; assumes safest path for Type C & low-risk B.\"\n"
    "license: MIT\n"
    "metadata:\n"
    "  author: agmonetti\n"
    "  version: \"1.0.0\"\n"
    "---\n"
)

SKILL_OFF_FRONTMATTER = (
    "---\n"
    "name: disambiguator-off\n"
    "description: \"Disambiguator OFF mode: temporarily disables cognitive gatekeeper interception.\"\n"
    "license: MIT\n"
    "metadata:\n"
    "  author: agmonetti\n"
    "  version: \"1.0.0\"\n"
    "---\n"
)

SKILL_STATUS_FRONTMATTER = (
    "---\n"
    "name: disambiguator-status\n"
    "description: \"Show current Disambiguator operational mode (strict, soft, or off).\"\n"
    "license: MIT\n"
    "metadata:\n"
    "  author: agmonetti\n"
    "  version: \"1.0.0\"\n"
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
    "Acknowledge in exactly one short line following the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.\n"
)

COMMAND_DISAMBIGUATOR_CONTENT = (
    "---\n"
    "description: Set Disambiguator operational mode (strict|soft|status|off)\n"
    "---\n\n"
    "Switch Disambiguator mode to $ARGUMENTS.\n"
    "- If the argument is \"soft\", switch to soft mode (halt on Type A & high-risk Type B; assume safest standard for Type C & low-risk Type B).\n"
    "- If the argument is \"strict\" or empty, switch to strict mode (halt on all Type A, B, and C ambiguities before taking action).\n"
    "- If the argument is \"off\", disable Disambiguator gatekeeper prompt injection.\n"
    "- If the argument is \"status\", display the current active mode.\n\n"
    "Acknowledge the mode update immediately following the Disambiguator Runtime Mode Control Protocol in exactly one short line and adopt it for all subsequent turns.\n"
)

COMMAND_STRICT_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to STRICT mode (halts on all ambiguities before action)\n"
    "---\n\n"
    "Switch Disambiguator to strict mode. All ambiguities (Type A, B, and C) will halt execution for clarification before any changes are made. Acknowledge the mode update following the Disambiguator Runtime Mode Control Protocol in exactly one short line and adopt it for all subsequent turns.\n"
)

COMMAND_SOFT_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to SOFT mode (halts on Type A & high-risk Type B; assumes safest for Type C)\n"
    "---\n\n"
    "Switch Disambiguator to soft mode. Halt on Type A & high-risk Type B ambiguities; assume the safest standard path (Option a) for Type C & low-risk Type B. Acknowledge the mode update following the Disambiguator Runtime Mode Control Protocol in exactly one short line and adopt it for all subsequent turns.\n"
)

COMMAND_OFF_CONTENT = (
    "---\n"
    "description: Switch Disambiguator to OFF mode (disables ambiguity interception)\n"
    "---\n\n"
    "Switch Disambiguator to off mode. Disable Disambiguator cognitive gatekeeper prompt interception. Acknowledge the mode update following the Disambiguator Runtime Mode Control Protocol in exactly one short line and adopt it for all subsequent turns.\n"
)

COMMAND_STATUS_CONTENT = (
    "---\n"
    "description: Show current Disambiguator operational mode (strict, soft, or off)\n"
    "---\n\n"
    "Report the current Disambiguator operational mode (strict, soft, or off). Acknowledge in exactly one short line and adopt it for all subsequent turns.\n"
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


def get_targets(canonical_content: str) -> dict[str, str]:
    """Return map of relative target paths to their full generated content."""
    clean_canonical = canonical_content.strip() + "\n"
    strict_canonical = re.sub(r"# MODE:\s*(strict|soft|off)", "# MODE: strict", clean_canonical)
    soft_canonical = re.sub(r"# MODE:\s*(strict|soft|off)", "# MODE: soft", clean_canonical)

    return {
        "AGENTS.md": HEADER_COMMENT + clean_canonical,
        ".agents/rules/disambiguator.md": HEADER_COMMENT + clean_canonical,
        "SKILL.md": SKILL_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        "skills/disambiguator/SKILL.md": SKILL_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        "skills/disambiguator-strict/SKILL.md": SKILL_STRICT_FRONTMATTER + HEADER_COMMENT + strict_canonical,
        "skills/disambiguator-soft/SKILL.md": SKILL_SOFT_FRONTMATTER + HEADER_COMMENT + soft_canonical,
        "skills/disambiguator-off/SKILL.md": SKILL_OFF_FRONTMATTER + HEADER_COMMENT + SKILL_OFF_BODY,
        "skills/disambiguator-status/SKILL.md": SKILL_STATUS_FRONTMATTER + HEADER_COMMENT + SKILL_STATUS_BODY,
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
    targets = get_targets(canonical_content)

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
    targets = get_targets(canonical_content)

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
