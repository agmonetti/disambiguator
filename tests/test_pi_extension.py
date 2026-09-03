"""Tests for the Pi Agent Harness extension."""

import json
from pathlib import Path
import subprocess
import unittest


class TestPiExtension(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.package_json = self.repo_root / "package.json"
        self.ext_dir = self.repo_root / "pi-extension"
        self.ext_package = self.ext_dir / "package.json"
        self.ext_index = self.ext_dir / "index.js"

    def test_package_json_pi_manifest(self) -> None:
        self.assertTrue(self.package_json.is_file(), "package.json must exist")
        data = json.loads(self.package_json.read_text(encoding="utf-8"))
        self.assertIn("pi", data, "package.json must declare 'pi' configuration")
        self.assertIn("extensions", data["pi"], "pi block must declare 'extensions'")
        self.assertIn("./pi-extension/index.js", data["pi"]["extensions"])
        self.assertIn("skills", data["pi"], "pi block must declare 'skills'")
        self.assertIn("./skills", data["pi"]["skills"])

        # Check required files in 'files'
        for expected in ("pi-extension", "commands", ".opencode", "system-prompt.md"):
            self.assertIn(expected, data.get("files", []), f"'{expected}' must be in package.json files")

    def test_pi_extension_files_exist(self) -> None:
        self.assertTrue(self.ext_package.is_file(), "pi-extension/package.json must exist")
        self.assertTrue(self.ext_index.is_file(), "pi-extension/index.js must exist")

        ext_data = json.loads(self.ext_package.read_text(encoding="utf-8"))
        self.assertEqual(ext_data.get("type"), "module", "pi-extension must be type: module")

    def test_pi_extension_node_syntax(self) -> None:
        res = subprocess.run(
            ["node", "--check", str(self.ext_index)],
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Node syntax error in index.js: {res.stderr}")

    def test_pi_extension_logic_via_node(self) -> None:
        test_script = (
            "import { normalizeMode, resolveSessionMode, getDisambiguatorInstructions, DEFAULT_MODE } "
            "from './pi-extension/index.js';\n"
            "import assert from 'node:assert';\n"
            "\n"
            "assert.strictEqual(DEFAULT_MODE, 'strict');\n"
            "assert.strictEqual(normalizeMode('STRICT'), 'strict');\n"
            "assert.strictEqual(normalizeMode('Soft'), 'soft');\n"
            "assert.strictEqual(normalizeMode('off'), 'off');\n"
            "assert.strictEqual(normalizeMode('invalid'), null);\n"
            "\n"
            "// Session mode resolution\n"
            "const entries = [\n"
            "  { type: 'message' },\n"
            "  { type: 'custom', customType: 'disambiguator-mode', data: { mode: 'soft' } },\n"
            "];\n"
            "assert.strictEqual(resolveSessionMode(entries), 'soft');\n"
            "assert.strictEqual(resolveSessionMode([]), 'strict');\n"
            "\n"
            "// Prompt instruction generation\n"
            "const strictPrompt = getDisambiguatorInstructions('strict');\n"
            "assert.ok(strictPrompt.includes('# MODE: strict'), 'Should contain # MODE: strict');\n"
            "const softPrompt = getDisambiguatorInstructions('soft');\n"
            "assert.ok(softPrompt.includes('# MODE: soft'), 'Should contain # MODE: soft');\n"
        )
        res = subprocess.run(
            ["node", "--input-type=module", "-e", test_script],
            cwd=str(self.repo_root),
            capture_output=True,
            text=True,
        )
        self.assertEqual(res.returncode, 0, f"Node logic test failed: {res.stderr}")


if __name__ == "__main__":
    unittest.main()
