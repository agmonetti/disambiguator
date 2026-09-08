---
description: Set Disambiguator operational mode (strict|soft|status|off)
---

Inspect or switch Disambiguator mode according to $ARGUMENTS.
- If the argument is "soft", switch to soft mode (halt on Type A & high-risk Type B; assume safest standard for Type C & low-risk Type B).
- If the argument is "strict", switch to strict mode (halt on all Type A, B, and C ambiguities before taking action).
- If the argument is "off", disable Disambiguator gatekeeper prompt injection.
- If the argument is "status" or empty, display the current active mode.

Respond with the corresponding confirmation block from the Disambiguator Runtime Mode Control Protocol and adopt the resulting mode for all subsequent turns.
