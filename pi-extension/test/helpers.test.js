import assert from "node:assert/strict";
import test from "node:test";

import {
  DEFAULT_MODE,
  getDisambiguatorInstructions,
  normalizeMode,
  parseDisambiguatorCommand,
  resolveSessionMode,
} from "../index.js";

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
