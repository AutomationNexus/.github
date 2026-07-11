---
description: Execute an approved meta-repo plan through workflow-engineer, QA, and review.
argument-hint: [optional focus]
---

Confirm a feature branch off fresh `master`. Dispatch `workflow-engineer` for $ARGUMENTS,
then `qa-gatekeeper`, then `reviewer`. Stop on first failed gate. Push and open a PR to
`master` only after all gates pass. Do not run template/workspace sync follow-ups until
the PR merges; `sync-templates.sh` additionally requires explicit human confirmation.
