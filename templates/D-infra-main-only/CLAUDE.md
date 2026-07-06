# CLAUDE.md — REPLACE_ME (Group D: Infra / image builder, main-only)

<!-- Replace REPLACE_ME above and the paragraph below once the repo is renamed. -->
Single-branch infra/image-builder repo. No `dev` branch — feature branches go straight to
`main` via PR. CI/CD via `automationnexus/.github@v1` reusable workflows.

> **Note on this file's location:** the org convention commits `CLAUDE.md`/`.claude/` on
> `dev` and strips them from `main`. This repo is **main-only** (no `dev` branch), so that
> mechanism doesn't apply — this file is committed directly on `main` as a documented
> exception (see ARCRunner's `CLAUDE.md` for the precedent). If a `dev` branch is ever
> added to a repo made from this template, revisit and move to the standard dev-only
> convention.

## Branch rules

- Main-only. Never push directly to `main` except via the `github-actions[bot]` actor
  (workflow promotion, if any exists). Use a feature branch and open a PR to `main` for
  all human changes.
- Start every task with `git status --short --branch` before edits.
- Enable local hook once per clone: `tools\install-githooks.cmd`.

## QA gates (run before every PR)

```
git status --short --branch
git diff --check
```
Add lint/build verification commands here once `build-image.yml.example` is renamed and
`IMAGE` is set (see README.md step 3).

## Subagents

| Agent | Use for | Model |
|-------|---------|-------|
| `qa-gatekeeper` | Branch policy + QA gate before PR | haiku |

Keep this repo's agent set minimal (see ARCRunner) — an architect/reviewer/security-auditor
is over-engineering for a single Dockerfile/workflow surface. Add them only if this repo's
scope genuinely grows.

## Slash commands

`/qa` (QA gate), `/prepush` (PR readiness check).

## Shared CI — do not inline

- **Never inline or fork `automationnexus/.github` reusable-workflow logic** into this
  repo's own workflow files. Always call it via
  `uses: automationnexus/.github/.github/workflows/<name>.yml@v1`.
- If this repo needs CI behavior the shared workflow doesn't support, add a generic input
  to the shared workflow (contribute it to `automationnexus/.github`), never a local
  copy/paste workaround.
- Never use `GITHUB_TOKEN` for cross-repo automation — only the CI-Bot GitHub App, if this
  repo ever needs cross-repo writes.

## Do not

- Do not add model/provider/router config anywhere in this repo. Claude Code talks
  directly to Anthropic with the operator's own account.
- Do not commit real values for `CI_BOT_APP_PRIVATE_KEY` or any `.env`-style secret.
