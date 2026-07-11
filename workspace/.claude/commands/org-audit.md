---
description: Org-wide security audit across all repo clones (read-only).
argument-hint: [optional focus]
---

Dispatch `security-officer` for an org-wide audit. Focus: $ARGUMENTS (default: full
sweep — secrets hygiene, workflow/token usage, `.claude/settings.json` denylist
consistency vs the `_shared` baseline, `dev-only-paths` coverage, ruleset coverage,
dependency risk).

Report findings ranked by severity with repo + file:line references. No fixes applied —
propose a follow-up action per finding instead.
