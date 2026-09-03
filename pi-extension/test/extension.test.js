import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";

import disambiguatorExtension from "../index.js";

// Isolate global config during tests
process.env.XDG_CONFIG_HOME = fs.mkdtempSync(path.join(os.tmpdir(), "pi-ext-cfg-"));

function createPiHarness() {
  const events = new Map();
  const commands = new Map();
  const appendedEntries = [];

  const pi = {
    on(eventName, handler) {
      events.set(eventName, handler);
    },
    registerCommand(name, options) {
      commands.set(name, options);
    },
    appendEntry(customType, data) {
      appendedEntries.push({ customType, data });
    },
  };

  disambiguatorExtension(pi);
  return { events, commands, appendedEntries };
}

function createCommandContext(overrides = {}) {
  const notifications = [];
  const statusEntries = new Map();
  const tmpWorkspace = fs.mkdtempSync(path.join(os.tmpdir(), "pi-cmd-ws-"));

  return {
    cwd: tmpWorkspace,
    isIdle: () => true,
    sessionManager: { getEntries: () => [], getBranch: () => [] },
    ui: {
      theme: {
        fg: (_color, text) => text,
      },
      notify(msg, type) {
        notifications.push({ msg, type });
      },
      setStatus(key, text) {
        statusEntries.set(key, text);
      },
    },
    notifications,
    statusEntries,
    ...overrides,
  };
}

test("extension registers /disambiguator commands and lifecycle listeners", () => {
  const { events, commands } = createPiHarness();

  assert.ok(commands.has("disambiguator"), "Should register /disambiguator command");
  assert.ok(commands.has("disambiguator-strict"), "Should register /disambiguator-strict command");
  assert.ok(commands.has("disambiguator-soft"), "Should register /disambiguator-soft command");
  assert.ok(events.has("input"), "Should register input listener");
  assert.ok(events.has("session_start"), "Should register session_start listener");
  assert.ok(events.has("agent_start"), "Should register agent_start listener");
  assert.ok(events.has("agent_end"), "Should register agent_end listener");
  assert.ok(events.has("before_agent_start"), "Should register before_agent_start listener");
});

test("getArgumentCompletions returns expected items and filters prefix", () => {
  const { commands } = createPiHarness();
  const cmd = commands.get("disambiguator");

  const allCompletions = cmd.getArgumentCompletions("");
  assert.equal(allCompletions.length, 4, "Should offer 4 options (strict, soft, status, off)");

  const sCompletions = cmd.getArgumentCompletions("s");
  const values = sCompletions.map((item) => item.value);
  assert.ok(values.includes("strict"));
  assert.ok(values.includes("soft"));
  assert.ok(values.includes("status"));
  assert.ok(!values.includes("off"));

  const strictOnly = cmd.getArgumentCompletions("str");
  assert.equal(strictOnly.length, 1);
  assert.equal(strictOnly[0].value, "strict");
});

test("handler toggles mode, appends entry, and updates status", async () => {
  const { commands, appendedEntries } = createPiHarness();
  const cmd = commands.get("disambiguator");
  const ctx = createCommandContext();

  await cmd.handler("soft", ctx);

  assert.equal(appendedEntries.length, 1);
  assert.deepEqual(appendedEntries[0], {
    customType: "disambiguator-mode",
    data: { mode: "soft" },
  });
  assert.equal(ctx.notifications.length, 1);
  assert.match(ctx.notifications[0].msg, /Disambiguator mode updated: soft/);
  assert.match(ctx.statusEntries.get("disambiguator"), /Soft/);
});

test("handler reports status", async () => {
  const { commands } = createPiHarness();
  const cmd = commands.get("disambiguator");
  const ctx = createCommandContext();

  await cmd.handler("status", ctx);

  assert.equal(ctx.notifications.length, 1);
  assert.match(ctx.notifications[0].msg, /Disambiguator current mode: strict/);
});

