import assert from "node:assert/strict";
import test from "node:test";

import disambiguatorExtension from "../index.js";

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

  return {
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

test("extension registers /disambiguator command and lifecycle listeners", () => {
  const { events, commands } = createPiHarness();

  assert.ok(commands.has("disambiguator"), "Should register /disambiguator command");
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
});
