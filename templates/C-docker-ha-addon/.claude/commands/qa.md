---
description: Run local QA checks and report pass/fail blockers.
---

Dispatch `qa-gatekeeper`: `git status --short --branch`, `python -m pytest -q`,
`git diff --check`, plus add-on validation if applicable. Return pass/fail and actionable
blockers only. No file edits.
