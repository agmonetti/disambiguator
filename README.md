<p align="center">
  <img src="https://raw.githubusercontent.com/agmonetti/disambiguator/main/assets/banner.png" alt="Disambiguator banner" width="600">
</p>

<h1 align="center">Disambiguator</h1>

<p align="center">
A zero-dependency, pure instruction system prompt that intercepts ambiguous user instructions <strong>before any action is taken</strong>, surfaces assumptions as actionable multiple-choice options, and prevents wasted tokens and unintended code changes.
</p>

---

## Why Disambiguator?

AI coding assistants frequently rush into execution when handed vague instructions like *"make the UI look nice"* or *"refactor the backend"*. This leads to:
- Wasted tokens rewriting files you didn't want touched
- Hallucinated styling and unaligned architectural patterns
- Silent drift and destructive unintended edits

**Disambiguator acts as a zero-execution gatekeeper**: it halts the model before any tool execution, groups ambiguities by category, and generates realistic **multiple-choice suggestions (a/b/c/d)** so you can answer with just a letter instead of writing essays.

---

## Operating Modes

| Mode | Type A (Subjectivity) | Type B (Scope) | Type C (Context Assumptions) |
|---|---|---|---|
| **`strict` (Default)** | Always halts | Always halts | Always halts |
| **`soft`** | Always halts | Halts only on high-risk/destructive actions | Assumes safest standard, notes assumption, and proceeds |

### Switching Modes at Runtime
You can switch modes on the fly in any agent conversation, terminal harness, or IDE without editing files:
- Run `/disambiguator soft` to switch to soft mode.
- Run `/disambiguator strict` to switch back to strict mode.
- Run `/disambiguator off` to temporarily disable Disambiguator.
- Run `/disambiguator status` to check the active mode.

In IDEs and skill-based agents (Cursor, Windsurf, Copilot, Antigravity, OpenCode, OpenChamber, etc.), you can also pick dedicated skills directly from autocomplete:
- `/disambiguator-strict`: Instantly sets strict mode.
- `/disambiguator-soft`: Instantly sets soft mode.
- `/disambiguator-off`: Instantly disables gatekeeper.
- `/disambiguator-status`: Displays the current active mode.

To change the permanent repository default, configure the top of [`system-prompt.md`](./system-prompt.md) and run `npm run sync`:
```markdown
# CONFIGURATION
# MODE: strict   <--- Change to "soft" to reduce interruptions
```

---

## Install & Integration Tiers

Disambiguator operates across three integration tiers depending on your agent harness's architecture:

### Tier 1: Native Plugin & Lifecycle Hooks (Zero-Token Runtime Switching)

#### Antigravity CLI (`agy`) & Antigravity IDE
```bash
agy plugin install https://github.com/agmonetti/disambiguator
```
*(On legacy Gemini CLI: `gemini extensions install https://github.com/agmonetti/disambiguator`).*

- **Zero-Token Runtime Mode Switcher**: Toggle operational modes instantly in 0 ms without burning conversational tokens:
  ```bash
  npx @agmonetti/disambiguator strict   # Enforce strict mode across ambiguities
  npx @agmonetti/disambiguator soft     # Set soft mode (assume safest for Type C)
  npx @agmonetti/disambiguator off      # Temporarily disable Disambiguator
  npx @agmonetti/disambiguator status   # View active mode
  ```
- **Antigravity Lifecycle Hook (`hooks.json`)**: Listens on `PreInvocation`, tracks slash commands (`/disambiguator strict|soft|off`), persists active mode, and injects ephemeral context notes.
- **Native Workspace Rules (`.agents/rules/disambiguator.md`)**: Automatically loaded by Antigravity CLI and IDE with zero setup in cloned repositories.
- **Marketplace Distribution**: Manifested in `.agents/plugins/marketplace.json` for seamless Antigravity plugin marketplace discovery.

#### Pi Agent Harness
```bash
pi install git:github.com/agmonetti/disambiguator
```
*(Or if running locally: `pi -e ./pi-extension/index.js`).*

- **First-Class Slash Command**: Direct `/disambiguator [strict|soft|off|status]` command with argument autocomplete in Pi's terminal dropdown.
- **Zero-Token Runtime Toggles**: Switching modes executes locally in 0 ms without sending conversational prompts or burning LLM tokens.
- **Dual-Tier State Persistence**: Persists mode switches across Pi session journal and user configuration without polluting repository working trees.
- **Terminal Status Bar**: Displays the live mode (`● disambiguator: Strict` / `Soft`) in the terminal footer.
- **Dynamic Prompt Hook**: Injects or updates active mode directly on each turn via Pi's `before_agent_start` event.

