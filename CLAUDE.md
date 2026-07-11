# CLAUDE.md — automationnexus/.github

This is the AutomationNexus org meta-repo: reusable GitHub Actions workflows, repo
templates (groups A–E), branch-protection rulesets, and the bootstrap/sync scripts
that wire a new repo together. See `README.md` for the full architecture; this file
is instructions for Claude Code when working in this repo specifically.

## What this repo is NOT

It is not an application. There is no build, no tests to run for "the product" —
the "product" is the workflow YAML and the template bundles. Validate changes by
reasoning about the YAML/script logic and, where possible, by checking out a
consumer repo and running its CI.

## Golden rule: reusable workflows, never copy-paste

- `.github/workflows/*.yml` here are called by every consumer repo via
  `uses: automationnexus/.github/.github/workflows/<name>.yml@v1`.
- If a consumer repo needs new behavior, the fix is a new **generic input** on the
  shared workflow — never a one-off fork in the consumer repo. Precedent: `build-args`,
  `main-source-allow-glob`, `exclude-paths`, `strip-dev-only-paths`, `bump-type`,
  `main-only` (auto-merge.yml).
- Tag stable changes `@v1` only after they're proven; `@latest` tracks HEAD.

## Templates (`templates/<group>/` + `templates/_shared/`)

- Five groups: `A-python-docker`, `B-python-pypi`, `C-docker-ha-addon`,
  `D-infra-main-only`, `E-ha-config`. Each is a full starter bundle for the matching
  `AutomationNexus/template-*` repo.
- `templates/_shared/` holds files common to multiple groups (gitignore, dev-only-paths,
  githooks, CLAUDE.md template, tools). Groups compose from `_shared` plus their own
  group-specific files.
- **After editing anything under `templates/`, run `scripts/sync-templates.sh`.** It does
  not auto-sync to the real `AutomationNexus/template-*` repos — that is a separate,
  explicit step (requires push access to those repos).

## Bootstrap script (`scripts/bootstrap-repo.sh`)

Wires a new repo after "Use this template": creates `dev`, sets repo secrets
(`CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`, `PYPI_API_TOKEN` for group B), applies
rulesets for public repos. Treat this script carefully — it writes real repo secrets
via `gh secret set`. Never hardcode a token value in this repo; it only ever reads
from the operator's local env at bootstrap time.

## AI tooling convention (org-wide)

This org standardizes on Claude Code. The standard per-repo layout:

- `CLAUDE.md` at repo root — project-specific instructions.
- `.claude/agents/*.md` — repo-specific subagents.
- `.claude/settings.json` — permission denylist (secrets, destructive git ops); never
  put provider/model routing or tokens here.
- `.claude/settings.local.json` — personal, gitignored, never committed.
- `CLAUDE.local.md` — personal per-project notes, gitignored, never committed.

**Dev-only convention (this org's choice):** `CLAUDE.md` and `.claude/` are committed
on `dev` but must be stripped from `main`. The promote-dev-to-main workflow only does this
when its caller passes `strip-dev-only-paths: true` — every consumer repo's
`.github/workflows/promote-dev-to-main.yml` must set it (alongside a `.github/dev-only-paths`
file) or these files will reach `main` and fail `ci.yml`'s Guard Main Files hygiene check.
`main` stays a lean, AI-instructions-free public artifact. Full rationale and rollout status:
[`docs/ai-migration.md`](docs/ai-migration.md).

`templates/_shared/CLAUDE.md.template` and `templates/_shared/.claude/` are the seeds
new repos start from — keep them in sync with whatever pattern proves out during rollout.

## Org-tier workspace layer (`workspace/`)

`workspace/` is the canonical, versioned source for the AutomationNexus workspace root's
`CLAUDE.md` + `.claude/` (the "CTO desk": 6 org agents + 7 org commands). The workspace
root is not a git repo, so `scripts/sync-workspace.sh` copies this layer into place locally;
`--check` reports drift and `--force` backs up before overwrite. Edit `workspace/` here via
PR to `master`, never the root copies.

Two separate propagation scripts serve different protection models:

- `scripts/sync-templates.sh` — bundle → 5 `template-*` repos. Direct-push exception;
  always requires explicit human confirmation. `--check` reports managed `.claude/` orphans.
- `scripts/sync-shared-claude.sh` — `_shared/.claude` → app repos. Protected-branch-safe:
  opens feature-branch PRs to `dev`; preserves repo-specific content; excludes ARCRunner's
  documented minimal-team exception.

## Do not

- Do not add per-repo model/provider/router config anywhere in this org. Claude Code
  is used directly against Anthropic; there is no proxy/router in the standard workflow.
- Do not commit real values for `CI_BOT_APP_PRIVATE_KEY`, `PYPI_API_TOKEN`, or any
  `.env`-style secret in any template or script.
