# Project OpenCode Rules

<!-- REPLACE_ME: one-line description of what this repo does. -->

## Shell (Windows local dev)

- Chain commands with `;`, not `&&` or `||`.
- Use Windows paths (`\` or quoted full paths). Do not mix cmd/bash/PowerShell syntax.
- Outside a clone: `gh --repo automationnexus/<repo> <subcommand>`.
- For CI logs: `gh run view <id> --log-failed`; use `Select-Object -Last N` instead of `tail`.
- Debug: one command per tool call.
- CI workflows keep bash on `ubuntu-latest`; do not change workflow shells.

## Safety Rules

- Start every task with `git status --short --branch`.
- Never read, print, copy, edit, or commit credentials (`.env`, `secrets.yaml`, tokens, API
  keys, cookies).
- Never create/track `AGENT-HANDOFF.md`, `AGENTS.md`, `CLAUDE.md`.
- Do not commit `opencode.json` or `.opencode/`.

## QA Gates (run before PR)

- `git status --short --branch`
- `ruff check <lint-paths>` (match `.github/workflows/ci.yml`'s `lint-paths` input)
- `python -m pytest -q`
- `pre-commit run --all-files` (when installed)
- `git diff --check`

## Token-Efficient Handoff (agent-to-agent)

- Goal: one sentence.
- Files read/touched: paths only.
- Current branch/status: short.
- Decisions: max 5 bullets.
- Remaining work: max 5 bullets.
- Validation: commands + pass/fail only.
- Risks/blockers: actionable only.

No large file contents, raw diffs, secrets, or full logs.

## Branch Policy

<!-- REPLACE_ME: pick the paragraph matching this repo's branch-model input in ci.yml. -->
- **main-dev** (groups A/B/C/E): `dev` is workbench, `main` is stable. No direct pushes
  (enforced by CI guards + `.githooks/pre-push`). Feature branch → PR to `dev` → CI green →
  merge → delete branch. Promote `dev`→`main` only via the **Promote dev to main** workflow.
- **main-only** (group D): no `dev` branch. Feature branch → PR to `main` → CI green → merge.
- Enable hooks once: `tools/install-githooks.cmd`.

## Shared CI — Do Not Inline

- **Never inline or fork `automationnexus/.github` reusable-workflow logic** into this repo's
  own workflow files, even temporarily. Always call it via
  `uses: automationnexus/.github/.github/workflows/<name>.yml@v1`.
- If this repo needs CI behavior the shared workflow doesn't support, the fix is a new
  **generic** input on the shared workflow (contributed to `automationnexus/.github`), never
  a local copy/paste workaround.
- Never use `GITHUB_TOKEN` or a personal access token for cross-branch or cascade automation
  — only the CI-Bot GitHub App.
- Before touching any `.github/workflows/*.yml` file here, check `automationnexus/.github`
  first — most CI behavior lives there, not in this repo's thin wrapper.
