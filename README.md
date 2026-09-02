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
<summary><b>Anthropic Claude Code (<code>CLAUDE.md</code>)</b></summary>

Add Disambiguator to your project-level or global Claude Code instructions.

**Option A — Project-level:**
Append the contents of `system-prompt.md` to `CLAUDE.md` in your repository root:
```bash
cat system-prompt.md >> CLAUDE.md
```

**Option B — Direct fetch via cURL:**
```bash
curl -sSL https://raw.githubusercontent.com/username/disambiguator/main/system-prompt.md >> CLAUDE.md
```

</details>

<details>
<summary><b>Cursor (<code>.cursorrules</code> / <code>.cursor/rules/</code>)</b></summary>

Cursor reads `.cursorrules` or modular rule files in `.cursor/rules/`.

**Option A — Legacy single file:**
Create or append to `.cursorrules` in your workspace root:
```bash
cat system-prompt.md >> .cursorrules
```

**Option B — Cursor Rules Directory (v0.40+):**
Copy `system-prompt.md` directly into `.cursor/rules/disambiguator.mdc`:
```bash
mkdir -p .cursor/rules
cp system-prompt.md .cursor/rules/disambiguator.mdc
```

</details>

<details>
<summary><b>VS Code + GitHub Copilot (<code>.github/copilot-instructions.md</code>)</b></summary>

GitHub Copilot Workspace and Copilot Chat automatically read instructions from `.github/copilot-instructions.md`.

```bash
mkdir -p .github
cat system-prompt.md >> .github/copilot-instructions.md
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
> *"Modificame la UI de la landing para que quede linda y moderna"*

**Disambiguator Response:**
```markdown
Antes de continuar, encontré 3 ambigüedades que necesito resolver:

1. **"la UI de la landing"** (Tipo B - Scope indefinido) — La página tiene múltiples secciones independientes.
   a) Toda la página completa (Hero, Features, Pricing, Footer)
   b) Solo la sección superior (Navbar y Hero)
   c) Secciones de contenido y llamados a la acción (Features, CTA)
   d) Otro — (especificar qué secciones)

2. **"linda"** (Tipo A - Subjetividad) — No hay un criterio visual definido.
   a) Paleta más sobria, mayor contraste y espaciado generoso
   b) Tonos pasteles, bordes redondeados y micro-interacciones suaves
   c) Tipografía minimalista y diseño enfocado en legibilidad
   d) Otro — (describir tu preferencia)

3. **"moderna"** (Tipo A - Referencia no especificada) — No hay estilo de diseño de referencia.
   a) Estilo Linear / Vercel (dark mode sutil, bordes finos, acentos monocromáticos)
   b) Glassmorphism y gradientes suaves
   c) Flat design geométrico y limpio
   d) Otro — (compartir una referencia)

Respondé con las opciones elegidas (ej: 1a, 2b, 3a) o indicá tus preferencias para comenzar.
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

## License

MIT License. Free for personal and commercial use.

