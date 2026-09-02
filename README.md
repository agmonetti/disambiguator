# Disambiguator

> A zero-dependency, pure instruction system prompt that intercepts ambiguous user instructions **before any action is taken**, surfaces assumptions as actionable multiple-choice options, and prevents wasted tokens and unintended code changes.

---

## Why Disambiguator?

AI coding assistants frequently rush into execution when handed vague instructions like *"make the UI look nice"* or *"refactor the backend"*. This leads to:
- Wasted tokens rewriting files you didn't want touched
- Hallucinated styling and unaligned architectural patterns
- Silent drift and destructive unintended edits

**Disambiguator acts as a zero-execution gatekeeper**: it halts the model before any tool execution, groups ambiguities by category, and generates realistic **multiple-choice suggestions (a/b/c/d)** so you can answer with just a letter instead of writing essays.

---

## Operating Modes

Configure the mode directly at the top of [`system-prompt.md`](./system-prompt.md):

```markdown
# CONFIGURATION
# MODE: strict   <--- Change to "soft" to reduce interruptions
```

| Mode | Type A (Subjectivity) | Type B (Scope) | Type C (Context Assumptions) |
|---|---|---|---|
| **`strict` (Default)** | Always halts | Always halts | Always halts |
| **`soft`** | Always halts | Halts only on high-risk/destructive actions | Assumes safest standard, notes assumption, and proceeds |

---

## Installation & Setup

Choose your preferred tool below. Click to expand setup instructions:

<details>
<summary><b>Universal Agent Context (<code>AGENTS.md</code>)</b></summary>

Modern AI coding agents (GitHub Copilot, Codex, Cursor, Devin, OpenCode) automatically discover and load `AGENTS.md` at the repository root.

**Option A — Project-level:**
Copy or link `AGENTS.md` into your repository root:
```bash
cp AGENTS.md /path/to/your/project/AGENTS.md
```

**Option B — Direct fetch via cURL:**
```bash
curl -sSL https://raw.githubusercontent.com/username/disambiguator/main/AGENTS.md > AGENTS.md
```

</details>

<details>
<summary><b>Cursor (<code>.cursor/rules/</code> or <code>.cursorrules</code>)</b></summary>

Cursor reads modular rule files in `.cursor/rules/` (v0.40+) or `.cursorrules`.

**Option A — Modular Rule (Recommended):**
Copy the preconfigured rule file into your workspace:
```bash
mkdir -p .cursor/rules
cp .cursor/rules/disambiguator.mdc /path/to/your/project/.cursor/rules/
```

**Option B — Single-file rule:**
```bash
cat system-prompt.md >> .cursorrules
```

</details>

<details>
<summary><b>Codeium Windsurf (<code>.windsurf/rules/</code>)</b></summary>

Windsurf Cascade automatically picks up workspace rules from `.windsurf/rules/`:

```bash
mkdir -p .windsurf/rules
cp .windsurf/rules/disambiguator.md /path/to/your/project/.windsurf/rules/
```

</details>

<details>
<summary><b>Cline / Roo-Code (<code>.clinerules</code>)</b></summary>

Cline and Roo-Code read custom system instructions from `.clinerules` in the workspace root:

```bash
cp .clinerules /path/to/your/project/.clinerules
```

</details>

<details>
<summary><b>VS Code + GitHub Copilot (<code>.github/copilot-instructions.md</code>)</b></summary>

GitHub Copilot Workspace and Copilot Chat automatically read instructions from `.github/copilot-instructions.md`:

```bash
mkdir -p .github
cp .github/copilot-instructions.md /path/to/your/project/.github/copilot-instructions.md
```

</details>

<details>
<summary><b>Anthropic Claude Code (<code>CLAUDE.md</code> & Skills)</b></summary>

Add Disambiguator to your project-level or global Claude Code configuration.

**Option A — CLAUDE.md instruction:**
Append the contents of `system-prompt.md` to `CLAUDE.md` in your repository root:
```bash
cat system-prompt.md >> CLAUDE.md
```

**Option B — Standard Agent Skill:**
Copy the skill into your project or personal skills directory:
```bash
mkdir -p ~/.claude/skills/disambiguator
cp -r skills/disambiguator/* ~/.claude/skills/disambiguator/
```

