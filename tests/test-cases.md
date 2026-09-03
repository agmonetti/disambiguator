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
| 08 | **Must NOT Stop** | *"Run `npm test` and report any failing suites."* | `[]` | Run command / execute directly | `[ ] PASS / [ ] FAIL` |
| 09 | **Must NOT Stop** | *"Add column `last_login_at` (TIMESTAMP WITH TIME ZONE NULL) to `users` in `migrations/003.sql`."* | `[]` | Edit target file directly | `[ ] PASS / [ ] FAIL` |
| 10 | **Must NOT Stop** | *"Explain why Docker multi-stage builds reduce final image footprint."* | `[]` | Answer conceptual query immediately | `[ ] PASS / [ ] FAIL` |
| 11 | **Grey Zone** | *"Clean up the unused imports in `src/utils/math.ts`."* | `[B]` | Strict: confirm removal. Soft: proceed with note. | `[ ] PASS / [ ] FAIL` |
| 12 | **Grey Zone** | *"Format this markdown table according to standard GFM rules."* | `[]` | Proceed directly (deterministic format) | `[ ] PASS / [ ] FAIL` |
| 13 | **Grey Zone** | *"Add a tooltip to the checkout submit button."* | `[A, C]` | Strict: ask text/trigger. Soft: suggest default. | `[ ] PASS / [ ] FAIL` |
| 14 | **Grey Zone** | *"Refactor this 10-line helper to use early returns instead of nested if-else."* | `[B]` | Proceed directly (single bounded idiom) | `[ ] PASS / [ ] FAIL` |
| 15 | **Grey Zone** | *"Make this API error message more user friendly."* | `[A]` | Halt; offer 3 concrete copy variations | `[ ] PASS / [ ] FAIL` |
| 16 | **Mixed** | *"Export `calculateTotal` in `src/billing.ts` and make the module nicer."* | `[A, B]` | Partial stop: export ready; clarify 'nicer' | `[ ] PASS / [ ] FAIL` |
| 17 | **Mixed** | *"Bump version in `package.json` to 1.2.0 and modernize the docs."* | `[A, B]` | Partial stop: bump ready; clarify doc scope | `[ ] PASS / [ ] FAIL` |
| 18 | **Mixed** | *"Create `POST /api/webhooks/stripe` with signature check, handle events properly."* | `[B, C]` | Partial stop: route clear; clarify event types | `[ ] PASS / [ ] FAIL` |
| 19 | **Mixed** | *"Agregá un test para `validateEmail()` y mejorá los otros tests."* | `[B]` | Partial stop in ES: test ready; clarify scope | `[ ] PASS / [ ] FAIL` |
| 20 | **Mixed** | *"Delete deprecated `v1/auth.go` and clean up related legacy logic."* | `[B]` | Partial stop: deletion clear; clarify callers | `[ ] PASS / [ ] FAIL` |

---

## Detailed Test Cases & Automation Assertions

### Category 1: Must Stop (Clear Ambiguity)

#### Test Case 01: Pure Subjectivity + Undefined Scope
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
- **Prompt**: `"Run npm test and report any failing suites."`
- **Ambiguity Types**: `[]`
- **Expected Behavior**: Executes the terminal command or offers to run it without asking clarifying questions.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes: environment_dependent: true, context: chat_no_tools
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


#### Test Case 09: Unambiguous Schema Migration
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
- **Prompt**: `"In src/utils/math.ts: import { add, unusedHelper } from './ops'; export const fn = () => add(1, 2); Clean up the unused imports."`
- **Ambiguity Types**: `[B]`
- **Expected Behavior**:
  - In `strict` mode: Asks confirmation to remove unused imports.
  - In `soft` mode: Removes unused imports directly and emits a 1-line notice stating the scope taken.
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


#### Test Case 12: Standard Formatting Task
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
- **Prompt**: `"Refactor this 10-line helper to use early returns instead of nested if-else: function check(u) { if (u) { if (u.active) return true; } return false; }"`
- **Ambiguity Types**: `[B]`
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
- **Prompt**: `"Export calculateTotal in src/billing.ts and make the module nicer."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Partial stop. States that exporting `calculateTotal` is ready; pauses "make nicer" and asks for criteria.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: false
  ambiguity_types_flagged: ["A", "B"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```

#### Test Case 17: Version Bump + Unbounded Documentation
- **Prompt**: `"Bump version in package.json to 1.2.0 and modernize the docs."`
- **Ambiguity Types**: `[A, B]`
- **Expected Behavior**: Partial stop. Identifies `package.json` bump as actionable; halts on "modernize docs" to clarify scope.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes: In partial-stop responses, code output is not required in the same turn. Declarative announcement of the deterministic action is sufficient. Actual execution is environment-dependent.
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
- **Prompt**: `"Create POST /api/webhooks/stripe with signature check, handle events properly."`
- **Ambiguity Types**: `[B, C]`
- **Expected Behavior**: Partial stop. Route and signature verification are clear; halts to confirm specific Stripe event types.
- **Manual Verification**: `[ ] PASS / [ ] FAIL` | Notes:
```yaml
assertions:
  contains_question: true
  min_questions: 1
  no_code_executed: true
  ambiguity_types_flagged: ["A", "C"]
  proceeds_directly: false
  aviso_emitido: false
  partial_stop: true
```

#### Test Case 19: Targeted Test + Broad Testing Goal
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
