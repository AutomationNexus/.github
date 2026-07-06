---
description: Verify PR readiness with local QA and branch policy.
---

Confirm the current branch is not `main` unless explicitly documented as an exception.
Run the full `/qa` sequence via `qa-gatekeeper`. Report whether pushing/opening a PR is
allowed, with blockers. Direct pushes to `main` are forbidden. Do not edit files, push, or
open PRs.