#### OpenCode
Add to `opencode.json`:
```json
{ "plugin": ["@agmonetti/disambiguator"] }
```
Or run directly from a local repository checkout:
```json
{ "plugin": ["./.opencode/plugins/disambiguator.mjs"] }
```
- **Transform Hook**: Injects Disambiguator into every chat turn with defensive array/string handling and idempotency to prevent duplicate prompts.
- **Skills Catalog**: Automatically registers the full skills catalog (`disambiguator`, `disambiguator-strict`, `disambiguator-soft`).
- **Slash Commands**: Exposes `/disambiguator [strict|soft|status|off]` and `/disambiguator-help`.
- **Isolated Persistence**: Persists mode changes across sessions in `~/.config/opencode/.disambiguator-active`.

---

### Tier 2: Universal Rules & IDE Context (Always-On Workspace Gatekeeper)

#### OpenChamber & VS Code
OpenChamber and VS Code environments automatically discover and load `AGENTS.md` from your repository root with zero setup required. Drop `AGENTS.md` into your project root or clone this repository to activate Disambiguator immediately.

#### Dedicated Editor Rules (Copy & Paste)
For editor environments with dedicated instruction directories, copy the matching rule file from this repo:

| Editor / Environment | Target Path in Your Project | Global Path |
|---|---|---|
| **OpenChamber** | `AGENTS.md` | — |
| **Cursor** | `.cursor/rules/disambiguator.mdc` | — |
| **Codeium Windsurf** | `.windsurf/rules/disambiguator.md` | — |
| **Cline / Roo-Code** | `.clinerules` | — |
| **VS Code Copilot Chat** | `.github/copilot-instructions.md` | `~/.copilot/copilot-instructions.md` |
| **Kiro** | `.kiro/steering/disambiguator.md` | `~/.kiro/steering/disambiguator.md` |
| **Antigravity Workspace Rule** | `.agents/rules/disambiguator.md` | `~/.gemini/config/` |

#### Zero-Setup Universal Context (`AGENTS.md`)
The following agents automatically discover and load `AGENTS.md` from your repository root:
- **OpenChamber, Amp (Sourcegraph), Jules (Google), JetBrains Junie, VS Code with Codex extension, Zed, Qoder**.

---

### Tier 3: Assisted Configuration & Skills Catalog

#### Claude Code
Install via plugin marketplace:
```
/plugin marketplace add agmonetti/disambiguator
/plugin install disambiguator@disambiguator
```
*(You have to send two separate prompts for the install to work)*

- **Slash Commands & Skills**: Registers `/disambiguator [strict|soft|status|off]` and the full skills catalog.
- **Continuous Turn-by-Turn Protection**: Claude Code plugins register on-demand commands. To enforce Disambiguator as an always-on continuous gatekeeper across all prompts in your workspace, add `AGENTS.md` or append Disambiguator instructions to `CLAUDE.md` (or `~/.claude/CLAUDE.md`).

#### Aider
Configure Aider to automatically load Disambiguator rules on every session:
- In `.aider.conf.yml`:
  ```yaml
  read: [AGENTS.md]
  ```
- Or pass via CLI:
  ```bash
  aider --read AGENTS.md
  ```

#### Universal Agent Skills (`skills.sh` / `npx skills`)
Works across 70+ AI coding agents automatically:
```bash
npx skills add agmonetti/disambiguator
```
To install globally across all workspaces on your machine:
```bash
npx skills add agmonetti/disambiguator -g
```

#### Other Supported Environments
- **Codex CLI**: `codex plugin marketplace add agmonetti/disambiguator && codex plugin add disambiguator@disambiguator`
- **GitHub Copilot CLI**: `/plugin marketplace add agmonetti/disambiguator && /plugin install disambiguator@disambiguator`
- **Devin CLI**: `devin plugins install agmonetti/disambiguator`
- **Hermes Agent**: `hermes plugins install agmonetti/disambiguator --enable`
- **Swival**: `swival skills add --global https://github.com/agmonetti/disambiguator && swival skills add disambiguator`
- **OpenClaw**: `clawhub install disambiguator`

---

### Generic Web LLMs (ChatGPT, Claude Web, LibreChat, OpenWebUI)
1. Open [`system-prompt.md`](./system-prompt.md).
2. Copy the full content.
3. Paste into the **Custom Instructions**, **System Prompt**, or **Model Instructions** field of your preferred interface.

---

## Uninstall

