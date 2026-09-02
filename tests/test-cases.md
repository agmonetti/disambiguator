# Disambiguator Test Battery

This test suite evaluates whether the Disambiguator prompt accurately catches ambiguities, avoids false positives on precise requests, behaves predictably in grey zones, and cleanly isolates mixed prompts.

---

## Evaluation Summary Table

| # | Category | Prompt Under Test | Ambiguity Types | Expected Action | Status |
|---|----------|-------------------|-----------------|-----------------|--------|
| 1 | **Must Stop** | *"Make the landing page look prettier and cleaner."* | Type A, Type B | Halt; offer design & section options | `[ ] PASS / [ ] FAIL` |
| 2 | **Must Stop** | *"Optimize the database queries."* | Type B, Type C | Halt; identify queries & metrics | `[ ] PASS / [ ] FAIL` |
| 3 | **Must Stop** | *"Add authentication to the project."* | Type C | Halt; offer auth strategies/providers | `[ ] PASS / [ ] FAIL` |
| 4 | **Must Stop** | *"Arreglá el código para que sea más profesional y rápido."* | Type A, Type B | Halt; define metric, files & standard | `[ ] PASS / [ ] FAIL` |
| 5 | **Must Stop** | *"Refactor the components to follow best practices."* | Type A, Type B | Halt; define scope & specific pattern | `[ ] PASS / [ ] FAIL` |
| 6 | **Must NOT Stop** | *"In `src/components/Button.tsx`, change the button background color from `#000000` to `#0070f3`."* | None | Execute directly | `[ ] PASS / [ ] FAIL` |
| 7 | **Must NOT Stop** | *"What is the difference between `useEffect` and `useLayoutEffect` in React?"* | None (Informational) | Answer directly without halting | `[ ] PASS / [ ] FAIL` |
| 8 | **Must NOT Stop** | *"Run `npm test` and report any failing suites."* | None (Deterministic) | Run command / execute directly | `[ ] PASS / [ ] FAIL` |
| 9 | **Must NOT Stop** | *"Add a column `last_login_at` (TIMESTAMP WITH TIME ZONE NULL) to `users` in `migrations/003.sql`."* | None | Edit target file directly | `[ ] PASS / [ ] FAIL` |
| 10 | **Must NOT Stop** | *"Explain why Docker multi-stage builds reduce final image footprint."* | None (Conceptual) | Answer directly without halting | `[ ] PASS / [ ] FAIL` |
| 11 | **Grey Zone** | *"Clean up the unused imports in `src/utils/math.ts`."* | Mild Type B | Strict: confirm removal. Soft: proceed safely. | `[ ] PASS / [ ] FAIL` |
| 12 | **Grey Zone** | *"Format this markdown table according to standard GFM rules."* | Standard pattern | Proceed directly (deterministic format) | `[ ] PASS / [ ] FAIL` |
| 13 | **Grey Zone** | *"Add a tooltip to the checkout submit button."* | Mild Type A/C | Ask for copy/trigger OR suggest standard copy | `[ ] PASS / [ ] FAIL` |
| 14 | **Grey Zone** | *"Refactor this 10-line helper to use early returns instead of nested if-else."* | Constrained Type B | Proceed (well-bounded, single idiom) | `[ ] PASS / [ ] FAIL` |
| 15 | **Grey Zone** | *"Make this API error message more user friendly."* | Type A | Halt; propose 3 concrete copy variations | `[ ] PASS / [ ] FAIL` |
| 16 | **Mixed** | *"Export `calculateTotal` in `src/billing.ts` and make the module nicer."* | Precise + Type A/B | Offer to export immediately; clarify 'nicer' | `[ ] PASS / [ ] FAIL` |
| 17 | **Mixed** | *"Bump version in `package.json` to 1.2.0 and modernize the docs."* | Precise + Type A/B | Update version; clarify doc changes | `[ ] PASS / [ ] FAIL` |
| 18 | **Mixed** | *"Create `POST /api/webhooks/stripe` with signature check, handle events properly."* | Precise + Type B/C | Confirm event handlers list before coding | `[ ] PASS / [ ] FAIL` |
| 19 | **Mixed** | *"Agregá un test para `validateEmail()` y mejorá los otros tests."* | Precise + Type B | Write email test; clarify scope of 'mejorá' | `[ ] PASS / [ ] FAIL` |
| 20 | **Mixed** | *"Delete deprecated `v1/auth.go` and clean up related legacy logic."* | Precise + Broad Type B | Delete file; confirm list of callers to remove | `[ ] PASS / [ ] FAIL` |

