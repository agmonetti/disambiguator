#!/usr/bin/env node
/**
 * Disambiguator CLI — Zero-Token Runtime Mode Switcher
 *
 * Allows toggling Disambiguator between strict, soft, and off modes locally
 * without sending prompts or burning LLM tokens.
 *
 * Usage:
 *   npx @agmonetti/disambiguator [strict|soft|status|off]
 */

const fs = require('fs');
const os = require('os');
const path = require('path');

const VALID_MODES = ['strict', 'soft', 'off'];
const DEFAULT_MODE = 'strict';

function getGlobalStatePath() {
  return path.join(
    process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
    'disambiguator',
    'mode'
  );
}

function readMode(_cwd = process.cwd()) {
  // Global state only (never pollutes workspace)
  const globalPath = getGlobalStatePath();
  if (fs.existsSync(globalPath)) {
    try {
      const mode = fs.readFileSync(globalPath, 'utf8').trim().toLowerCase();
      if (VALID_MODES.includes(mode)) return mode;
    } catch (_) {}
  }

  return DEFAULT_MODE;
}

function writeMode(mode, cwd = process.cwd()) {
  const normalized = String(mode || '').trim().toLowerCase();
  if (!VALID_MODES.includes(normalized)) return false;

  // Persist strictly to global config (never write to workspace/repo)
  try {
    const globalPath = getGlobalStatePath();
    fs.mkdirSync(path.dirname(globalPath), { recursive: true });
    fs.writeFileSync(globalPath, normalized, 'utf8');
  } catch (_) {}

  // If local AGENTS.md or .agents/rules/disambiguator.md exists in cwd, update # MODE:
  // Skip modifying files that are managed by scripts/sync.py in this repo to prevent drift
  const isSyncRepo = fs.existsSync(path.join(cwd, 'scripts', 'sync.py'));
  if (!isSyncRepo) {
    const filesToUpdate = [
      path.join(cwd, 'AGENTS.md'),
      path.join(cwd, '.agents', 'rules', 'disambiguator.md'),
    ];

    for (const file of filesToUpdate) {
      if (fs.existsSync(file)) {
        try {
          const content = fs.readFileSync(file, 'utf8');
          const updated = content.replace(/# MODE:\s*(strict|soft|off)/, `# MODE: ${normalized}`);
          if (updated !== content) {
            fs.writeFileSync(file, updated, 'utf8');
          }
        } catch (_) {}
      }
    }
  }

  return true;
}

function printUsage() {
  console.log(`Disambiguator CLI — Zero-Token Runtime Mode Switcher

Usage:
  disambiguator [mode]

Modes:
  strict   Halt on all Type A, B, and C ambiguities before taking action (default)
  soft     Halt on Type A & high-risk Type B; assume safest path for Type C & low-risk Type B
  status   Show current operational mode
  off      Temporarily disable Disambiguator

Examples:
  npx @agmonetti/disambiguator strict
  npx @agmonetti/disambiguator soft
  npx @agmonetti/disambiguator status
`);
}

function main() {
  const args = process.argv.slice(2);
  const command = (args[0] || '').trim().toLowerCase();

  if (!command || command === 'status') {
    const current = readMode();
    console.log(`Disambiguator current active mode: ${current} (default: ${DEFAULT_MODE})`);
    process.exit(0);
  }

  if (command === '--help' || command === '-h' || command === 'help') {
    printUsage();
    process.exit(0);
  }

  if (VALID_MODES.includes(command)) {
    writeMode(command);
    if (command === 'strict') {
      console.log('✔ Disambiguator mode set to: strict');
      console.log('  All ambiguities (Type A, B, and C) will halt execution for clarification before modifying code.');
    } else if (command === 'soft') {
      console.log('✔ Disambiguator mode set to: soft');
      console.log('  Type A & high-risk Type B halt; Type C & low-risk Type B will assume the safest path and proceed.');
    } else if (command === 'off') {
      console.log('✔ Disambiguator mode disabled (off).');
    }
    process.exit(0);
  }

  console.error(`Error: Unknown mode '${command}'. Valid options: strict, soft, status, off`);
  process.exit(1);
}

if (require.main === module) {
  main();
}

module.exports = {
  readMode,
  writeMode,
  VALID_MODES,
  DEFAULT_MODE,
};
