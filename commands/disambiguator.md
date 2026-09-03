---
description: Set Disambiguator operational mode (strict|soft|status|off)
---

Switch Disambiguator mode to $ARGUMENTS.
- If the argument is "soft", switch to soft mode (halt on Type A & high-risk Type B; assume safest standard for Type C & low-risk Type B).
- If the argument is "strict" or empty, switch to strict mode (halt on all Type A, B, and C ambiguities before taking action).
- If the argument is "off", disable Disambiguator gatekeeper prompt injection.
- If the argument is "status", display the current active mode.

Acknowledge the mode update immediately following the Disambiguator Runtime Mode Control Protocol and adopt it for all subsequent turns.
