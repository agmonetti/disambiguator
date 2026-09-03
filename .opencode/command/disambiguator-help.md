---
description: Quick reference for Disambiguator modes, active status, and commands
---

Show the Disambiguator quick reference card. One shot, change nothing: do not modify code, execute tools, or persist state changes.

Display:
1. Active Status: Report the current Disambiguator operational mode (strict / soft / off).
2. Operational Modes:
   - strict (default): Halts on all Type A (Subjectivity), Type B (Scope), and Type C (Context assumptions) ambiguities before taking action.
   - soft: Halts on Type A & high-risk Type B (destructive changes); automatically assumes the safest standard path (Option a) for Type C & low-risk Type B and proceeds.
   - off: Temporarily disables Disambiguator cognitive gatekeeper prompt injection.
3. Available Commands:
   - /disambiguator [strict|soft|status|off]: Switch or inspect operational mode.
   - /disambiguator-help: Display this quick reference card.
