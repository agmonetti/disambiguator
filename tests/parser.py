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
    prompt: str
    ambiguity_types: list[str]
    expected_behavior: str
    assertions: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _parse_yaml_assertions(block: str) -> dict[str, Any]:
    """Parse a simple key-value YAML assertions block without external dependencies."""
    assertions: dict[str, Any] = {}
    for line in block.strip().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or line == "assertions:":
            continue

        if ":" not in line:
            continue

        key, val = line.split(":", 1)
        key = key.strip()
        val = val.strip()

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


def parse_test_cases(markdown_path: Path | str) -> list[TestCase]:
    """Parse all 20 test cases and their assertions from tests/test-cases.md."""
    path = Path(markdown_path)
    if not path.is_file():
        raise FileNotFoundError(f"Test cases file not found at: {path}")

    content = path.read_text(encoding="utf-8")

    # Match Category sections (e.g., "### Category 1: Must Stop (Clear Ambiguity)")
    category_pattern = re.compile(
        r"^###\s+Category\s+\d+:\s*(.+)$", re.MULTILINE
    )
    category_matches = list(category_pattern.finditer(content))

    test_cases: list[TestCase] = []

    # Pattern for individual test case blocks with multiline Expected Behavior support
    case_pattern = re.compile(
        r"####\s+Test Case\s+(\d+):\s*(.+?)\n"
        r"-\s+\*\*Prompt\*\*:\s*[`\"]*(.*?)[`\"]*\n"
        r"-\s+\*\*Ambiguity Types\*\*:\s*`?\[(.*?)\]`?\n"
        r"-\s+\*\*Expected Behavior\*\*:\s*([\s\S]*?)\n"
        r"-\s+\*\*Manual Verification\*\*:[^\n]*\n"
        r"\s*```yaml\s*\n(assertions:[\s\S]*?)```",

        re.MULTILINE,
    )


    for match in case_pattern.finditer(content):
        case_id = int(match.group(1))
        title = match.group(2).strip()
        prompt = match.group(3).strip().strip('"').strip("'")
        raw_types = match.group(4).strip()
        expected = match.group(5).strip()
        yaml_block = match.group(6)

        # Parse ambiguity types
        if raw_types:
            ambiguity_types = [
                t.strip().strip('"').strip("'")
                for t in raw_types.split(",")
                if t.strip()
            ]
        else:
            ambiguity_types = []

        # Determine category based on character offset in document
        match_start = match.start()
        current_category = "General"
        for cat_match in reversed(category_matches):
            if cat_match.start() < match_start:
                current_category = cat_match.group(1).strip()
                break

        assertions = _parse_yaml_assertions(yaml_block)

        test_cases.append(
            TestCase(
                id=case_id,
                title=title,
                category=current_category,
                prompt=prompt,
                ambiguity_types=ambiguity_types,
                expected_behavior=expected,
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
