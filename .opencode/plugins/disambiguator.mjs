// disambiguator — OpenCode plugin.
//
// Injects the Disambiguator cognitive gatekeeper into every chat's system
// prompt at the active mode (strict|soft), persists mode switches, and
// registers slash commands and skills so they work when the package is
// installed from npm or loaded from a local checkout.
//
// Add to your opencode.json:
//   { "plugin": ["@agmonetti/disambiguator"] }
// Or from a checkout:
//   { "plugin": ["./.opencode/plugins/disambiguator.mjs"] }

import { createRequire } from 'module';
import fs from 'fs';
import os from 'os';
import path from 'path';
import { fileURLToPath } from 'url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// CommonJS bridge for frontmatter parsing without exposing multiple plugin exports
const require = createRequire(import.meta.url);
const { parseCommandFile } = require('./disambiguator-frontmatter.cjs');

const systemPromptPath = path.resolve(__dirname, '../../system-prompt.md');
const disambiguatorSkillsDir = path.resolve(__dirname, '../../skills');

function getStatePath() {
  return path.join(
    process.env.XDG_CONFIG_HOME || path.join(os.homedir(), '.config'),
    'opencode',
    '.disambiguator-active'
  );
}

const DEFAULT_MODE = 'strict';
const VALID_MODES = new Set(['strict', 'soft', 'off']);

function normalizeMode(mode) {
  const normalized = String(mode || '').trim().toLowerCase();
  return VALID_MODES.has(normalized) ? normalized : null;
}

function readMode() {
  try {
    const statePath = getStatePath();
    if (fs.existsSync(statePath)) {
      const raw = fs.readFileSync(statePath, 'utf8').trim().toLowerCase();
      return normalizeMode(raw) || DEFAULT_MODE;
    }
  } catch (e) {}
  return DEFAULT_MODE;
}

function writeMode(mode) {
  const normalized = normalizeMode(mode);
  if (!normalized) return false;
  try {
    const statePath = getStatePath();
    fs.mkdirSync(path.dirname(statePath), { recursive: true });
    fs.writeFileSync(statePath, normalized, 'utf8');
    return true;
  } catch (e) {
    return false;
  }
}

let cachedSystemPrompt = null;
function getInstructions(mode) {
  if (!cachedSystemPrompt) {
    if (fs.existsSync(systemPromptPath)) {
      cachedSystemPrompt = fs.readFileSync(systemPromptPath, 'utf8');
    } else {
      cachedSystemPrompt = '';
    }
  }
  if (!cachedSystemPrompt) return '';
  return cachedSystemPrompt.replace(/# MODE:\s*(strict|soft|off)/, `# MODE: ${mode}`);
}

export default async ({ client } = {}) => {
  const log = (level, message) => {
    try {
      client?.app?.log?.({ body: { service: 'disambiguator', level, message } });
    } catch (e) {}
  };

  const persistMode = (mode) => {
    if (writeMode(mode)) {
      log('info', `disambiguator ${mode}`);
      return;
    }
    log('error', `disambiguator ${mode} could not be persisted`);
  };

  return {
    // Register slash commands + skills directory
    config: async (config) => {
      if (!config.command) config.command = {};
      const commandDir = path.join(__dirname, '..', 'command');
      try {
        if (fs.existsSync(commandDir)) {
          for (const file of fs.readdirSync(commandDir).filter((f) => f.endsWith('.md'))) {
            const name = path.basename(file, '.md');
            const parsed = parseCommandFile(path.join(commandDir, file));
            if (parsed) config.command[name] = parsed;
          }
        }
      } catch (e) {}

      config.skills = config.skills || {};
      config.skills.paths = config.skills.paths || [];
      if (!config.skills.paths.includes(disambiguatorSkillsDir)) {
        config.skills.paths.push(disambiguatorSkillsDir);
      }
    },

    // Keep every preinjected ruleset aligned with the persisted mode.
    'experimental.chat.system.transform': async (_input, output) => {
      if (!output) return;

      const mode = readMode();
      const marker = 'DISAMBIGUATOR — SYSTEM PROMPT';
      const rewriteMode = (value) => value.replace(
        /# MODE:\s*(strict|soft|off)/,
        `# MODE: ${mode}`
      );

      if (Array.isArray(output.system)) {
        let alreadyInjected = false;
        for (let index = 0; index < output.system.length; index += 1) {
          const entry = output.system[index];
          if (typeof entry === 'string' && entry.includes(marker)) {
            output.system[index] = rewriteMode(entry);
            alreadyInjected = true;
          }
        }

        if (mode === 'off' || alreadyInjected) return;
        const instructions = getInstructions(mode);
        if (!instructions) return;
        const lastIndex = output.system.length - 1;
        if (lastIndex >= 0 && typeof output.system[lastIndex] === 'string') {
          output.system[lastIndex] += '\n\n' + instructions;
        } else {
          output.system.push(instructions);
        }
        return;
      }

      if (typeof output.system === 'string') {
        if (output.system.includes(marker)) {
          output.system = rewriteMode(output.system);
          return;
        }
        if (mode === 'off') return;
        const instructions = getInstructions(mode);
        if (instructions) output.system += '\n\n' + instructions;
        return;
      }

      log('error', 'Unsupported OpenCode system prompt shape; leaving it unchanged.');
    },

    // Persist mode switches from slash commands
    'command.execute.before': async (input) => {
      if (!input) return;
      if (input.command === 'disambiguator') {
        const args = String(input.arguments || '').trim().toLowerCase();
        if (!args || args === 'status') {
          const current = readMode();
          log('info', `disambiguator status: ${current}`);
          return;
        }
        const mode = normalizeMode(args);
        if (mode) persistMode(mode);
      } else if (input.command === 'disambiguator-strict') {
        persistMode('strict');
      } else if (input.command === 'disambiguator-soft') {
        persistMode('soft');
      } else if (input.command === 'disambiguator-off') {
        persistMode('off');
      }
    },
  };
};
