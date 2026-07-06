---
description: Run local QA checks and report pass/fail blockers.
---

Dispatch `qa-gatekeeper`: `git status --short --branch` (confirm not `main`),
`git diff --check`. Return pass/fail and actionable blockers only. No file edits.
