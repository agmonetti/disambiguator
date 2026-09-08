# Disambiguator Test Battery & Automation Matrix

This document provides the standardized test suite for the Disambiguator prompt. It is dual-purpose:
1. **Manual Evaluation**: Human reviewers can execute test prompts and mark results in the summary table and individual check blocks.
2. **Automated Evaluation**: Each test case specifies machine-evaluable assertions formatted for programmatic evaluation via an LLM judge runner.

---

## Evaluation Summary Table (Manual Testing)

| # | Category | Prompt Under Test | Ambiguity Types | Expected Action | Status |
|---|----------|-------------------|-----------------|-----------------|--------|
| 01 | **Must Stop** | *"Make the landing page look prettier and cleaner."* | `[A, B]` | Halt; present design & section choices | `[ ] PASS / [ ] FAIL` |
| 02 | **Must Stop** | *"Optimize the database queries."* | `[B, C]` | Halt; identify target queries & metrics | `[ ] PASS / [ ] FAIL` |
| 03 | **Must Stop** | *"Add authentication to the project."* | `[C]` | Halt; offer auth strategies/providers | `[ ] PASS / [ ] FAIL` |
| 04 | **Must Stop** | *"Arreglá el código para que sea más profesional y rápido."* | `[A, B]` | Halt; define metric, files & standard in ES | `[ ] PASS / [ ] FAIL` |
| 05 | **Must Stop** | *"Refactor the components to follow best practices."* | `[A, B]` | Halt; flag jargon & present concrete patterns | `[ ] PASS / [ ] FAIL` |
| 06 | **Must NOT Stop** | *"In `src/components/Button.tsx`, change button background from `#000000` to `#0070f3`."* | `[]` | Execute change directly | `[ ] PASS / [ ] FAIL` |
| 07 | **Must NOT Stop** | *"What is the difference between `useEffect` and `useLayoutEffect` in React?"* | `[]` | Answer conceptual query immediately | `[ ] PASS / [ ] FAIL` |
| 08 | **Must NOT Stop** | *"Run `npm test` and report any failing suites."* | `[]` | Emit `npm test`; do not fabricate results | `[ ] PASS / [ ] FAIL` |
| 09 | **Must NOT Stop** | *"Add column `last_login_at` (TIMESTAMP WITH TIME ZONE NULL) to `users` in `migrations/003.sql`."* | `[]` | Edit target file directly | `[ ] PASS / [ ] FAIL` |
| 10 | **Must NOT Stop** | *"Explain why Docker multi-stage builds reduce final image footprint."* | `[]` | Answer conceptual query immediately | `[ ] PASS / [ ] FAIL` |
| 11 | **Grey Zone** | *"Clean up the unused imports in `src/utils/math.ts`."* | `[B]` | Strict: halt on Type B without code output | `[ ] PASS / [ ] FAIL` |
| 12 | **Grey Zone** | *"Format this markdown table according to standard GFM rules."* | `[]` | Proceed directly (deterministic format) | `[ ] PASS / [ ] FAIL` |
| 13 | **Grey Zone** | *"Add a tooltip to the checkout submit button."* | `[A, C]` | Strict: ask text/trigger. Soft: suggest default. | `[ ] PASS / [ ] FAIL` |
| 14 | **Grey Zone** | *"Refactor this 10-line helper to use early returns instead of nested if-else."* | `[]` | Proceed directly (single bounded idiom) | `[ ] PASS / [ ] FAIL` |
| 15 | **Grey Zone** | *"Make this API error message more user friendly."* | `[A, B]` | Halt; request current message or context | `[ ] PASS / [ ] FAIL` |
| 16 | **Mixed** | *"Export `calculateTotal` in `src/billing.ts` and make the module nicer."* | `[A, B]` | List export as pending; clarify "nicer" | `[ ] PASS / [ ] FAIL` |
| 17 | **Mixed** | *"Bump version in `package.json` to 1.2.0 and modernize the docs."* | `[A, B]` | List bump as pending; clarify doc scope | `[ ] PASS / [ ] FAIL` |
| 18 | **Mixed** | *"Create `POST /api/webhooks/stripe` with signature check, handle events properly."* | `[B, C]` | Partial stop: route clear; clarify event types | `[ ] PASS / [ ] FAIL` |
| 19 | **Mixed** | *"Agregá un test para `validateEmail()` y mejorá los otros tests."* | `[B]` | Partial stop in ES: test ready; clarify scope | `[ ] PASS / [ ] FAIL` |
| 20 | **Mixed** | *"Delete deprecated `v1/auth.go` and clean up related legacy logic."* | `[B]` | Partial stop: deletion clear; clarify callers | `[ ] PASS / [ ] FAIL` |
| 21 | **Mode Semantics** | *"Clean up the unused imports in `src/utils/math.ts`."* | `[B]` | Soft: emit correction with one assumption notice | `[ ] PASS / [ ] FAIL` |
| 22 | **Mode Semantics** | *"Clean up the unused imports in `src/utils/math.ts`."* | `[]` | Off: emit correction without interception | `[ ] PASS / [ ] FAIL` |