test("before_agent_start injects prompt with active mode", async () => {
  const { events, commands } = createPiHarness();
  const beforeStart = events.get("before_agent_start");
  const cmd = commands.get("disambiguator");
  const ctx = createCommandContext();

  // Test strict mode (default)
  const resultStrict = await beforeStart({ systemPrompt: "Existing prompt" });
  assert.match(resultStrict.systemPrompt, /Existing prompt/);
  assert.match(resultStrict.systemPrompt, /# MODE:\s*strict/);

  // Switch to soft mode
  await cmd.handler("soft", ctx);
  const resultSoft = await beforeStart({ systemPrompt: "Existing prompt" });
  assert.match(resultSoft.systemPrompt, /# MODE:\s*soft/);
});

test("before_agent_start updates existing inlined prompt without duplicating", async () => {
  const { events, commands } = createPiHarness();
  const beforeStart = events.get("before_agent_start");
  const cmd = commands.get("disambiguator");
  const ctx = createCommandContext();

  const existingPrompt = "# DISAMBIGUATOR — SYSTEM PROMPT\n# MODE: strict\nRest of prompt";
  await cmd.handler("soft", ctx);

  const result = await beforeStart({ systemPrompt: existingPrompt });
  assert.match(result.systemPrompt, /# MODE:\s*soft/);
  // Ensure it didn't duplicate the header
  const occurrences = (result.systemPrompt.match(/DISAMBIGUATOR — SYSTEM PROMPT/g) || []).length;
  assert.equal(occurrences, 1, "Should not duplicate prompt section");

  // Verify transition from off mode
  const offPrompt = "# DISAMBIGUATOR — SYSTEM PROMPT\n# MODE: off\nRest of prompt";
  await cmd.handler("strict", ctx);
  const resultFromOff = await beforeStart({ systemPrompt: offPrompt });
  assert.match(resultFromOff.systemPrompt, /# MODE:\s*strict/);
});

test("before_agent_start neutralizes inlined prompt when mode is off", async () => {
  const { events, commands } = createPiHarness();
  const beforeStart = events.get("before_agent_start");
  const cmd = commands.get("disambiguator");
  const ctx = createCommandContext();

  await cmd.handler("off", ctx);

  // 1. If existing prompt has inlined AGENTS.md, rewrite to # MODE: off
  const existingPrompt = "# DISAMBIGUATOR — SYSTEM PROMPT\n# MODE: strict\nRest of prompt";
  const resultInlined = await beforeStart({ systemPrompt: existingPrompt });
  assert.ok(resultInlined && resultInlined.systemPrompt, "Should return updated systemPrompt");
  assert.match(resultInlined.systemPrompt, /# MODE:\s*off/);
  assert.doesNotMatch(resultInlined.systemPrompt, /# MODE:\s*strict/);

  // 2. If prompt does not have inlined AGENTS.md, return undefined (no prompt injection)
  const plainPrompt = "Just a standard system prompt";
  const resultPlain = await beforeStart({ systemPrompt: plainPrompt });
  assert.strictEqual(resultPlain, undefined, "Should not inject disambiguator instructions when off");
});

test("direct commands switch mode instantly", async () => {
  const { commands } = createPiHarness();
  const cmdSoft = commands.get("disambiguator-soft");
  const cmdStrict = commands.get("disambiguator-strict");
  const ctx = createCommandContext();

  await cmdSoft.handler("", ctx);
  assert.match(ctx.statusEntries.get("disambiguator"), /Soft/);

  await cmdStrict.handler("", ctx);
  assert.match(ctx.statusEntries.get("disambiguator"), /Strict/);
});

test("input event intercepts skill triggers and skips LLM processing", async () => {
  const { events } = createPiHarness();
  const inputHandler = events.get("input");
  const ctx = createCommandContext();

  // Intercept /skill:disambiguator-soft
  const resSoft = await inputHandler({ text: "/skill:disambiguator-soft" }, ctx);
  assert.deepEqual(resSoft, { action: "handled" }, "Must return handled to skip LLM call");
  assert.match(ctx.statusEntries.get("disambiguator"), /Soft/);

  // Intercept /skill:disambiguator-strict
  const resStrict = await inputHandler({ text: "/skill:disambiguator-strict" }, ctx);
  assert.deepEqual(resStrict, { action: "handled" }, "Must return handled to skip LLM call");
  assert.match(ctx.statusEntries.get("disambiguator"), /Strict/);

  // Regular user messages pass through
  const resRegular = await inputHandler({ text: "Hello world" }, ctx);
  assert.deepEqual(resRegular, { action: "continue" }, "Regular text must continue to agent");
});

test("session_start recovers mode from workspace .disambiguator-mode when entries are empty", async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pi-ext-session-"));
  try {
    fs.writeFileSync(path.join(tmpDir, ".disambiguator-mode"), "soft", "utf-8");

    const { events } = createPiHarness();
    const sessionStart = events.get("session_start");
    const beforeStart = events.get("before_agent_start");
    const ctx = createCommandContext({ cwd: tmpDir });

    await sessionStart({}, ctx);
    assert.match(ctx.statusEntries.get("disambiguator"), /Soft/);

    const res = await beforeStart({ systemPrompt: "Existing prompt" });
    assert.match(res.systemPrompt, /# MODE:\s*soft/);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("session_start prioritizes session entries over workspace file", async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pi-ext-priority-"));
  try {
    fs.writeFileSync(path.join(tmpDir, ".disambiguator-mode"), "soft", "utf-8");

    const { events } = createPiHarness();
    const sessionStart = events.get("session_start");
    const ctx = createCommandContext({
      cwd: tmpDir,
      sessionManager: {
        getBranch: () => [
          { type: "custom", customType: "disambiguator-mode", data: { mode: "strict" } },
        ],
      },
    });

    await sessionStart({}, ctx);
    assert.match(ctx.statusEntries.get("disambiguator"), /Strict/);
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

test("command handler writes mode to workspace disk", async () => {
  const tmpDir = fs.mkdtempSync(path.join(os.tmpdir(), "pi-ext-write-"));
  try {
    const { commands } = createPiHarness();
    const cmd = commands.get("disambiguator");
    const ctx = createCommandContext({ cwd: tmpDir });

    await cmd.handler("soft", ctx);

    const modeFile = path.join(tmpDir, ".disambiguator-mode");
    assert.ok(fs.existsSync(modeFile), "Must write .disambiguator-mode to workspace");
    assert.equal(fs.readFileSync(modeFile, "utf-8"), "soft");
  } finally {
    fs.rmSync(tmpDir, { recursive: true, force: true });
  }
});

