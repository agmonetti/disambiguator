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

## Testing & Validation

A battery of 20 categorized test cases is provided in [`tests/test-cases.md`](./tests/test-cases.md):
- **5 Must-Stop cases** (verifies zero false negatives on ambiguous requests)
- **5 Must-NOT-Stop cases** (verifies zero false positives on precise and conceptual requests)
- **5 Grey Zone cases** (inspects strict vs. soft mode behavior)
- **5 Mixed cases** (verifies partial execution and isolated clarification)

To validate your integration, run the prompts in sequence and mark passes in the markdown matrix.

---

## License

MIT License. Free for personal and commercial use.
