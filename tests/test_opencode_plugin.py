"""Tests for the OpenCode plugin integration."""

import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TestOpenCodePlugin(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.package_json = self.repo_root / "package.json"
        self.plugin_dir = self.repo_root / ".opencode" / "plugins"
        self.plugin_mjs = self.plugin_dir / "disambiguator.mjs"
        self.frontmatter_cjs = self.plugin_dir / "disambiguator-frontmatter.cjs"

    def test_package_json_opencode_manifest(self) -> None:
        self.assertTrue(self.package_json.is_file(), "package.json must exist")
        data = json.loads(self.package_json.read_text(encoding="utf-8"))

        self.assertEqual(
            data.get("main"),
            "./.opencode/plugins/disambiguator.mjs",
            "package.json must specify 'main' pointing to OpenCode plugin",
        )
        exports = data.get("exports", {})
        self.assertEqual(
            exports.get("."),
            "./.opencode/plugins/disambiguator.mjs",
            "exports['.'] must point to OpenCode plugin",
        )
        self.assertEqual(
            exports.get("./plugin"),
            "./.opencode/plugins/disambiguator.mjs",
            "exports['./plugin'] must point to OpenCode plugin",
        )
        self.assertIn(".opencode", data.get("files", []), "'.opencode' must be in files list")
        self.assertIn("opencode-plugin", data.get("keywords", []), "'opencode-plugin' must be in keywords")

    def test_opencode_plugin_files_exist(self) -> None:
        self.assertTrue(self.plugin_mjs.is_file(), "disambiguator.mjs must exist")
        self.assertTrue(self.frontmatter_cjs.is_file(), "disambiguator-frontmatter.cjs must exist")

    def test_opencode_plugin_node_syntax(self) -> None:
        for file_path in (self.plugin_mjs, self.frontmatter_cjs):
            res = subprocess.run(
                ["node", "--check", str(file_path)],
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"Node syntax error in {file_path.name}: {res.stderr}")

    def test_opencode_plugin_behavior_via_node(self) -> None:
        tmp_dir = tempfile.mkdtemp()
        try:
            test_script = f"""
import disambiguatorPlugin from './.opencode/plugins/disambiguator.mjs';
import assert from 'node:assert';
import fs from 'node:fs';
import path from 'node:path';

process.env.XDG_CONFIG_HOME = {json.dumps(tmp_dir)};

const logs = [];
const client = {{
  app: {{
    log: (entry) => logs.push(entry),
  }},
}};

const plugin = await disambiguatorPlugin({{ client }});
assert.strictEqual(typeof plugin.config, 'function');
assert.strictEqual(typeof plugin['experimental.chat.system.transform'], 'function');
assert.strictEqual(typeof plugin['command.execute.before'], 'function');

// 1. Test config hook (registers commands and skills directory)
const configObj = {{}};
await plugin.config(configObj);

assert.ok(configObj.command, 'config.command should exist');
assert.ok(configObj.command.disambiguator, 'disambiguator command registered');
assert.ok(configObj.command['disambiguator-help'], 'disambiguator-help command registered');
assert.strictEqual(configObj.command['disambiguator-strict'], undefined, 'disambiguator-strict should not be registered');
assert.strictEqual(configObj.command['disambiguator-soft'], undefined, 'disambiguator-soft should not be registered');
assert.ok(configObj.command.disambiguator.description, 'command should have description');
assert.ok(configObj.command['disambiguator-help'].description, 'help command should have description');
assert.ok(configObj.command['disambiguator-help'].template, 'help command should have template');

assert.ok(configObj.skills, 'config.skills should exist');
assert.ok(Array.isArray(configObj.skills.paths), 'config.skills.paths should be an array');
assert.ok(
  configObj.skills.paths.some((p) => p.endsWith('skills')),
  'config.skills.paths should contain skills directory'
);

// 2. Test transform hook (default mode is strict)
const output1 = {{ system: ['Base system prompt'] }};
await plugin['experimental.chat.system.transform']({{}}, output1);
assert.ok(output1.system[0].includes('DISAMBIGUATOR — SYSTEM PROMPT'), 'instructions appended');
assert.ok(output1.system[0].includes('# MODE: strict'), 'default mode is strict');

// 3. Test command execution: switch to soft
await plugin['command.execute.before']({{ command: 'disambiguator', arguments: 'soft' }});
const stateFile = path.join({json.dumps(tmp_dir)}, 'opencode', '.disambiguator-active');
assert.strictEqual(fs.readFileSync(stateFile, 'utf8').trim(), 'soft');

const output2 = {{ system: ['Base system prompt'] }};
await plugin['experimental.chat.system.transform']({{}}, output2);
assert.ok(output2.system[0].includes('# MODE: soft'), 'transform reflects soft mode');

// 4. Test command execution: switch back to strict
await plugin['command.execute.before']({{ command: 'disambiguator', arguments: 'strict' }});
assert.strictEqual(fs.readFileSync(stateFile, 'utf8').trim(), 'strict');

// 5. Test command execution: turn off
await plugin['command.execute.before']({{ command: 'disambiguator', arguments: 'off' }});
assert.strictEqual(fs.readFileSync(stateFile, 'utf8').trim(), 'off');

const output3 = {{ system: ['Base system prompt'] }};
await plugin['experimental.chat.system.transform']({{}}, output3);
assert.strictEqual(output3.system[0], 'Base system prompt', 'when off, prompt remains untouched');
"""
            res = subprocess.run(
                ["node", "--input-type=module", "-e", test_script],
                cwd=str(self.repo_root),
                capture_output=True,
                text=True,
            )
            self.assertEqual(res.returncode, 0, f"OpenCode plugin test failed: {res.stderr}\n{res.stdout}")
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
