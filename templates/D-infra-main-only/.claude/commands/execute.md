---
description: Execute an approved plan through the QA gate (main-only repo).
argument-hint: [optional focus notes]
---

Run the execute pipeline for an approved plan: $ARGUMENTS

1. `git status --short --branch` — confirm a feature branch (not `main`); create one
   from updated `main` if needed.
2. Apply changes from the approved plan only.
3. Dispatch `qa-gatekeeper` for the full `/qa` local gate.
4. Stop on the first failed gate.
5. Push the feature branch and open a PR to `main` after user approval (never push
   directly to `main`).
