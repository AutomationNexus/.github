# CLAUDE.md — REPLACE_ME (Group B: Python package → PyPI)

<!-- Replace REPLACE_ME above and the paragraph below once the repo is renamed. -->
Python package published to PyPI. CI/CD via `automationnexus/.github@v1` reusable
workflows (this repo only holds thin wrappers in `.github/workflows/`).

## Conventions

- Package: `src/REPLACE_ME/`. Tests: `tests/`.
- Version in `pyproject.toml` is bumped automatically by the promote workflow (`bump-type`
  input on its `workflow_dispatch`: `patch`/`minor`/`major`, default `patch`) — never
  hand-edit it.
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
| `qa-gatekeeper` | Local QA gate — pass/fail report only, no edits | haiku |

Add `architect`/`reviewer`/`security-auditor` (opus/sonnet/opus) once the repo has real
scope beyond the stub — see CognitiveSystems's `CLAUDE.md` for the pattern to copy.

## Slash commands

`/qa` (QA gate), `/prepush` (PR readiness check).

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
- Do not commit real values for `CI_BOT_APP_PRIVATE_KEY`, `PYPI_API_TOKEN`, or any
  `.env`-style secret.
