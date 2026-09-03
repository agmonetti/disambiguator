"""Comprehensive test suite for Disambiguator Antigravity CLI integration.

Validates:
1. plugin.json manifest and `agy plugin validate .` execution.
2. .agents/ directory layout (rules and marketplace).
3. hooks.json configuration and lifecycle hook contract.
4. PreInvocation mode tracker (antigravity-mode-tracker.js).
5. Zero-token CLI runtime mode switcher (bin/disambiguator.js).
"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


class TestAntigravityIntegration(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_root = Path(__file__).resolve().parent.parent
        self.xdg_tmp = tempfile.mkdtemp()
        self.test_env = dict(os.environ, XDG_CONFIG_HOME=self.xdg_tmp)

    def tearDown(self) -> None:
        shutil.rmtree(self.xdg_tmp, ignore_errors=True)

    def run_cmd(self, cmd: list[str], **kwargs) -> subprocess.CompletedProcess:
        env = kwargs.pop("env", self.test_env)
        return subprocess.run(cmd, env=env, capture_output=True, text=True, **kwargs)

    def test_plugin_manifest(self) -> None:
        plugin_file = self.repo_root / "plugin.json"
        self.assertTrue(plugin_file.is_file(), "plugin.json must exist in repository root")
        data = json.loads(plugin_file.read_text(encoding="utf-8"))
        self.assertEqual(data.get("name"), "disambiguator")
        self.assertTrue(data.get("version"), "plugin.json must have a version")
        self.assertTrue(data.get("description"), "plugin.json must have a description")

    def test_agents_directory_structure(self) -> None:
        rule_file = self.repo_root / ".agents" / "rules" / "disambiguator.md"
        self.assertTrue(rule_file.is_file(), ".agents/rules/disambiguator.md must exist")
        rule_content = rule_file.read_text(encoding="utf-8")
        self.assertIn("DISAMBIGUATOR — SYSTEM PROMPT", rule_content)

        mkt_file = self.repo_root / ".agents" / "plugins" / "marketplace.json"
        self.assertTrue(mkt_file.is_file(), ".agents/plugins/marketplace.json must exist")
        mkt_data = json.loads(mkt_file.read_text(encoding="utf-8"))
        self.assertEqual(mkt_data.get("name"), "disambiguator")

    def test_hooks_manifest(self) -> None:
        hooks_file = self.repo_root / "hooks.json"
        self.assertTrue(hooks_file.is_file(), "hooks.json must exist in repository root")
        data = json.loads(hooks_file.read_text(encoding="utf-8"))
        self.assertIn("disambiguator-mode-tracker", data)
        tracker_hook = data["disambiguator-mode-tracker"]
        self.assertIn("PreInvocation", tracker_hook)
        handlers = tracker_hook["PreInvocation"]
        self.assertTrue(len(handlers) > 0)
        self.assertEqual(handlers[0].get("type"), "command")
        self.assertIn("antigravity-mode-tracker.js", handlers[0].get("command", ""))

    def test_agy_plugin_validate(self) -> None:
        agy_bin = shutil.which("agy")
        if not agy_bin:
            self.skipTest("agy CLI binary not installed in test environment")

        res = self.run_cmd([agy_bin, "plugin", "validate", "."], cwd=str(self.repo_root))
        self.assertEqual(res.returncode, 0, f"agy plugin validate failed: {res.stderr}\n{res.stdout}")
        self.assertIn("[ok]", res.stdout)
        self.assertIn("hooks       : 1 processed", res.stdout)

    def test_cli_mode_switcher(self) -> None:
        bin_script = self.repo_root / "bin" / "disambiguator.js"
        self.assertTrue(bin_script.is_file(), "bin/disambiguator.js must exist")

        tmp_dir = tempfile.mkdtemp()
        try:
            # 1. Check status in clean tmp dir (default strict)
            res = self.run_cmd(["node", str(bin_script), "status"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Disambiguator current active mode:", res.stdout)

            # 2. Switch to soft
            res = self.run_cmd(["node", str(bin_script), "soft"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Disambiguator mode set to: soft", res.stdout)

            state_file = Path(tmp_dir) / ".disambiguator-mode"
            self.assertTrue(state_file.is_file())
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "soft")

            # 3. Switch back to strict
            res = self.run_cmd(["node", str(bin_script), "strict"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Disambiguator mode set to: strict", res.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "strict")

            # 4. Switch to off
            res = self.run_cmd(["node", str(bin_script), "off"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertIn("Disambiguator mode disabled (off)", res.stdout)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "off")

            # 5. Lockout recovery: switch from off back to soft and then strict
            mock_agents = Path(tmp_dir) / "AGENTS.md"
            mock_agents.write_text("# MODE: off\nRest of rules\n", encoding="utf-8")

            res = self.run_cmd(["node", str(bin_script), "soft"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "soft")
            self.assertIn("# MODE: soft", mock_agents.read_text(encoding="utf-8"))

            res = self.run_cmd(["node", str(bin_script), "strict"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "strict")
            self.assertIn("# MODE: strict", mock_agents.read_text(encoding="utf-8"))

            # 6. Anti-drift protection: files with sync.py header are not mutated directly
            sync_agents = Path(tmp_dir) / "AGENTS.md"
            sync_agents.write_text("<!-- Generated automatically by scripts/sync.py -->\n# MODE: strict\n", encoding="utf-8")
            res = self.run_cmd(["node", str(bin_script), "soft"], cwd=tmp_dir)
            self.assertEqual(res.returncode, 0)
            # File content remains strictly unmutated to prevent git drift
            self.assertIn("# MODE: strict", sync_agents.read_text(encoding="utf-8"))
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)

    def test_hook_pre_invocation_execution(self) -> None:
        hook_script = self.repo_root / "hooks" / "antigravity-mode-tracker.js"
        self.assertTrue(hook_script.is_file())

        tmp_dir = tempfile.mkdtemp()
        try:
            transcript_path = Path(tmp_dir) / "transcript.jsonl"

            # Scenario 1: Normal prompt with no mode command
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "Help me refactor this code"}) + "\n",
                encoding="utf-8",
            )
            payload = {
                "conversationId": "test-conv",
                "workspacePaths": [tmp_dir],
                "transcriptPath": str(transcript_path),
            }

            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("injectSteps", output)
            self.assertTrue(len(output["injectSteps"]) > 0)
            self.assertIn("DISAMBIGUATOR ACTIVE MODE: strict", output["injectSteps"][0]["ephemeralMessage"])

            # Scenario 2: User issues /disambiguator soft command
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "/disambiguator soft"}) + "\n",
                encoding="utf-8",
            )
            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("injectSteps", output)
            self.assertIn("Mode updated to: **soft**", output["injectSteps"][0]["ephemeralMessage"])

            state_file = Path(tmp_dir) / ".disambiguator-mode"
            self.assertTrue(state_file.is_file())
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "soft")

            # Scenario 3: Next turn inherits soft mode
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "Now build the UI"}) + "\n",
                encoding="utf-8",
            )
            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("DISAMBIGUATOR ACTIVE MODE: soft", output["injectSteps"][0]["ephemeralMessage"])

            # Scenario 4: User issues /disambiguator-off command
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "/disambiguator-off"}) + "\n",
                encoding="utf-8",
            )
            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("injectSteps", output)
            self.assertIn("Mode updated to: **off**", output["injectSteps"][0]["ephemeralMessage"])
            self.assertEqual(state_file.read_text(encoding="utf-8").strip(), "off")

            # Scenario 5: Next turn while off indicates gatekeeper is disabled
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "Just do whatever you want"}) + "\n",
                encoding="utf-8",
            )
            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("injectSteps", output)
            self.assertIn("DISAMBIGUATOR ACTIVE MODE: off", output["injectSteps"][0]["ephemeralMessage"])

            # Scenario 6: User queries status with /disambiguator-status
            transcript_path.write_text(
                json.dumps({"type": "USER_INPUT", "content": "/disambiguator-status"}) + "\n",
                encoding="utf-8",
            )
            res = self.run_cmd(["node", str(hook_script)], cwd=str(self.repo_root), input=json.dumps(payload))
            self.assertEqual(res.returncode, 0)
            output = json.loads(res.stdout)
            self.assertIn("injectSteps", output)
            self.assertIn("Current operational mode is: **off**", output["injectSteps"][0]["ephemeralMessage"])
        finally:
            shutil.rmtree(tmp_dir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
