---
description: Run meta-repo validation and report pass/fail blockers.
---

Dispatch `qa-gatekeeper`: branch check, `git diff --check`, `bash -n scripts/*.sh`, JSON
parse checks, agent-frontmatter validation, and
`python scripts/validate-governance.py`. Report pass/fail only; no edits.
