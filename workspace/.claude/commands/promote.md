---
description: CI-gated dev→main promotion runbook for one repo (human-confirmed dispatch).
argument-hint: <repo> [patch|minor|major]
---

Dispatch `release-manager` for: $ARGUMENTS

It must: verify the target repo's `dev` CI is green; agree the bump-type with the user
(`patch` default); STOP for explicit confirmation before running
`gh workflow run promote-dev-to-main.yml --repo AutomationNexus/<repo> -f bump-type=…`;
then monitor promote run → promote PR → main CI → release tag, reporting each gate.

Scope guard: only CognitiveSystems / MediaRefinery / ModelDeck / Uploadarr are
versioned. HomeAssistant promotes without a version bump. ARCRunner and the `template-*`
repos have no promote workflow — refuse with an explanation.
