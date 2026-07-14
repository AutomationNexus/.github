---
description: Run meta-repo validation and report pass/fail blockers.
---

Dispatch `qa-gatekeeper`: branch check, `git diff --check`, `bash -n scripts/*.sh`, JSON
parse checks, agent-frontmatter validation, and (when `governance/`, any `.claude/`, or
`workspace/` changed) `python scripts/validate-governance.py` and
`python -m unittest tests/test_governance_scenarios.py`. Report pass/fail only; no edits.
