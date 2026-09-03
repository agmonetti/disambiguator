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

function getWorkspaceStatePath(workspacePath) {
  if (!workspacePath) return null;
  return path.join(workspacePath, '.disambiguator-mode');
}

function readActiveMode(_workspacePath) {
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

function writeActiveMode(mode, _workspacePath) {
  const normalized = String(mode || '').trim().toLowerCase();
  if (!VALID_MODES.has(normalized)) return;

  // Persist strictly to global user config (never write to workspace/repo)
  try {
    const globalPath = getGlobalStatePath();
    fs.mkdirSync(path.dirname(globalPath), { recursive: true });
    fs.writeFileSync(globalPath, normalized, 'utf8');
  } catch (_) {}
}

function parseCommandFromPrompt(prompt) {
  const trimmed = String(prompt || '').trim();
  const lower = trimmed.toLowerCase();

  // Match /disambiguator-strict or /disambiguator:disambiguator-strict
  if (
    lower === '/disambiguator-strict' ||
    lower.startsWith('/disambiguator-strict ') ||
    lower === '/disambiguator:disambiguator-strict' ||
    lower.startsWith('/disambiguator:disambiguator-strict ')
  ) {
    return { type: 'set-mode', mode: 'strict' };
  }

  // Match /disambiguator-soft or /disambiguator:disambiguator-soft
  if (
    lower === '/disambiguator-soft' ||
    lower.startsWith('/disambiguator-soft ') ||
    lower === '/disambiguator:disambiguator-soft' ||
    lower.startsWith('/disambiguator:disambiguator-soft ')
  ) {
    return { type: 'set-mode', mode: 'soft' };
  }

  // Match /disambiguator-off or /disambiguator:disambiguator-off
  if (
    lower === '/disambiguator-off' ||
    lower.startsWith('/disambiguator-off ') ||
    lower === '/disambiguator:disambiguator-off' ||
    lower.startsWith('/disambiguator:disambiguator-off ')
  ) {
    return { type: 'set-mode', mode: 'off' };
  }

  // Match /disambiguator-status or /disambiguator:disambiguator-status
  if (
    lower === '/disambiguator-status' ||
    lower.startsWith('/disambiguator-status ') ||
    lower === '/disambiguator:disambiguator-status' ||
    lower.startsWith('/disambiguator:disambiguator-status ')
  ) {
    return { type: 'status' };
  }

  // Match /disambiguator or /disambiguator:disambiguator
  if (
    lower === '/disambiguator' ||
    lower.startsWith('/disambiguator ') ||
    lower === '/disambiguator:disambiguator' ||
    lower.startsWith('/disambiguator:disambiguator ')
  ) {
    const parts = lower.split(/\s+/);
    const arg = (parts[1] || '').trim();
    if (!arg || arg === 'status') {
      return { type: 'status' };
    }
    if (VALID_MODES.has(arg)) {
      return { type: 'set-mode', mode: arg };
    }
  }

  return null;
}

function getLatestUserPrompt(transcriptPath) {
  if (!transcriptPath || !fs.existsSync(transcriptPath)) return null;

  try {
    const content = fs.readFileSync(transcriptPath, 'utf8');
    const lines = content.split('\n').filter(Boolean);
    for (let i = lines.length - 1; i >= 0; i--) {
      try {
        const entry = JSON.parse(lines[i]);
        if (entry.type === 'USER_INPUT' && entry.content) {
          return entry.content;
        }
      } catch (_) {}
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
      const workspacePath = Array.isArray(payload.workspacePaths) && payload.workspacePaths.length > 0
        ? payload.workspacePaths[0]
        : process.cwd();

      const latestPrompt = getLatestUserPrompt(payload.transcriptPath);
      const command = parseCommandFromPrompt(latestPrompt);

      let currentMode = readActiveMode(workspacePath);
      let modeSwitched = false;
      let isStatusRequest = false;

      if (command) {
        if (command.type === 'set-mode') {
          writeActiveMode(command.mode, workspacePath);
          currentMode = command.mode;
          modeSwitched = true;
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
        injectSteps.push({
          ephemeralMessage: `[DISAMBIGUATOR] Mode updated to: **${currentMode}**. Acknowledge this update in 1 short line: "Disambiguator mode updated: **${currentMode}**." and do not call tools.`
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
