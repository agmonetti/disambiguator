"""Parser for Disambiguator test cases from tests/test-cases.md.

Zero external dependencies (uses standard library re, json, pathlib).
"""

from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
from typing import Any


@dataclass
class TestCase:
    id: int
    title: str
    category: str
    mode: str
    prompt: str
    ambiguity_types: list[str]
    expected_behavior: str
    assertions: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


NON_ASSERTION_KEYS = {"notes", "environment_dependent", "context", "manual_notes"}
VALID_MODES = {"strict", "soft", "off"}
ASSERTION_TYPES: dict[str, type] = {
    "contains_question": bool,
    "min_questions": int,
    "no_code_executed": bool,
    "ambiguity_types_flagged": list,
    "proceeds_directly": bool,
    "aviso_emitido": bool,
    "partial_stop": bool,
}


def _parse_yaml_assertions(block: str) -> dict[str, Any]:
    """Parse a simple key-value YAML assertions block without external dependencies."""
    assertions: dict[str, Any] = {}
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line == "assertions:":
            continue

        # Strip inline comments (e.g., "val # comment") unless inside quotes
        if "#" in line and not (('"' in line and line.count('"') >= 2) or ("'" in line and line.count("'") >= 2)):
            line = line.split("#", 1)[0].strip()

        if ":" not in line:
            continue

        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()

        if key in NON_ASSERTION_KEYS:
            continue

        # Parse booleans
        if val.lower() == "true":
            assertions[key] = True
        elif val.lower() == "false":
            assertions[key] = False
        # Parse integers
        elif val.isdigit():
            assertions[key] = int(val)
        # Parse list of strings like ["A", "B"] or []
        elif val.startswith("[") and val.endswith("]"):
            inner = val[1:-1].strip()
            if not inner:
                assertions[key] = []
            else:
                items = [
                    re.sub(r"^[\"']|[\"']$", "", item.strip())
                    for item in inner.split(",")
                    if item.strip()
                ]
                assertions[key] = items
        else:
            # Fallback string with quotes stripped
            assertions[key] = re.sub(r"^[\"']|[\"']$", "", val)

    return assertions


def _field_error(case_id: int | str, field: str, detail: str) -> ValueError:
    return ValueError(f"Test Case {case_id}: invalid field '{field}': {detail}")


def _required_match(
    pattern: str,
    block: str,
    case_id: int,
    field: str,
    flags: int = re.MULTILINE,
) -> re.Match[str]:
    match = re.search(pattern, block, flags)
    if not match:
        raise _field_error(case_id, field, "missing or malformed")
    return match


def _parse_ambiguity_types(raw_types: str) -> list[str]:
    raw_types = raw_types.strip()
    if not raw_types:
        return []
    return [
        item.strip().strip('"').strip("'")
        for item in raw_types.split(",")
        if item.strip()
    ]


def _validate_assertions(case_id: int, assertions: dict[str, Any]) -> None:
    actual_keys = set(assertions)
    expected_keys = set(ASSERTION_TYPES)
    missing = sorted(expected_keys - actual_keys)
    extra = sorted(actual_keys - expected_keys)
    if missing or extra:
        details = []
        if missing:
            details.append(f"missing {missing}")
        if extra:
            details.append(f"unexpected {extra}")
        raise _field_error(case_id, "assertions", "; ".join(details))

    for key, expected_type in ASSERTION_TYPES.items():
        value = assertions[key]
        if type(value) is not expected_type:
            raise _field_error(
                case_id,
                f"assertions.{key}",
                f"expected {expected_type.__name__}, got {type(value).__name__}",
            )
        if key == "ambiguity_types_flagged" and not all(
            isinstance(item, str) for item in value
        ):
            raise _field_error(case_id, f"assertions.{key}", "expected list[str]")


