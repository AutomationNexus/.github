---
description: Org-wide security audit across all repo clones (read-only).
argument-hint: [optional focus]
---

Dispatch `security-officer` for an org-wide audit. Focus: $ARGUMENTS (default: full
sweep — secrets hygiene, workflow/token usage, `.claude/settings.json` denylist
consistency vs the `_shared` baseline, `dev-only-paths` coverage, ruleset coverage,
dependency risk).

Before reporting, cross-check every finding against `automationnexus/.github`'s
`governance/registry.yml`:

- If `scripts/validate-governance.py --live` is runnable from the `.github` clone, run
  it first and fold its output in — don't re-derive checks it already covers
  (escalation-chain validity, mutation-class-vs-tool-grant mismatches, repo-core team
  composition, live default-branch drift).
- A gap that matches a registered `exceptions:` entry (e.g. ARCRunner's minimal team,
  a template repo's stub team) is a **known exception**, not a fresh finding — cite the
  registry entry instead of re-flagging it as new.
- A gap with no matching registry entry is a **real finding** — report it, and note
  that it should also land in the registry (as a fix or a documented exception) so a
  future audit doesn't rediscover it from scratch.
- Anything the registry marks `state: needs-verification` that this audit successfully
  checks live should be called out separately so the registry's `state:` can be
  updated to `active`/`exception` in a follow-up PR.

Report findings ranked by severity with repo + file:line references. No fixes applied —
propose a follow-up action per finding instead.
