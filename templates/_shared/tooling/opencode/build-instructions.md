# Build Mode

You are the execute orchestrator for this repo. Use built-in `build` only after an approved
plan, or when the user says go, build, or execute.

## Branch

- Start with `git status --short --branch`.
- Work on a feature branch, never commit directly on `dev` or `main` (see Branch Policy in
  `project-rules.md`).
- Never `git push origin dev` or `git push origin main`.

## Execute pipeline

1. Implement the approved plan.
2. Run the QA gate from `project-rules.md` (lint, tests, `pre-commit`) before opening a PR.
   Stop on the first failed gate.
3. Push the feature branch and open a PR (to `dev` for main-dev groups, to `main` for
   main-only groups). Never push directly to a protected branch.
4. For releases, follow this repo's release workflow only after explicit user approval.

Use the compact handoff format from `project-rules.md` before switching agents/sessions.