---

## Detailed Test Case Specifications

### Category 1: Must Stop (Clear Ambiguity)

#### Test Case 01: Pure Subjectivity + Undefined Scope
- **User Prompt**: *"Make the landing page look prettier and cleaner."*
- **Target Detection**:
  - `prettier`, `cleaner`: Type A (Pure Subjectivity)
  - `the landing page`: Type B (Scope Undefined if multi-component)
- **Expected Response**:
  - Does NOT edit any file.
  - Presents numbered multi-choice questions covering visual criteria and target sections.
  - Provides options (e.g., whitespace, typography, color palette).

#### Test Case 02: Undefined Scope + Missing Metrics
- **User Prompt**: *"Optimize the database queries."*
- **Target Detection**:
  - `Optimize`: Type B (Open-ended verb)
  - `the database queries`: Type B / Type C (Which queries, latency vs throughput, indexing vs rewriting)
- **Expected Response**:
  - Halts execution.
  - Queries which specific endpoints/queries to target and desired optimization strategy.

#### Test Case 03: Missing Architectural Context
- **User Prompt**: *"Add authentication to the project."*
- **Target Detection**:
  - `authentication`: Type C (Multiple incompatible architectures: JWT, Session cookies, OAuth2, Firebase, Auth0, Supabase)
- **Expected Response**:
  - Halts execution without installing dependencies.
  - Offers multiple choice auth mechanisms.

#### Test Case 04: Spanish Idiom + Subjective Speed
- **User Prompt**: *"Arreglá el código para que sea más profesional y rápido."*
- **Target Detection**:
  - `Arreglá el código`: Type B (Scope undefined)
  - `más profesional`: Type A (Subjective)
  - `rápido`: Type A / C (Runtime performance vs development speed vs perceived load)
- **Expected Response**:
  - Answers in Spanish.
  - Lists 3 ambiguities with options (a/b/c/d) for each.

#### Test Case 05: Unbounded Refactoring
- **User Prompt**: *"Refactor the components to follow best practices."*
- **Target Detection**:
  - `Refactor`: Type B
  - `the components`: Type B
  - `best practices`: Type A (Unanchored standard)
- **Expected Response**:
  - Halts and asks which components and which specific architectural pattern (e.g., compound components, custom hooks, container/presenter).

---

### Category 2: Must NOT Stop (Zero Ambiguity / Pure Theory)

#### Test Case 06: Deterministic Single-File Edit
- **User Prompt**: *"In `src/components/Button.tsx`, change the button background color from `#000000` to `#0070f3`."*
- **Target Detection**: None. Exact file, exact element, exact property, exact before/after values.
- **Expected Response**: Executes change directly or provides the exact code diff. Zero questions asked.

#### Test Case 07: Conceptual / Theoretical Query
- **User Prompt**: *"What is the difference between `useEffect` and `useLayoutEffect` in React?"*
- **Target Detection**: Negative constraint applies (pure informational query, no file modifications requested).
- **Expected Response**: Explains the difference immediately with code examples. No halts.

#### Test Case 08: Deterministic Command Execution
- **User Prompt**: *"Run `npm test` and report any failing suites."*
- **Target Detection**: Command and objective are fully specified.
- **Expected Response**: Executes the command or summarizes the result without prompting.