| Host | Command |
|---|---|
| **Claude Code** | `/plugin remove disambiguator` |
| **Codex** | `codex plugin remove disambiguator` |
| **Devin CLI** | `devin plugins remove disambiguator` |
| **Pi agent** | `pi uninstall disambiguator` |
| **Antigravity CLI** | `agy plugin remove disambiguator` |
| **Agent Skills** | `npx skills remove disambiguator` |
| **OpenClaw** | `clawhub uninstall disambiguator` |
| **Cursor / Windsurf / Cline / OpenChamber / etc.** | Delete the copied rule file |

---

### Generic Web LLMs (ChatGPT, Claude Web, LibreChat, OpenWebUI)
1. Open [`system-prompt.md`](./system-prompt.md).
2. Copy the full content.
3. Paste into the **Custom Instructions**, **System Prompt**, or **Model Instructions** field of your preferred interface.

---

## Uninstall

| Host | Command |
|---|---|
| **Claude Code** | `/plugin remove disambiguator` |
| **Codex** | `codex plugin remove disambiguator` |
| **Devin CLI** | `devin plugins remove disambiguator` |
| **Pi agent** | `pi uninstall disambiguator` |
| **Antigravity CLI** | `agy plugin remove disambiguator` |
| **Agent Skills** | `npx skills remove disambiguator` |
| **OpenClaw** | `clawhub uninstall disambiguator` |
| **Cursor / Windsurf / Cline / Qoder / etc.** | Delete the copied rule file |

---


## How It Works in Practice

### Ambiguity Taxonomy

- **Type A — Pure Subjectivity**: Unmeasurable adjectives (*"clean"*, *"modern"*, *"elegant"*, *"faster"*).
- **Type B — Undefined Scope**: Unbounded targets or open-ended verbs (*"fix the UI"*, *"refactor the code"*, *"clean up tests"*).
- **Type C — Missing Context**: Unspecified dependencies, stacks, or target files when multiple valid choices exist.

### Example Interaction

**User:**
> *"Update the landing page UI so it looks clean and modern."*

**Disambiguator Response:**
```markdown
Before proceeding, I found 3 items to clarify:

1. **"the landing page UI"** (Type B — Undefined Scope) — The page contains multiple independent sections.
   a) The entire page (Hero, Features, Pricing, and Footer)
   b) Header and Hero section only
   c) Content and conversion sections (Features and CTA)
   d) Other — (specify target sections)

2. **"clean"** (Type A — Pure Subjectivity) — No measurable aesthetic standard was provided.
   a) Minimalist layout with generous whitespace and high-contrast typography
   b) Subtle borders, soft background tones, and reduced element density
   c) Structured corporate layout with clear grid dividers
   d) Other — (describe your preferred style)

3. **"modern"** (Type A — Unspecified Reference) — No design reference was specified.
   a) Linear / Vercel style (subtle dark theme, fine borders, monochrome accents)
   b) Glassmorphism with soft gradients and rounded corners
   c) Geometric flat design with crisp edges
   d) Other — (share a reference URL or design guideline)

Reply with your selected options (e.g., 1a, 2b, 3a) or describe your preferences to proceed.
```

---


## Edge Case Protocols

Disambiguator includes a prioritized 10-point robustness protocol to prevent deadlocks and maintain user trust:

1. **"Just assume" override**: Maps to the safest, most conservative option (option `a`), states it explicitly in one line, and proceeds immediately without further questions.
2. **Chained ambiguities (2-round limit)**: Imposes a hard limit of two clarification rounds. Round 1 presents primary ambiguities; Round 2 resolves any direct followup ambiguity. If ambiguity remains after Round 2, the safest conservative choice is applied with an explicit declaration.
3. **Mid-clarification cancellation & partial answers**: If a user answers only one question and requests immediate action, unaddressed Type B/C items apply safe fallbacks with a 1-line declaration, while unaddressed Type A (subjectivity) items halt again to request the missing criterion.
4. **Pseudo-technical buzzword blacklist**: Generic terms like *"clean code"*, *"best practices"*, *"enterprise-grade"*, and *"scalable"* are treated as Type A subjectivity unless grounded in concrete standards.
5. **Nested ambiguity deconstruction**: When an instruction relies on a relative comparison anchored to an undefined baseline (*"more professional than the current version"*), it separates the baseline from the target criteria into a single coordinated item.
6. **Overload triage (Phase 1 vs. Phase 2)**: When 4 or more ambiguities arise, core architectural choices are grouped into Phase 1 (max 3 questions), deferring visual styling and micro-details to Phase 2.
7. **Scope shift recognition**: When a user's clarifying response expands scope (e.g., *"actually redesign the entire auth flow"*), it is recognized as a new request rather than an answer, resetting analysis without loops.
8. **Conversational silence & implicit prompts**: When an asset (snippet, stack trace, image) is shared without an explicit action verb, Disambiguator prompts for the user's intent first rather than hallucinating options.
9. **Mixed prompts / partial stops (deterministic core + ambiguous expansion)**: When an instruction pairs an unambiguous command with an ambiguous goal, Disambiguator decouples code output, acknowledges the unambiguous segment as identified/staged, halts tool execution, and clarifies only the ambiguous remainder.
10. **Operational mode interactions (`strict`, `soft`, `off`)**: In `strict` mode, edge cases enforce halting on all ambiguity types; in `soft` mode, Type C and localized low-risk Type B adopt Option `a` automatically with a 1-line notice, reserving halts exclusively for Type A and high-risk destructive actions.

