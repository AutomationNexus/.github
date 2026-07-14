---
description: Sync templates/ bundles to the 5 template-* repos (direct push — human confirmation required).
argument-hint: [group letters, e.g. A C]
---

Dispatch `template-steward` to sync template groups: $ARGUMENTS (default: all 5).

Procedure it must follow, in order:

1. Show what changed under `.github/templates/` since the last sync (`git log`/`diff`
   in the `.github` clone).
2. Run `scripts/sync-templates.sh --check` and show the orphan/drift report.
3. Restate that this script DIRECT-PUSHES to the template repos' `main` — the org's one
   documented direct-push exception (`CLAUDE.md`'s "Unified authority and confirmation")
   — and STOP for explicit human confirmation.
4. Only after confirmation: run `scripts/sync-templates.sh [groups]` from the `.github`
   clone (Git Bash), then verify each synced repo's latest `main` commit landed.
