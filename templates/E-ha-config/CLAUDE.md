# CLAUDE.md — REPLACE_ME (Group E: Home Assistant config)

<!-- Replace REPLACE_ME above and the paragraph below once the repo is renamed. -->
Home Assistant configuration repo. CI/CD via `automationnexus/.github@v1` reusable
workflows (this repo only holds thin wrappers in `.github/workflows/`).

## Conventions

- `configuration.yaml` is the entrypoint. Replace the stub config with your real one.
- `secrets.yaml.example` is copied to `secrets.yaml` automatically by CI — never commit
  real `secrets.yaml` values.

## Branch policy

- `dev` (default) → `main` via the **Promote dev to main** GitHub Actions workflow. Never
  push directly to `dev` or `main`.
- Start every task with `git status --short --branch` before edits.
- Enable local hook once per clone: `tools\install-githooks.cmd`.

## QA gates (run before every PR)

```
git status --short --branch
python -m yamllint .
git diff --check
```
Plus the HA config check (`has-ha-validate: true` in CI) when Docker is available locally.

## Secrets / never read or print

- Never read, print, or commit `secrets.yaml`, tokens, or any real Home Assistant
  credential. `secrets.yaml.example` is the only safe placeholder file.

## Subagents

| Agent | Use for | Model |
|-------|---------|-------|
| `architect` (high effort) | Design/boundaries/release risk — before implementing | sonnet |
| `qa-gatekeeper` | Local QA gate (yamllint + HA config check) — pass/fail only, no edits | haiku |
| `reviewer` | Independent review before PR | sonnet |
| `security-auditor` (high effort) | Secrets, workflow changes, dependency risk | sonnet |

This is the org-standard shared core (sourced from `automationnexus/.github`
`templates/_shared/.claude/`; this group overlays its own yamllint-flavored
`qa-gatekeeper`/`qa` and a `secrets.yaml`-aware `settings.json`). Add
`yaml-engineer`/`live-inspector` once the repo has real scope — see HomeAssistant's
`CLAUDE.md` and `.claude/agents/` for the full pattern to copy (note: that repo is a
private live-instance digital twin; adapt the live-inspector/drift-sync agents only if
this repo also tracks a live instance).

## Slash commands

`/execute` (build pipeline), `/qa` (QA gate), `/prepush` (PR readiness check),
`/release` (dev→main promotion).

## Shared CI — do not inline

- **Never inline or fork `automationnexus/.github` reusable-workflow logic** into this
  repo's own workflow files. Always call it via
  `uses: automationnexus/.github/.github/workflows/<name>.yml@v1`.
- If this repo needs CI behavior the shared workflow doesn't support, add a generic input
  to the shared workflow (contribute it to `automationnexus/.github`), never a local
  copy/paste workaround.
- Never use `GITHUB_TOKEN` or a personal access token for cross-branch or cascade
  automation (promote) — only the CI-Bot GitHub App.

## Do not

- Do not add model/provider/router config anywhere in this repo. Claude Code talks
  directly to Anthropic with the operator's own account.
- Do not commit real values for `CI_BOT_APP_PRIVATE_KEY` or any secret.
