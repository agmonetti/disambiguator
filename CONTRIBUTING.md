# Contributing to Disambiguator

Thank you for helping improve Disambiguator!

## The Golden Rule

**Never edit adapter files directly.**

The rule adapters (`AGENTS.md`, `SKILL.md`, `.cursor/rules/`, `.windsurf/rules/`, `.clinerules`, `.github/copilot-instructions.md`, `.kiro/steering/`, and `skills/disambiguator/SKILL.md`) are automatically generated copies.

1. Make all core instruction changes in [`system-prompt.md`](./system-prompt.md).
2. Synchronize all adapters:
   ```bash
   python3 scripts/sync.py
   ```
3. Verify with the offline test suite:
   ```bash
   python3 -m unittest discover tests
   ```

CI enforces zero drift with `scripts/sync.py --check` on every pull request.

## Adding or Modifying Test Cases

New benchmark cases belong in [`tests/test-cases.md`](./tests/test-cases.md). Ensure any added test case conforms to the standard assertion keys (`contains_question`, `min_questions`, `no_code_executed`, `ambiguity_types_flagged`, `proceeds_directly`, `aviso_emitido`, `partial_stop`) and passes the offline parser check.