---

## Automated Test Runner & Benchmarks

Disambiguator provides both an **instant offline test suite** and a standardized **multi-provider LLM-as-a-judge** evaluation harness.

### 1. Instant Offline Test Suite (< 50ms)
Validates parser schema, YAML assertion integrity, and zero-drift harness parity across all 20 adapters using Python's standard library:

```bash
python3 -m unittest discover -v -s tests

# or execute both Python and Node test suites together:
npm test
```

### 2. Multi-Provider Automated LLM Runner
Evaluates 20 real-world benchmark cases through a target model and grades compliance using an LLM judge (`tests/runner.py`).

- **Zero Mandatory Dependencies**: Built entirely on Python standard library modules (`urllib`, `json`, `re`, `pathlib`, `unittest`).
- **Universal Provider Support**: Native REST drivers for Google Gemini, OpenAI, Anthropic Claude, and local OpenAI-compatible runners (Ollama, Groq, DeepSeek, vLLM).
- **Machine-Evaluable Assertions**: 20 test cases in [`tests/test-cases.md`](./tests/test-cases.md) specifying unambiguous evaluation schemas (`contains_question`, `min_questions`, `no_code_executed`, `ambiguity_types_flagged`, `proceeds_directly`, `aviso_emitido`, `partial_stop`).

#### Running the Test Suite Locally

Configure environment variables in a `.env` file or export them directly:

```bash
# Example 1: Run with Google Gemini (default)
GEMINI_API_KEY="your-api-key" python3 tests/runner.py

# Example 2: Run with local Ollama (zero API costs)
PROVIDER=ollama OPENAI_BASE_URL=http://localhost:11434/v1 TEST_MODEL=llama3.2 python3 tests/runner.py

# Example 3: Run with OpenAI
PROVIDER=openai OPENAI_API_KEY="sk-..." TEST_MODEL=gpt-4o-mini python3 tests/runner.py

# Example 4: Run with Anthropic Claude
PROVIDER=anthropic ANTHROPIC_API_KEY="sk-ant-..." python3 tests/runner.py
```

Results are dumped to `results.json` with per-assertion verdicts, judge reasoning, and summary metrics.

---

## Design Decisions & Limitations

- **Cognitive Gatekeeper vs. Tool Execution**: Disambiguator evaluates intent, gatekeeping rules, and ambiguity taxonomy. It does not contain language-specific execution tools. When hosted in an agentic IDE (Cursor, Claude Code, AGY CLI), modifying tools execute directly; in raw chat interfaces, actions are emitted as declarative diffs and execution plans.
- **Decoupled Code Output in Partial Stops**: In mixed prompts where the model pauses for an ambiguous segment while identifying a deterministic core, code generation in the same turn is not required. A declarative statement identifying the active part suffices, avoiding unintended half-executions.
- **Language Adaptation**: Prompts are matched dynamically. Spanish user prompts yield Spanish clarifying options; English prompts yield English options. No separate localized prompt files are required.

---

## Maintainers & Anti-Drift Architecture

Disambiguator maintains strict parity across all 20 harness adapters (`AGENTS.md`, `SKILL.md`, `.cursor/rules/`, `.windsurf/rules/`, `.clinerules`, `.github/copilot-instructions.md`, `.kiro/steering/disambiguator.md`, `skills/*`, `commands/*`, `.opencode/*`, etc.).

The single canonical source of truth is always [`system-prompt.md`](./system-prompt.md).

```bash
# Synchronize all adapters after editing system-prompt.md
python3 scripts/sync.py

# Verify parity in CI or locally (fails with code 1 if drift is detected)
python3 scripts/sync.py --check
```

Continuous integration runs `.github/workflows/sync-check.yml` on every pull request to enforce zero drift.

---

## License


MIT License. Free for personal and commercial use.