---

## Detailed Test Cases & Automation Assertions

### Category 1: Must Stop (Clear Ambiguity)

#### Test Case 01: Pure Subjectivity + Undefined Scope
- **Mode**: strict
- **Prompt**: `"Make the landing page look prettier and cleaner."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Halts immediately. Does not edit files. Presents multi-choice options for visual aesthetics (Type A) and target sections (Type B).
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 2
  no_code_executed: true
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 02: Undefined Scope + Missing Metrics
- **Mode**: strict
- **Prompt**: `"Optimize the database queries."`
- **Ambiguity Types**: `[B, C]`
- **Expected Behavior**: Halts execution. Identifies that target queries, optimization metrics (latency vs throughput), and approaches (indexing vs rewrite) are undefined.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["B", "C"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 03: Missing Architectural Context
- **Mode**: strict
- **Prompt**: `"Add authentication to the project."`
- **Ambiguity Types**: `[C]`
- **Expected Behavior**: Halts before installing libraries or scaffolding files. Presents multiple-choice authentication options (JWT, OAuth2, Session cookies, Supabase).
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["C"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 04: Spanish Idiom + Subjective Speed
- **Mode**: strict
- **Prompt**: `"Arreglá el código para que sea más profesional y rápido."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Responds in Spanish. Halts execution. Presents multiple-choice questions for scope ("el código"), quality ("más profesional"), and speed ("rápido").
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 2
  no_code_executed: true
  ambiguity_types_flagged: ["A"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false

```

#### Test Case 05: Unanchored Technical Jargon
- **Mode**: strict
- **Prompt**: `"Refactor the components to follow best practices."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Flags "best practices" as pseudo-technical subjectivity (Type A) and "the components" as unbounded scope (Type B). Offers concrete architectural patterns.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 2
  no_code_executed: true
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```

---

### Category 2: Must NOT Stop (Precise Request / Pure Theory)

#### Test Case 06: Deterministic Single-File Edit
- **Mode**: strict
- **Prompt**: `"In src/components/Button.tsx: export const Button = () => <button style={{ backgroundColor: '#000000' }}>Click</button>; Change the button background color from #000000 to #0070f3."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Executes the requested edit directly or outputs the exact code diff. Zero questions asked.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:

```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 07: Conceptual / Theoretical Query
- **Mode**: strict
- **Prompt**: `"What is the difference between useEffect and useLayoutEffect in React?"`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Answers directly with theoretical and practical explanation. Does not halt.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: true
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 08: Deterministic Command Execution
- **Mode**: strict
- **Prompt**: `"Run npm test and report any failing suites."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Immediately emits `npm test` as the command to run. Asks no clarifying questions and does not invent test results because the HTTP runner has no terminal.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes: environment_dependent: true, context: chat_no_tools
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```


#### Test Case 09: Unambiguous Schema Migration
- **Mode**: strict
- **Prompt**: `"Add a column last_login_at (TIMESTAMP WITH TIME ZONE NULL) to users in migrations/003.sql."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Directly edits `migrations/003.sql` with the specified SQL statement.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 10: Architectural Explanation
- **Mode**: strict
- **Prompt**: `"Explain why Docker multi-stage builds reduce final image footprint."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Explains multi-stage caching and image size reduction immediately. No halts.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: true
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```

---

### Category 3: Grey Zone (Contextual & Mild Ambiguity)

#### Test Case 11: Localized Cleanup
- **Mode**: strict
- **Prompt**: `"In src/utils/math.ts: import { add, unusedHelper } from './ops'; export const fn = () => add(1, 2); Clean up the unused imports."`
- **Ambiguity Types**: `[B]`
- **Expected Behavior**: In `strict` mode, halts on the localized Type B scope, asks whether to remove `unusedHelper`, and emits no corrected import or diff.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```


#### Test Case 12: Standard Formatting Task
- **Mode**: strict
- **Prompt**: `"Format this markdown table according to standard GFM rules: | Name | Role | Status | | --- | --- | --- | | Alice | Dev | Active | | Bob | Designer | Pending |"`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Proceeds directly. GFM table alignment is deterministic and standardized.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:

```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 13: UI Enhancement with Missing Microcopy
- **Mode**: strict
- **Prompt**: `"Add a tooltip to the checkout submit button."`
- **Ambiguity Types**: `[A, C]`
- **Expected Behavior**: Halts to clarify tooltip text/behavior, or provides 3 concrete text proposals.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["C"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```

#### Test Case 14: Micro-Refactoring
- **Mode**: strict
- **Prompt**: `"Refactor this 10-line helper to use early returns instead of nested if-else: function check(u) { if (u) { if (u.active) return true; } return false; }"`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Bounded scope and single idiom. Proceeds directly with code implementation.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```


#### Test Case 15: Copywriting Adjustment
- **Mode**: strict
- **Prompt**: `"Make this API error message more user friendly."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Halts execution. Identifies missing original error message/context (Type B) and subjectivity of 'user friendly' (Type A). Asks for current message or context before offering variations.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: false
```


---

### Category 4: Mixed Prompts (Precise Core + Ambiguous Tail)

#### Test Case 16: Isolated Change + Vague Module Goal
- **Mode**: strict
- **Prompt**: `"Export calculateTotal in src/billing.ts and make the module nicer."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Partial stop. Identifies and lists exporting `calculateTotal` as pending without emitting code or a diff; pauses "make nicer" and asks for criteria.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```

#### Test Case 17: Version Bump + Unbounded Documentation
- **Mode**: strict
- **Prompt**: `"Bump version in package.json to 1.2.0 and modernize the docs."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Partial stop. Identifies and lists the `package.json` bump as pending without emitting code or a diff; halts on "modernize docs" to clarify scope.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes: The deterministic portion is listed only; code output and execution remain deferred until the ambiguity is resolved.
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```


#### Test Case 18: Concrete Route + Implicit Handlers
- **Mode**: strict
- **Prompt**: `"Create POST /api/webhooks/stripe with signature check, handle events properly."`
- **Ambiguity Types**: `[B, C]`
- **Expected Behavior**: Partial stop. Route and signature verification are clear; halts to confirm specific Stripe event types.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["B", "C"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```

#### Test Case 19: Targeted Test + Broad Testing Goal
- **Mode**: strict
- **Prompt**: `"Agregá un test para validateEmail() y mejorá los otros tests."`
- **Ambiguity Types**: `[B]`
- **Expected Behavior**: Partial stop in Spanish. Identifies `validateEmail()` test as ready; pauses to clarify "mejorá los otros".
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```


#### Test Case 20: Safe Deletion + Broad Ripple Effect
- **Mode**: strict
- **Prompt**: `"Delete deprecated v1/auth.go and clean up related legacy logic."`
- **Ambiguity Types**: `[B]`
- **Expected Behavior**: Partial stop. Deletion of `v1/auth.go` is unambiguous; warns that removing callers is broad and confirms strategy.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```

---

### Category 5: Mode Semantics (Same Prompt Across Modes)

#### Test Case 21: Localized Cleanup in Soft Mode
- **Mode**: soft
- **Prompt**: `"In src/utils/math.ts: import { add, unusedHelper } from './ops'; export const fn = () => add(1, 2); Clean up the unused imports."`
- **Ambiguity Types**: `[B]`
- **Expected Behavior**: Emits `import { add } from './ops';`, exactly one assumption notice line selecting the localized unused-import cleanup, and no question.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: true
  partial_stop: false
```

#### Test Case 22: Localized Cleanup with Gatekeeper Off
- **Mode**: off
- **Prompt**: `"In src/utils/math.ts: import { add, unusedHelper } from './ops'; export const fn = () => add(1, 2); Clean up the unused imports."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Emits `import { add } from './ops';` directly with no assumption notice, ambiguity classification, or question.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: false
  min_questions: 0
  no_code_executed: false
  ambiguity_types_flagged: []
  proceeds_directly: true
  aviso_emitido: false
  partial_stop: false
```
