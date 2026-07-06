---
description: Verify PR readiness with local QA and branch policy.
---

Confirm the current branch is a feature branch (not `dev`/`main`). Run the full `/qa`
sequence via `qa-gatekeeper`. Report whether pushing/opening a PR is allowed, with
blockers. Direct pushes to `dev`/`main` are forbidden. Do not edit files, push, or open PRs.
