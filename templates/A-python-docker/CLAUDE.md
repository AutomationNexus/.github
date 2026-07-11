# CLAUDE.md — REPLACE_ME (Group A: Python service + Docker)

<!-- Replace REPLACE_ME above and the paragraph below once the repo is renamed. -->
Python service that ships a Docker image to GHCR. CI/CD via `automationnexus/.github@v1`
reusable workflows (this repo only holds thin wrappers in `.github/workflows/`).

## Conventions

- Package: `src/REPLACE_ME/`. Tests: `tests/`.
- Keep changes minimal; run the QA gate before every PR.

## Branch policy

- `dev` (default) → `main` via the **Promote dev to main** GitHub Actions workflow. Never
  push directly to `dev` or `main`.
- Start every task with `git status --short --branch` before edits.
- Enable local hook once per clone: `tools\install-githooks.cmd`.

## QA gates (run before every PR)

```
git status --short --branch
pip install -e ".[dev]"
python -m pytest -q
git diff --check
```
Adjust lint/test commands here once real code replaces the `REPLACE_ME` stub.

## Subagents

| Agent | Use for | Model |
|-------|---------|-------|
| `architect` (high effort) | Design/boundaries/release risk — before implementing | sonnet |
| `qa-gatekeeper` | Local QA gate — pass/fail report only, no edits | haiku |
| `reviewer` | Independent review before PR | sonnet |
| `security-auditor` (high effort) | Secrets, workflow changes, dependency risk | sonnet |

This is the org-standard shared core (sourced from `automationnexus/.github`
`templates/_shared/.claude/` — keep the `<!-- repo-specific -->` marker in each file
when customizing). Add domain engineer agents (e.g. `backend-engineer`,
`frontend-engineer`) once the repo has real scope — see a sibling repo's
`.claude/agents/` (MediaRefinery, ModelDeck, Uploadarr) for the pattern.

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
  automation (nightly, promote, release) — only the CI-Bot GitHub App.

## Do not

- Do not add model/provider/router config anywhere in this repo. Claude Code talks
  directly to Anthropic with the operator's own account.
- Do not commit real values for `CI_BOT_APP_PRIVATE_KEY` or any `.env`-style secret.
