import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const SYSTEM_PROMPT_PATH = path.resolve(__dirname, "..", "system-prompt.md");

export const DEFAULT_MODE = "strict";
export const RUNTIME_MODES = ["strict", "soft", "off"];

export const DISAMBIGUATOR_COMMAND_DESCRIPTION = "Set mode: strict|soft|off. Commands: status, strict, soft, off";

export const MODE_DESCRIPTIONS = {
  strict: "All ambiguities (Type A, B, and C) will halt execution for clarification before any changes are made (default).",
  soft: "Halt on Type A & high-risk Type B; assume safest path for Type C & low-risk Type B.",
  status: "Show current Disambiguator operational mode.",
  off: "Temporarily disable Disambiguator cognitive gatekeeper.",
};

let cachedSystemPrompt = null;

export function getCanonicalPrompt() {
  if (!cachedSystemPrompt) {
    if (fs.existsSync(SYSTEM_PROMPT_PATH)) {
      cachedSystemPrompt = fs.readFileSync(SYSTEM_PROMPT_PATH, "utf-8");
    } else {
      cachedSystemPrompt = "";
    }
  }
  return cachedSystemPrompt;
}

export function getDisambiguatorInstructions(mode = DEFAULT_MODE) {
  const basePrompt = getCanonicalPrompt();
  if (!basePrompt) return "";
  return basePrompt.replace(/# MODE:\s*(strict|soft|off)/, `# MODE: ${mode}`);
}

export function normalizeMode(mode) {
  const normalized = String(mode || "").trim().toLowerCase();
  return RUNTIME_MODES.includes(normalized) ? normalized : null;
}

export function parseDisambiguatorCommand(text, defaultMode = DEFAULT_MODE) {
  const fallback = normalizeMode(defaultMode) || DEFAULT_MODE;
  const normalizedText = String(text || "").trim().toLowerCase();

  if (!normalizedText) {
    return { type: "status", mode: fallback };
  }

  const [primary] = normalizedText.split(/\s+/);

  if (primary === "status") {
    return { type: "status", mode: fallback };
  }

  const mode = normalizeMode(primary);
  return mode ? { type: "set-mode", mode } : { type: "invalid", mode: primary };
}

export function getGlobalStatePath() {
  return path.join(
    process.env.XDG_CONFIG_HOME || path.join(os.homedir(), ".config"),
    "disambiguator",
    "mode"
  );
}

export function getWorkspaceStatePath(cwd = process.cwd()) {
  return path.join(cwd, ".disambiguator-mode");
}

export function readPersistedMode(cwd = process.cwd()) {
  // Check workspace state first
  try {
    const wsPath = getWorkspaceStatePath(cwd);
    if (fs.existsSync(wsPath)) {
      const mode = fs.readFileSync(wsPath, "utf-8").trim().toLowerCase();
      if (RUNTIME_MODES.includes(mode)) return mode;
    }
  } catch (_) {}

  // Check global state
  try {
    const globalPath = getGlobalStatePath();
    if (fs.existsSync(globalPath)) {
      const mode = fs.readFileSync(globalPath, "utf-8").trim().toLowerCase();
      if (RUNTIME_MODES.includes(mode)) return mode;
    }
  } catch (_) {}

  return DEFAULT_MODE;
}

export function writePersistedMode(mode, cwd = process.cwd()) {
  const normalized = normalizeMode(mode);
  if (!normalized) return false;

  // Persist to workspace
  try {
    const wsPath = getWorkspaceStatePath(cwd);
    fs.writeFileSync(wsPath, normalized, "utf-8");
  } catch (_) {}

  // Always persist to global config
  try {
    const globalPath = getGlobalStatePath();
    fs.mkdirSync(path.dirname(globalPath), { recursive: true });
    fs.writeFileSync(globalPath, normalized, "utf-8");
  } catch (_) {}

  return true;
}

export function resolveSessionMode(entries, fallbackMode = DEFAULT_MODE) {
  const fallback = normalizeMode(fallbackMode) || DEFAULT_MODE;
  if (!Array.isArray(entries)) return fallback;

  for (let i = entries.length - 1; i >= 0; i -= 1) {
    const entry = entries[i];
    if (entry?.type !== "custom" || entry?.customType !== "disambiguator-mode") continue;

    const mode = normalizeMode(entry?.data?.mode);
    if (mode) return mode;
  }

  return fallback;
}

export default function disambiguatorExtension(pi) {
  let currentMode = DEFAULT_MODE;
  let isActive = false;
  let lastCtx = null;

  function syncStatus(ctx) {
    if (ctx) lastCtx = ctx;
    const c = ctx || lastCtx;
    if (!c?.ui?.setStatus) return;

    let theme;
    try {
      theme = c.ui.theme;
      if (!theme?.fg) return;
    } catch {
      return;
    }

    if (currentMode === "off") {
      c.ui.setStatus("disambiguator", "");
      return;
    }

    const indicator = isActive ? theme.fg("accent", "●") : theme.fg("dim", "○");
    const modeLabel = currentMode.charAt(0).toUpperCase() + currentMode.slice(1).toLowerCase();
    c.ui.setStatus(
      "disambiguator",
      indicator + " " + theme.fg("muted", "disambiguator: ") + theme.fg("text", modeLabel)
    );
  }

  const setMode = (mode, ctx) => {
    const normalized = normalizeMode(mode);
    if (!normalized) return;

    currentMode = normalized;
    pi.appendEntry("disambiguator-mode", { mode: normalized });
    writePersistedMode(normalized, ctx?.cwd || process.cwd());
    syncStatus(ctx);

    const message = normalized === "off"
      ? "Disambiguator mode disabled (off)."
      : `Disambiguator mode updated: ${normalized}.`;
    ctx?.ui?.notify?.(message, "info");
  };

  pi.registerCommand("disambiguator", {
    description: DISAMBIGUATOR_COMMAND_DESCRIPTION,
    getArgumentCompletions: (argumentPrefix) => {
      const options = [
        {
          value: "strict",
          label: "strict",
          description: MODE_DESCRIPTIONS.strict,
        },
        {
          value: "soft",
          label: "soft",
          description: MODE_DESCRIPTIONS.soft,
        },
        {
          value: "status",
          label: "status",
          description: MODE_DESCRIPTIONS.status,
        },
        {
          value: "off",
          label: "off",
          description: MODE_DESCRIPTIONS.off,
        },
      ];

      const prefix = String(argumentPrefix || "").trim().toLowerCase();
      if (!prefix) return options;
      return options.filter((item) => item.value.toLowerCase().startsWith(prefix));
    },
    handler: async (args, ctx) => {
      const parsed = parseDisambiguatorCommand(args, currentMode);

      if (parsed.type === "status") {
        ctx?.ui?.notify?.(`Disambiguator current mode: ${currentMode} (default: ${DEFAULT_MODE})`, "info");
        return;
      }

      if (parsed.type === "set-mode") {
        setMode(parsed.mode, ctx);
        return;
      }

      ctx?.ui?.notify?.(`Unknown mode '${parsed.mode}'. Supported modes: strict, soft, off, status`, "warning");
    },
  });

  pi.registerCommand("disambiguator-strict", {
    description: "Switch Disambiguator operational mode to strict",
    handler: async (_args, ctx) => {
      setMode("strict", ctx);
    },
  });

  pi.registerCommand("disambiguator-soft", {
    description: "Switch Disambiguator operational mode to soft",
    handler: async (_args, ctx) => {
      setMode("soft", ctx);
    },
  });

  pi.registerCommand("disambiguator-off", {
    description: "Switch Disambiguator operational mode to off (disabled)",
    handler: async (_args, ctx) => {
      setMode("off", ctx);
    },
  });

  pi.registerCommand("disambiguator-status", {
    description: "Show current Disambiguator operational mode",
    handler: async (_args, ctx) => {
      ctx?.ui?.notify?.(`Disambiguator current mode: ${currentMode} (default: ${DEFAULT_MODE})`, "info");
    },
  });

  pi.on("input", async (event, ctx) => {
    if (event?.source === "extension") return { action: "continue" };

    const text = String(event?.text || "").trim();

    if (text === "/skill:disambiguator-soft" || text.startsWith("/skill:disambiguator-soft ")) {
      setMode("soft", ctx);
      return { action: "handled" };
    }

    if (text === "/skill:disambiguator-strict" || text.startsWith("/skill:disambiguator-strict ")) {
      setMode("strict", ctx);
      return { action: "handled" };
    }

    if (text === "/skill:disambiguator-off" || text.startsWith("/skill:disambiguator-off ")) {
      setMode("off", ctx);
      return { action: "handled" };
    }

    if (
      text === "/skill:disambiguator-status" ||
      text.startsWith("/skill:disambiguator-status ") ||
      text === "/skill:disambiguator" ||
      text.startsWith("/skill:disambiguator ")
    ) {
      ctx?.ui?.notify?.(`Disambiguator current mode: ${currentMode} (default: ${DEFAULT_MODE})`, "info");
      return { action: "handled" };
    }

    return { action: "continue" };
  });

  pi.on("session_start", async (_event, ctx) => {
    const entries = ctx?.sessionManager?.getBranch?.() || ctx?.sessionManager?.getEntries?.() || [];
    const cwd = ctx?.cwd || process.cwd();
    const fallback = readPersistedMode(cwd);
    currentMode = resolveSessionMode(entries, fallback);
    syncStatus(ctx);
  });

  pi.on("agent_start", async (_event, ctx) => {
    isActive = true;
    syncStatus(ctx);
  });

  pi.on("agent_end", async (_event, ctx) => {
    isActive = false;
    syncStatus(ctx);
  });

  pi.on("before_agent_start", async (event) => {
    if (!currentMode || currentMode === "off") return;

    const base = event?.systemPrompt || "";
    if (base.includes("DISAMBIGUATOR — SYSTEM PROMPT")) {
      const updatedPrompt = base.replace(/# MODE:\s*(strict|soft|off)/, `# MODE: ${currentMode}`);
      return { systemPrompt: updatedPrompt };
    }

    const instructions = getDisambiguatorInstructions(currentMode);
    return { systemPrompt: base ? `${base}\n\n${instructions}` : instructions };
  });
}
