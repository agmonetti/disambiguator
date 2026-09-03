"""Fast, zero-dependency offline test suite for Disambiguator.

Executes in < 50ms using Python standard library unittest.
Requires no external APIs, network connections, or API keys.
"""

from pathlib import Path
import unittest

from scripts.sync import get_targets, normalize
from tests.parser import _parse_yaml_assertions, parse_test_cases


class TestParser(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.cases_file = self.repo_root / "tests" / "test-cases.md"

    def test_parse_all_20_cases(self) -> None:
        cases = parse_test_cases(self.cases_file)
        self.assertEqual(len(cases), 20, "Should parse exactly 20 test cases")

        for idx, case in enumerate(cases, 1):
            self.assertEqual(case.id, idx, f"Case ID mismatch at index {idx}")
            self.assertTrue(case.title, f"Case {idx} has empty title")
            self.assertTrue(case.prompt, f"Case {idx} has empty prompt")
            self.assertTrue(case.expected_behavior, f"Case {idx} has empty expected_behavior")

            # Standard assertion keys
            expected_keys = {
                "contains_question",
                "min_questions",
                "no_code_executed",
                "ambiguity_types_flagged",
                "proceeds_directly",
                "aviso_emitido",
                "partial_stop",
            }
            self.assertTrue(
                expected_keys.issubset(set(case.assertions.keys())),
                f"Case {idx} missing standard assertion keys: {expected_keys - set(case.assertions.keys())}",
            )
            # Ensure metadata keys are filtered out
            for bad_key in ("notes", "environment_dependent", "context"):
                self.assertNotIn(bad_key, case.assertions, f"Case {idx} has unfiltered metadata key '{bad_key}'")

    def test_parse_yaml_inline_comments_and_types(self) -> None:
        yaml_block = (
            "assertions:\n"
            "  contains_question: true # must ask questions\n"
            "  min_questions: 2 # at least two\n"
            "  no_code_executed: false\n"
            '  ambiguity_types_flagged: ["A", "B"]\n'
            '  notes: "Human note should be filtered"\n'
        )
        parsed = _parse_yaml_assertions(yaml_block)
        self.assertEqual(parsed["contains_question"], True)
        self.assertEqual(parsed["min_questions"], 2)
        self.assertEqual(parsed["no_code_executed"], False)
        self.assertEqual(parsed["ambiguity_types_flagged"], ["A", "B"])
        self.assertNotIn("notes", parsed)


class TestSync(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.canonical_file = self.repo_root / "system-prompt.md"

    def test_sync_targets_count(self) -> None:
        canonical_content = self.canonical_file.read_text(encoding="utf-8")
        targets = get_targets(canonical_content)
        self.assertEqual(len(targets), 16, "Should maintain exactly 16 harness adapters")

    def test_all_adapters_in_sync(self) -> None:
        canonical_content = self.canonical_file.read_text(encoding="utf-8")
        targets = get_targets(canonical_content)
        for rel_path, expected_content in targets.items():
            target_path = self.repo_root / rel_path
            self.assertTrue(target_path.is_file(), f"Target file does not exist: {rel_path}")
            existing_content = target_path.read_text(encoding="utf-8")
            self.assertEqual(
                normalize(existing_content),
                normalize(expected_content),
                f"Adapter drift detected in: {rel_path}",
            )


if __name__ == "__main__":
    unittest.main()