#### Test Case 09: Unambiguous Schema Migration
- **User Prompt**: *"Add a column `last_login_at` (TIMESTAMP WITH TIME ZONE NULL) to `users` in `migrations/003.sql`."*
- **Target Detection**: Target file, table, column name, data type, and nullability are 100% specified.
- **Expected Response**: Edits `migrations/003.sql` immediately.

#### Test Case 10: Architectural Explanation
- **User Prompt**: *"Explain why Docker multi-stage builds reduce final image footprint."*
- **Target Detection**: Negative constraint applies (no modifying action).
- **Expected Response**: Provides educational explanation immediately.

---

### Category 3: Grey Zone (Contextual & Mild Ambiguity)

#### Test Case 11: Localized Cleanup
- **User Prompt**: *"Clean up the unused imports in `src/utils/math.ts`."*
- **Target Behavior**:
  - **Strict Mode**: Clarifies if automated AST tree-shaking should run or if user wants to inspect them.
  - **Soft Mode**: Executes removal directly because scope is localized to 1 utility file and risk is minimal.

#### Test Case 12: Standard Formatting Task
- **User Prompt**: *"Format this markdown table according to standard GFM rules."*
- **Target Behavior**:
  - Should NOT stop because GitHub Flavored Markdown table syntax is deterministic and standard.

#### Test Case 13: UI Enhancement with Missing Microcopy
- **User Prompt**: *"Add a tooltip to the checkout submit button."*
- **Target Behavior**:
  - **Strict Mode**: Asks what text should appear in the tooltip (Type C).
  - **Soft Mode**: Suggests standard default (e.g., *"Click to confirm and process your order"*) and implements it with a note.

#### Test Case 14: Micro-Refactoring
- **User Prompt**: *"Refactor this 10-line helper to use early returns instead of nested if-else."*
- **Target Behavior**:
  - Well-bounded scope and single programming pattern. Should proceed without interrogation.

#### Test Case 15: Copywriting Adjustment
- **User Prompt**: *"Make this API error message more user friendly."*
- **Target Behavior**:
  - Type A (user friendly). The model should present 3 distinct copy proposals (concise, detailed with remediation, or polite) for selection.

---

### Category 4: Mixed Prompts (Precise Action + Ambiguous Tail)

#### Test Case 16: Isolated Change + Vague Module Goal
- **User Prompt**: *"Export `calculateTotal` in `src/billing.ts` and make the module nicer."*
- **Expected Protocol**:
  - Notes that `export function calculateTotal` is clear and ready.
  - Pauses the "make nicer" part and asks for specific criteria (types, docstrings, splitting files).

#### Test Case 17: Version Bump + Unbounded Documentation
- **User Prompt**: *"Bump version in `package.json` to 1.2.0 and modernize the docs."*
- **Expected Protocol**:
  - Identifies that bumping `package.json` is unambiguous.
  - Halts the documentation edit to clarify what "modernize" entails (Docusaurus/VitePress migration, README restyling, or updating code examples).

#### Test Case 18: Concrete Route + Implicit Handlers
- **User Prompt**: *"Create `POST /api/webhooks/stripe` with signature check, handle events properly."*
- **Expected Protocol**:
  - Halts to ask which Stripe event types must be handled (`checkout.session.completed`, `invoice.payment_failed`, `customer.subscription.deleted`, etc.).

#### Test Case 19: Targeted Test + Broad Testing Goal
- **User Prompt**: *"Agregá un test para `validateEmail()` y mejorá los otros tests."*
- **Expected Protocol**:
  - Replies in Spanish.
  - Identifies `validateEmail()` as actionable.
  - Clarifies what "mejorá" entails (coverage, mock cleanup, speed, edge-case assertions).

#### Test Case 20: Safe Deletion + Broad Ripple Effect
- **User Prompt**: *"Delete deprecated `v1/auth.go` and clean up related legacy logic."*
- **Expected Protocol**:
  - Warns that removing callers across the codebase is high-impact (Type B scope).
  - Lists callers found or asks whether to delete callers or stub them with errors.
