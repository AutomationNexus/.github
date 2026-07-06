---
description: Run local QA checks and report pass/fail blockers.
---

Dispatch `qa-gatekeeper`: `git status --short --branch`, `python -m yamllint .`,
`git diff --check`, plus HA config check if Docker is available. Return pass/fail and
actionable blockers only. No file edits.
