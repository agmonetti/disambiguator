import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import {
  DEFAULT_MODE,
  getDisambiguatorInstructions,
  getGlobalStatePath,
  normalizeMode,
  parseDisambiguatorCommand,
  readPersistedMode,
  resolveSessionMode,
  writePersistedMode,
} from "../index.js";

// Isolate global config during tests
process.env.XDG_CONFIG_HOME = fs.mkdtempSync(path.join(os.tmpdir(), "pi-hlp-cfg-"));

test("normalizeMode normalizes valid modes and rejects unknown ones", () => {
  assert.equal(normalizeMode("strict"), "strict");
  assert.equal(normalizeMode("STRICT"), "strict");
  assert.equal(normalizeMode(" soft "), "soft");
  assert.equal(normalizeMode("off"), "off");
  assert.equal(normalizeMode("invalid"), null);
  assert.equal(normalizeMode(""), null);
});

test("parseDisambiguatorCommand returns status when invoked bare or with status", () => {
  assert.deepEqual(parseDisambiguatorCommand("", "strict"), { type: "status", mode: "strict" });
  assert.deepEqual(parseDisambiguatorCommand("status", "soft"), { type: "status", mode: "soft" });
});

test("parseDisambiguatorCommand parses valid mode targets", () => {
  assert.deepEqual(parseDisambiguatorCommand("soft", "strict"), { type: "set-mode", mode: "soft" });
  assert.deepEqual(parseDisambiguatorCommand("strict", "soft"), { type: "set-mode", mode: "strict" });
  assert.deepEqual(parseDisambiguatorCommand("off", "strict"), { type: "set-mode", mode: "off" });
});

test("parseDisambiguatorCommand rejects invalid modes", () => {
  assert.deepEqual(parseDisambiguatorCommand("super-strict", "strict"), {
    type: "invalid",
    mode: "super-strict",
  });
});

test("resolveSessionMode recovers mode from session entries in reverse order", () => {
  const entries = [
    { type: "message" },
    { type: "custom", customType: "disambiguator-mode", data: { mode: "strict" } },
    { type: "message" },
    { type: "custom", customType: "disambiguator-mode", data: { mode: "soft" } },
  ];
  assert.equal(resolveSessionMode(entries, "strict"), "soft");
});

test("resolveSessionMode falls back to default when no entry exists", () => {
  assert.equal(resolveSessionMode([], DEFAULT_MODE), "strict");
  assert.equal(resolveSessionMode(null, DEFAULT_MODE), "strict");
});

test("getDisambiguatorInstructions dynamically replaces # MODE: setting", () => {
  const strictPrompt = getDisambiguatorInstructions("strict");
  assert.match(strictPrompt, /# MODE:\s*strict/);

  const softPrompt = getDisambiguatorInstructions("soft");
  assert.match(softPrompt, /# MODE:\s*soft/);
});


test("getGlobalStatePath returns expected disambiguator mode path", () => {
  const globalPath = getGlobalStatePath();
  assert.ok(globalPath.endsWith(path.join("disambiguator", "mode")));
});

test("writePersistedMode and readPersistedMode persist and read global state without repo pollution", () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pi-ext-test-"));
  const origXdg = process.env.XDG_CONFIG_HOME;
  try {
    process.env.XDG_CONFIG_HOME = tmpDir;

    // Before writing, fallback to default
    const initialMode = readPersistedMode(tmpDir);
    assert.equal(initialMode, "strict");

    // Write soft mode
    const written = writePersistedMode("soft", tmpDir);
    assert.equal(written, true);

    // Workspace must remain 100% clean (no .disambiguator-mode)
    const modeFile = path.join(tmpDir, ".disambiguator-mode");
    assert.strictEqual(fs.existsSync(modeFile), false, "Must never write .disambiguator-mode to workspace");

    // Global config must be updated
    const globalFile = path.join(tmpDir, "disambiguator", "mode");
    assert.ok(fs.existsSync(globalFile), "Must write to global config");
    assert.equal(fs.readFileSync(globalFile, "utf-8"), "soft");

    // Read back
    assert.equal(readPersistedMode(tmpDir), "soft");

    // Rejects invalid mode
    assert.equal(writePersistedMode("invalid-mode", tmpDir), false);
  } finally {
    if (origXdg !== undefined) process.env.XDG_CONFIG_HOME = origXdg;
    else delete process.env.XDG_CONFIG_HOME;
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

