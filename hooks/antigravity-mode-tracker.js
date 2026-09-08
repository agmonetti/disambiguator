#!/usr/bin/env node
/**
 * Disambiguator — Antigravity Lifecycle Hook (PreInvocation)
 *
 * Runs before each model invocation in Antigravity CLI (`agy`) and Antigravity IDE.
 * 1. Reads the hook context from stdin (transcriptPath, workspacePaths, etc.).
 * 2. Inspects recent user inputs in transcript.jsonl for mode switch commands.
 * 3. Persists the active mode to disk so it survives turns and sessions.
 * 4. Injects an ephemeral system reminder into the model's context for deterministic enforcement.
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const DEFAULT_MODE = 'strict';
const VALID_MODES = new Set(['strict', 'soft', 'off']);

function getGlobalStatePath() {
  return path.join(
    process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
    'disambiguator',
    'mode'
  );
}


function readActiveMode() {
  // Global state only (never pollutes workspace)
  try {
    const globalPath = getGlobalStatePath();
    if (fs.existsSync(globalPath)) {
      const raw = fs.readFileSync(globalPath, 'utf8').trim().toLowerCase();
      if (VALID_MODES.has(raw)) return raw;
    }
  } catch (_) {}

  return DEFAULT_MODE;
}

function writeActiveMode(mode) {
  const normalized = String(mode || '').trim().toLowerCase();
  if (!VALID_MODES.has(normalized)) return false;

  // Persist strictly to global user config (never write to workspace/repo)
  try {
    const globalPath = getGlobalStatePath();
    fs.mkdirSync(path.dirname(globalPath), { recursive: true });
    fs.writeFileSync(globalPath, normalized, 'utf8');
    return true;
  } catch (err) {
    try {
      process.stderr.write(`[Disambiguator] Failed to persist active mode: ${err.message}\n`);
    } catch (_) {}
    return false;
  }
}

function parseCommandFromPrompt(prompt) {
  const trimmed = String(prompt || '').trim();
  const lower = trimmed.toLowerCase();

  // Strict matching for hyphenated command forms (no arbitrary trailing text)
  if (
    lower === '/disambiguator-strict' ||
    lower === '/disambiguator:disambiguator-strict'
  ) {
    return { type: 'set-mode', mode: 'strict' };
  }

  if (
    lower === '/disambiguator-soft' ||
    lower === '/disambiguator:disambiguator-soft'
  ) {
    return { type: 'set-mode', mode: 'soft' };
  }

  if (
    lower === '/disambiguator-off' ||
    lower === '/disambiguator:disambiguator-off'
  ) {
    return { type: 'set-mode', mode: 'off' };
  }

  if (
    lower === '/disambiguator-status' ||
    lower === '/disambiguator:disambiguator-status'
  ) {
    return { type: 'status' };
  }

  // Strict matching for /disambiguator [mode] (at most 2 whitespace-separated tokens)
  if (
    lower === '/disambiguator' ||
    lower.startsWith('/disambiguator ') ||
    lower === '/disambiguator:disambiguator' ||
    lower.startsWith('/disambiguator:disambiguator ')
  ) {
    const parts = lower.split(/\s+/).filter(Boolean);
    if (parts.length === 1) {
      return { type: 'status' };
    }
    if (parts.length === 2) {
      const arg = parts[1];
      if (arg === 'status') {
        return { type: 'status' };
      }
      if (VALID_MODES.has(arg)) {
        return { type: 'set-mode', mode: arg };
      }
    }
  }

  return null;
}

function getLatestUserPrompt(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return null;

  try {
    const stats = fs.statSync(transcriptPath);
    if (stats.size === 0) return null;

    // Read backwards in 64KB chunks to avoid memory exhaustion on massive transcripts (DoS prevention)
    const CHUNK_SIZE = 64 * 1024;
    const fd = fs.openSync(transcriptPath, 'r');
    try {
      let position = stats.size;
      let leftover = '';

      while (position > 0) {
        const bytesToRead = Math.min(CHUNK_SIZE, position);
        position -= bytesToRead;
        const buffer = Buffer.alloc(bytesToRead);
        fs.readSync(fd, buffer, 0, bytesToRead, position);
        const text = buffer.toString('utf8') + leftover;
        const lines = text.split('\n');

        // First line is incomplete if position > 0
        leftover = position > 0 ? (lines.shift() || '') : '';

        for (let i = lines.length - 1; i >= 0; i--) {
          const line = lines[i].trim();
          if (!line) continue;
          try {
            const entry = JSON.parse(line);
            if (entry.type === 'USER_INPUT' && entry.content) {
              return entry.content;
            }
          } catch (_) {}
        }
      }
    } finally {
      fs.closeSync(fd);
    }
  } catch (_) {}

  return null;
}

function main() {
  let input = '';
  let finished = false;

  function finish() {
    if (finished) return;
    finished = true;

    try {
      const payload = input ? JSON.parse(input.replace(/^\uFEFF/, '')) : {};

      const latestPrompt = getLatestUserPrompt(payload.transcriptPath);
      const command = parseCommandFromPrompt(latestPrompt);

      const persistedMode = readActiveMode();
      let currentMode = persistedMode;
      let modeSwitched = false;
      let persistenceFailed = false;
      let isStatusRequest = false;

      if (command) {
        if (command.type === 'set-mode') {
          const persisted = writeActiveMode(command.mode);
          currentMode = command.mode;
          modeSwitched = true;
          persistenceFailed = !persisted;
        } else if (command.type === 'status') {
          isStatusRequest = true;
        }
      }

      const injectSteps = [];

      if (isStatusRequest) {
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR] Current operational mode is: **${currentMode}** (default: ${DEFAULT_MODE}). Acknowledge in 1 short line: "Disambiguator current active mode: **${currentMode}** (default: ${DEFAULT_MODE})." and do not call tools.`
        });
      } else if (modeSwitched) {
        const persistenceNotice = persistenceFailed
          ? ` Persistence failed; this invocation uses **${currentMode}**, but the next invocation will return to the last saved mode **${persistedMode}**.`
          : '';
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR] Mode updated to: **${currentMode}**.${persistenceNotice} Acknowledge the update and do not call tools.`
        });
      } else if (currentMode === 'off') {
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR ACTIVE MODE: off] Disambiguator cognitive gatekeeper is currently disabled. Do not halt or prompt for multiple-choice disambiguation; proceed directly with normal execution.`
        });
      } else if (currentMode === 'soft') {
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR ACTIVE MODE: soft] Halt ONLY on Type A (Pure Subjectivity) and High-Risk Type B (Destructive/Large Scope). For Type C (Context Assumptions) and Low-Risk Type B, adopt the safest standard approach (Option a), state it in a 1-line note, and proceed immediately with execution.`
        });
      } else if (currentMode === 'strict') {
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR ACTIVE MODE: strict] Halt and clarify on ALL Type A, Type B, and Type C ambiguities before executing any tools or modifying code.`
        });
      }

      process.stdout.write(JSON.stringify({ injectSteps }));
    } catch (_) {
      process.stdout.write(JSON.stringify({ injectSteps: [] }));
    }
  }

  process.stdin.setEncoding('utf8');
  process.stdin.on('data', (chunk) => { input += chunk; });
  process.stdin.on('end', finish);
  process.stdin.on('error', () => { finish(); process.exit(0); });
  setTimeout(() => { finish(); process.exit(0); }, 3000).unref();
}

if (require.main === module) {
  main();
}

module.exports = {
  readActiveMode,
  writeActiveMode,
  parseCommandFromPrompt,
  getLatestUserPrompt,
};
