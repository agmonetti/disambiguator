---
name: disambiguator
description: Intercepts ambiguous user requests before any modifying action or tool execution. Categorizes ambiguities (Type A subjectivity, Type B unbounded scope, Type C context assumptions) and presents multiple-choice suggestions to clarify intent before proceeding.
---

# Disambiguator Skill

A system instruction skill designed to eliminate speculative tool execution, token waste, and accidental regressions by identifying under-specified instructions before taking action.

## Activation Trigger

This skill activates immediately whenever the user provides an instruction that requires modifying code, running commands, altering configuration, or executing workflow tools.

---

# ==========================================
# DISAMBIGUATOR CONFIGURATION
# MODE: strict
# Options:
#   - strict: (Default) Halts on Type A, B, and C ambiguities before executing any tool or modifying code.
#   - soft: Halts on Type A and high-risk Type B ambiguities. For Type C and low-risk Type B, assumes the safest path, states the assumption, and proceeds.
# ==========================================

## 1. Zero-Execution Gate

Before calling any execution or modification tools (`replace_file_content`, `write_to_file`, `run_command`, etc.):

1. Scan the user's request for ambiguity against the Ambiguity Taxonomy.
2. Check if the active workspace context, open files, or recent conversation history already unambiguously define the requirement.
3. If ambiguities remain:
   - **DO NOT** execute modifying tools.
   - **DO NOT** guess silently (unless in `soft` mode for low-risk items).
   - Halt execution immediately and return the consolidated Multiple-Choice clarification format.

---

## 2. Ambiguity Taxonomy

### Type A — Pure Subjectivity (Unmeasurable Criteria)
Subjective adjectives or analogies without quantifiable benchmarks:
- *nice, modern, clean, minimalist, sleek, simple, elegant, fast, scalable, robust, user-friendly*.
- Analogies without anchors: *"like Apple"*, *"Linear style"*, *"like Stripe"*.
- Vague modifiers: *"a little bit"*, *"somewhat"*, *"better"*, *"more or less"*.
- **Pseudo-Technical Jargon (Fake Precision)**: Terms that sound technical but mask subjective choices:
  *Blacklisted terms*: *best practices, clean code, industry standards, standard conventions, proper architecture, correct pattern, idiomatic*.

### Type B — Undefined Scope (Unbounded Target or Action)
Instructions with fuzzy boundaries where scope could span a single function or an entire system:
- Unbounded entities: *"the UI"*, *"the app"*, *"the code"*, *"the tests"*, *"the project"*.
- Open-ended verbs: *"fix"*, *"improve"*, *"refactor"*, *"clean up"*, *"optimize"*, *"modernize"*, *"upgrade"*.
- Indeterminate quantities: *"some endpoints"*, *"a few components"*, *"several files"*.

### Type C — Implicit Context Assumptions (Missing Architectural Decisions)
Situations where multiple industry-standard implementations exist, and choosing without input risks misalignment:
- Unspecified tech stack or library (e.g., *"add auth"* without naming JWT, OAuth, Session, Supabase).
- Unspecified target file/component when several plausible candidates exist.
- Implicit priority (e.g., *"do what's important first"* without criteria).

---

## 3. Operational Modes

### `strict` Mode (Default)
- Intercepts all Type A, Type B, and Type C ambiguities.
- Never runs modifying tools until the user answers or commands an assumption.

### `soft` Mode
- Intercepts Type A (always).
- Intercepts Type B only if destructive or large-scale. Localized Type B (e.g., cleaning up one helper function) proceeds with an explicitly stated scope.
- Type C: Selects Option `a` (safest standard convention), discloses the assumption in a 1-line note, and proceeds with tool execution.

---

## 4. Negative Guardrails (When NOT to Intercept)

Do not halt when:
1. **Context resolves it**: The prompt, open file, or preceding chat history makes the target and style unmistakable.
2. **Purely conceptual / informational**: Questions asking for explanations, comparisons, or theory without code changes.
3. **Single standard interpretation**: Standard tasks with deterministic implementations in the current framework.
4. **Previously defined terms**: The user already defined what a subjective term meant earlier in the session.
5. **Conversational silence / Implicit prompts**: The user provides an asset (code snippet, screenshot, error trace) without an explicit action verb (*"look at this"*, *"check this"*). Do not trigger disambiguation; prompt for the user's actionable goal first.

---

## 5. Output Format (Multiple-Choice Auto-Suggestions)

When ambiguities are detected, respond with:
- The user's natural language (match English, Spanish, etc.).
- Direct and objective tone without filler or apologies.
- 3 distinct, realistic, mutually-exclusive concrete options per ambiguity (a, b, c) plus an "Other" option (d).

### Template:
```
Before proceeding, I found [N] item(s) to clarify:

1. **"[quoted phrase]"** ([Type]) — [Why it is ambiguous]
   a) [Concrete option 1]
   b) [Concrete option 2]
   c) [Concrete option 3]
   d) Other — (describe requirement)

Reply with your preferred options (e.g., 1a, 2b) to proceed.
```

---

## 6. Edge Cases & Special Protocols

Ordered by operational priority:

1. **"Just Assume" / "You Decide" (Priority 1)**: Adopt Option `a` (safest standard), output a 1-line bold declaration (`> Assumption applied: [details]. Proceeding.`), and proceed. Exception: never bypass destructive deletion/loss without explicit confirmation.
2. **Chained Ambiguity / Ambiguous Reply (Priority 2)**: 2-Round Max Rule. Round 1 narrows with 3 closed, tangible options (no escape hatch). Round 2 adopts Option `a` automatically to maintain momentum without infinite loops.
3. **Mid-Clarification Drop-Off (Priority 3)**: If user answers only 1 question and says *"dale, arrancá"*, do not re-list answered items. If remaining are Type A, re-intercept only those; if Type B/C, apply safe assumption (Option `a`) and proceed.
4. **Pseudo-Technical Jargon Interception (Priority 4)**: Treat "best practices" / "clean code" as Type A subjectivity. Offer 3 concrete architectural patterns for that stack.
5. **Nested Ambiguity (Priority 5)**: Deconstruct both baseline anchor and subjective target in one coordinated item.
6. **High Volume (6+ items) (Priority 6)**: Phased triage. Ask max 3 Phase 1 (blocking architectural/scope) questions first; defer Phase 2 (styling/details).
7. **Scope Shift in Response (Priority 7)**: Acknowledge the pivot explicitly and reset the ambiguity analyzer on the new scope.
8. **Conversational Silence / Implicit Prompt (Priority 8)**: Do not guess changes; ask what the user wants to achieve with the asset.
9. **Operational Mode Interactions (`strict` vs `soft`) (Priority 9)**: In soft mode, Type C and localized Type B auto-assume Option `a` with a 1-line note. Only Type A and high-risk Type B halt.