def parse_test_cases(markdown_path: Path | str) -> list[TestCase]:
    """Parse and validate every test-case block from tests/test-cases.md."""
    path = Path(markdown_path)
    if not path.is_file():
        raise FileNotFoundError(f"Test cases file not found at: {path}")

    content = path.read_text(encoding="utf-8")
    category_matches = list(
        re.finditer(r"^###\s+Category\s+\d+:\s*(.+)$", content, re.MULTILINE)
    )
    block_matches = list(
        re.finditer(r"^####\s+Test Case\b.*$", content, re.MULTILINE)
    )
    if not block_matches:
        raise ValueError("Test Case unknown: invalid field 'heading': no test cases found")

    test_cases: list[TestCase] = []
    seen_ids: set[int] = set()
    for index, block_match in enumerate(block_matches):
        block_end = (
            block_matches[index + 1].start()
            if index + 1 < len(block_matches)
            else len(content)
        )
        block = content[block_match.start():block_end]
        heading = re.match(
            r"^####\s+Test Case\s+(\d+):\s*(\S.*)$",
            block_match.group(0),
        )
        if not heading:
            raise _field_error("unknown", "heading", block_match.group(0))

        case_id = int(heading.group(1))
        title = heading.group(2).strip()
        if case_id in seen_ids:
            raise _field_error(case_id, "id", "duplicate")
        expected_id = len(test_cases) + 1
        if case_id != expected_id:
            raise _field_error(case_id, "id", f"expected sequential ID {expected_id}")
        seen_ids.add(case_id)

        mode = _required_match(
            r"^-\s+\*\*Mode\*\*:\s*(\S+)\s*$",
            block,
            case_id,
            "mode",
        ).group(1).lower()
        if mode not in VALID_MODES:
            raise _field_error(case_id, "mode", f"unsupported value {mode!r}")

        prompt = _required_match(
            r"^-\s+\*\*Prompt\*\*:\s*(.+)$",
            block,
            case_id,
            "prompt",
        ).group(1).strip().strip("`").strip('"').strip("'")
        if not prompt:
            raise _field_error(case_id, "prompt", "empty")

        raw_types = _required_match(
            r"^-\s+\*\*Ambiguity Types\*\*:\s*`?\[(.*?)\]`?\s*$",
            block,
            case_id,
            "ambiguity_types",
        ).group(1)
        ambiguity_types = _parse_ambiguity_types(raw_types)

        expected_behavior = _required_match(
            r"^-\s+\*\*Expected Behavior\*\*:\s*(.*?)\n-\s+\*\*Manual Verification\*\*:",
            block,
            case_id,
            "expected_behavior",
            re.MULTILINE | re.DOTALL,
        ).group(1).strip()
        if not expected_behavior:
            raise _field_error(case_id, "expected_behavior", "empty")

        _required_match(
            r"^-\s+\*\*Manual Verification\*\*:",
            block,
            case_id,
            "manual_verification",
        )
        yaml_block = _required_match(
            r"```yaml\s*\n(assertions:.*?)```",
            block,
            case_id,
            "assertions",
            re.MULTILINE | re.DOTALL,
        ).group(1)
        assertions = _parse_yaml_assertions(yaml_block)
        _validate_assertions(case_id, assertions)

        current_category = "General"
        for category_match in reversed(category_matches):
            if category_match.start() < block_match.start():
                current_category = category_match.group(1).strip()
                break

        test_cases.append(
            TestCase(
                id=case_id,
                title=title,
                category=current_category,
                mode=mode,
                prompt=prompt,
                ambiguity_types=ambiguity_types,
                expected_behavior=expected_behavior,
                assertions=assertions,
            )
        )

    return test_cases


if __name__ == "__main__":
    import sys

    repo_root = Path(__file__).resolve().parent.parent
    cases_file = repo_root / "tests" / "test-cases.md"

    cases = parse_test_cases(cases_file)
    print(f"Successfully parsed {len(cases)} test cases from {cases_file.name}")
    print("=" * 60)
    for c in cases[:3]:  # preview first 3
        print(f"Test #{c.id:02d} [{c.category}] - {c.title}")
        print(f"  Prompt: {c.prompt}")
        print(f"  Ambiguity Types: {c.ambiguity_types}")
        print(f"  Assertions: {json.dumps(c.assertions, indent=4)}")
        print("-" * 60)
    print(f"... and {len(cases) - 3} more cases parsed.")
