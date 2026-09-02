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

Usage:
  python3 scripts/sync.py          # Generate and synchronize all targets
  python3 scripts/sync.py --check  # Verify all targets are in sync (CI mode)
"""

import argparse
from pathlib import Path
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
    "version: 1.0.0\n"
    "author: Disambiguator Team\n"
    "---\n"
)


def get_targets(canonical_content: str) -> dict[str, str]:
    """Return map of relative target paths to their full generated content."""
    clean_canonical = canonical_content.strip() + "\n"
    return {
        "AGENTS.md": HEADER_COMMENT + clean_canonical,
        "SKILL.md": SKILL_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        "skills/disambiguator/SKILL.md": SKILL_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        ".cursor/rules/disambiguator.mdc": CURSOR_FRONTMATTER + HEADER_COMMENT + clean_canonical,
        ".windsurf/rules/disambiguator.md": HEADER_COMMENT + clean_canonical,
        ".clinerules": HEADER_COMMENT + clean_canonical,
        ".github/copilot-instructions.md": HEADER_COMMENT + clean_canonical,
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