</details>

<details>
<summary><b>Codex CLI (<code>system.md</code>)</b></summary>

For OpenAI Codex CLI or custom wrapper tools:

**Option A — Project-level:**
```bash
mkdir -p .codex
cp system-prompt.md .codex/system.md
```

**Option B — User global configuration:**
```bash
mkdir -p ~/.codex
cat system-prompt.md >> ~/.codex/system.md
```

</details>

<details>
<summary><b>Google Antigravity (AGY Skill)</b></summary>

Install as a reusable AGY skill across your agent sessions:

```bash
mkdir -p ~/.gemini/antigravity-cli/builtin/skills/disambiguator
cp SKILL.md ~/.gemini/antigravity-cli/builtin/skills/disambiguator/SKILL.md
```

Once installed, invoke with `/disambiguator` or allow it to automatically run on task startup.

</details>

<details>
<summary><b>Generic / Any LLM Interface (ChatGPT, Claude Web, LibreChat, OpenWebUI)</b></summary>

1. Open [`system-prompt.md`](./system-prompt.md).
2. Copy the full content.
3. Paste into the **Custom Instructions**, **System Prompt**, or **Model Instructions** field of your preferred interface.

</details>

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

Disambiguator includes a prioritized 9-point robustness protocol to prevent deadlocks and maintain user trust:

1. **"Just assume" override**: Maps to the safest, most conservative option (option `a`), states it explicitly in one line, and proceeds immediately without further questions.
2. **Chained ambiguities (2-round limit)**: Imposes a hard limit of two clarification rounds. Round 1 presents primary ambiguities; Round 2 resolves any direct followup ambiguity. If ambiguity remains after Round 2, the safest conservative choice is applied with an explicit declaration.
3. **Mid-clarification cancellation & partial answers**: If a user answers only one question and requests immediate action, unaddressed Type A/B items apply safe fallbacks while preserving the resolved item.
4. **Scope shift recognition**: When a user's clarifying response expands scope (e.g., *"actually redesign the entire auth flow"*), it is recognized as a new request rather than an answer, resetting analysis without loops.
5. **Pseudo-technical buzzword blacklist**: Generic terms like *"clean code"*, *"best practices"*, *"enterprise-grade"*, and *"scalable"* are treated as Type A subjectivity unless grounded in concrete standards.
6. **Overload triage (Phase 1 vs. Phase 2)**: When more than 3 ambiguities arise, core architectural choices are grouped into Phase 1, deferring cosmetic details to Phase 2.
7. **Conversational silence & implicit prompts**: When an asset (snippet, stack trace, image) is shared without an explicit action verb, Disambiguator prompts for the user's intent first rather than hallucinating options.
8. **Negative constraints**: File-specific edits with deterministic targets, theoretical explanations, and previously defined user idioms proceed immediately with zero interruptions.

---

## Automated Test Runner & Benchmarks

Disambiguator includes a standardized multi-provider automated test runner (`tests/runner.py`) using an **LLM-as-a-judge** evaluation harness.

### Key Architecture Features
- **Zero Mandatory Dependencies**: Built entirely on Python standard library modules (`urllib`, `json`, `re`, `pathlib`). Optional dependencies (`python-dotenv`, `google-genai`) are supported if installed.
- **Universal Provider Support**: Native REST drivers for Google Gemini, OpenAI, Anthropic Claude, and local OpenAI-compatible runners (Ollama, Groq, DeepSeek, vLLM).
- **Machine-Evaluable Assertions**: 20 test cases in [`tests/test-cases.md`](./tests/test-cases.md) specifying unambiguous evaluation schemas (`contains_question`, `min_questions`, `no_code_executed`, `ambiguity_types_flagged`, `proceeds_directly`, `aviso_emitido`, `partial_stop`).

### Running the Test Suite Locally

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

Disambiguator maintains strict parity across all 7 agent rule copies (`AGENTS.md`, `SKILL.md`, `.cursor/rules/`, `.windsurf/rules/`, `.clinerules`, `.github/copilot-instructions.md`, and `skills/disambiguator/SKILL.md`).

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

