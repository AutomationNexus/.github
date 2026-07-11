# CLAUDE.md — REPLACE_ME (Group C: App + in-repo HA add-on)

<!-- Replace REPLACE_ME above and every REPLACE_ME* placeholder below once the repo is
     renamed and the add-on folder(s) are named — see README.md step 3. -->
Docker app that is also a Home Assistant add-on repository — the add-on folder(s) are
thin wrappers (`FROM` this app's own published image) living directly in this repo. CI/CD
via `automationnexus/.github@v1` reusable workflows.

## Conventions

- App package: `src/REPLACE_ME/`. Tests: `tests/`.
- Add-on folder(s): `REPLACE_ME_ADDON_DIR/` (stable), optionally `REPLACE_ME_ADDON_DIR-nightly/`.
  Each `config.yaml` defines `options`/`schema`/`version`/`slug` (slug must match the
  folder name); mirror every `options` key in `schema` with the correct HA type.
- **Never hand-edit `version:` or `CHANGELOG.md` in an add-on folder** once versioning
  automation is wired up (see ModelDeck's CLAUDE.md for the full versioning-cascade
  pattern to copy once this repo has real release automation).

## Branch policy

- `dev` (default) → `main` via the **Promote dev to main** GitHub Actions workflow (also
  fires automatically for add-on-only changes — see README.md). Never push directly to
  `dev` or `main`.
- Start every task with `git status --short --branch` before edits.
- Enable local hook once per clone: `tools\install-githooks.cmd`.

## QA gates (run before every PR)

```
git status --short --branch
pip install -e ".[dev]"
python -m pytest -q
git diff --check
```
Once `has-addon-validate: true` is flipped on (after adding `repository.yaml` + add-on
folder(s)), also run: `python tools/validate_ha_addon.py`, `python tools/check_build_from.py`.

## Subagents

| Agent | Use for | Model |
|-------|---------|-------|
| `architect` (high effort) | Design/boundaries/release risk — before implementing | sonnet |
| `qa-gatekeeper` | Local QA gate (incl. add-on validation) — pass/fail only, no edits | haiku |
| `reviewer` | Independent review before PR | sonnet |
| `security-auditor` (high effort) | Secrets, workflow changes, dependency risk | sonnet |

This is the org-standard shared core (sourced from `automationnexus/.github`
`templates/_shared/.claude/`; this group overlays its own add-on-aware
`qa-gatekeeper`/`qa`). Add domain engineers (`addon-engineer`, and e.g. `mqtt-engineer`)
once the repo has real scope — see ModelDeck's `CLAUDE.md` and `.claude/agents/` for the
dual-domain (app + add-on) pattern to copy.

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
