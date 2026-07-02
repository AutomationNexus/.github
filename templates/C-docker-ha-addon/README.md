# Group C — App + in-repo Home Assistant add-on (main-dev)

Template for a repo that is **both** a Docker app **and** a Home Assistant add-on
repository — the add-on folder(s) are thin wrappers (`FROM` your own published image) that
live directly in this repo, not a separate repo. Matches ModelDeck's proven pattern
(`automationnexus/ModelDeck`), not the older separate-addon-repo pattern.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`
(this repo only holds thin wrappers in `.github/workflows/`).

## Why one repo, not two

Home Assistant reads only a repository's default branch (`main`) and discovers **every**
add-on folder in it as a separately installable add-on — a repo can hold more than one
add-on. There's no way for a user to "subscribe to a different branch" for nightly vs.
stable, so both channels have to be folders on `main`, not separate repos or branches. See
`docs/getting-started/haos-addon.md` in ModelDeck for the end-user-facing explanation.

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-docker-ha-addon \
  --private --clone
```

## 2. Bootstrap (one-time)

Run in **Git Bash / WSL** from a clone of the org `.github` repo:

```bash
cd /c/Users/<you>/.../GitHub/.github

CI_BOT_APP_ID=4168350 \
CI_BOT_APP_PRIVATE_KEY_PATH="/c/Users/<you>/Downloads/automationnexus-ci-bot.<date>.private-key.pem" \
bash scripts/bootstrap-repo.sh AutomationNexus/<your-repo> C <private|public>
```

What it does: sets the CI-Bot App repo secrets, creates `dev` as default, and
(public only) applies the rulesets.

## 3. Replace placeholders

Search for `REPLACE_ME` across the repo and fill in:

| Placeholder | What |
|---|---|
| `REPLACE_ME` (image name, in `ci.yml`/`nightly.yml`/`release.yml`) | `automationnexus/<your-image, lowercase>` -- Docker/GHCR rejects uppercase repository names |
| `REPLACE_ME_ADDON_DIR` | Your stable-channel add-on folder name (holds `config.yaml`) |
| `REPLACE_ME_ADDON_DIR-nightly` | Your nightly-channel add-on folder name — **delete every reference to this** (and the `roll-nightly-addon` job in `nightly.yml`, the `exclude-paths` block in `promote-dev-to-main.yml`) if you don't ship a nightly channel |
| `REPLACE_ME_IMAGE_NAME` (in `tools/check_build_from.py`, `tools/sync_haos_addon.py`) | The image name segment inside `BUILD_FROM` |
| `src/REPLACE_ME` (in `ci.yml` `security-paths`) | Your app's source path |

If you only ship a **stable** channel (no nightly add-on), delete: the `roll-nightly-addon`
job in `nightly.yml`, and the `exclude-paths` input in `promote-dev-to-main.yml` (main no
longer needs protecting from a nightly pointer that doesn't exist).

If you only ship a **nightly** channel (no stable add-on tracking a versioned release),
delete: `sync-addon-stable` in `release.yml`, and the `push: dev, paths:` trigger in
`promote-dev-to-main.yml`.

## 4. Add your add-on folder(s), then PR into `dev`

Feature branch → PR to `dev` (auto-merge on green). From there, everything is automatic:

- **App code change** → nightly build fires on every `dev` push (event-driven, no cron
  needed except as a zero-activity fallback).
- **Nightly-channel-only change** (`REPLACE_ME_ADDON_DIR-nightly/**`) → publishes straight to
  `main` via `nightly.yml`'s `roll-nightly-addon` job. Loop-free by construction (writes only
  to `main`, never back to `dev`).
- **App release** (version bump, promoted to `main`) → `release.yml` builds the image, then
  `sync-addon-stable` PRs the new pin to `dev`; merging that PR auto-fires the promote.
- **Stable-channel-only change** (`REPLACE_ME_ADDON_DIR/**`, no new app release) →
  `promote-dev-to-main.yml`'s `push: dev, paths:` trigger auto-fires; content lands on
  `main` immediately (version stays unchanged — stable is always bare `X.Y.Z`, no
  packaging-revision suffix). Existing installed users see it bundled at the next real
  release; test add-on-only changes via the nightly channel first.

No manual promote clicks needed in the normal flow — `workflow_dispatch` on
`promote-dev-to-main.yml` stays available as a manual fallback.

## Notes / lessons learned (read before changing any of this)

- **`main` is a ruleset-protected branch.** A raw `git push` is rejected even from the
  CI-Bot App's bypass — the bypass covers required-check overrides on PR *merges*, not the
  `pull_request`-required rule itself. Every automated write here goes branch → PR → merge.
- **`exclude-paths`'s temp-branch snapshot of `main` can race** with another workflow (e.g.
  a concurrent nightly publish) pushing to `main` between the snapshot and the merge. The
  shared `promote-dev-to-main.yml` retries the whole cycle from a fresh snapshot up to 3
  times on conflict — don't remove that retry loop.
- **The very first promote** after adding these add-on folders will have no prior state on
  `main` to diff against — `bump_haos_version.py` and the shared `exclude-paths` logic both
  handle "path doesn't exist on old main yet" as "nothing to protect / nothing to diff",
  not as an error or a deletion.
- CI ships with `has-addon-validate: false` — flip it to `true` once you've added
  `repository.yaml` and your add-on folder(s) (see the placeholder table above); the check
  fails on a fresh repo since there's no add-on metadata to validate yet.
- Private repo: protection is CI guards + `auto-revert: true` (already set). Public gets
  rulesets.

## Out of the box

This template ships a working, green-CI Python project as-is, before you replace anything:

- [x] `pyproject.toml` + `src/REPLACE_ME/` + `tests/test_smoke.py` — `pip install -e ".[dev]"` +
  `python -m pytest -q` pass unmodified. `security-paths: src/REPLACE_ME` already matches the
  stub package, so `bandit` passes too.
- [x] `has-addon-validate: false` by default — CI is green before you've added an add-on
  folder. Flip to `true` once `repository.yaml` + your add-on folder(s) exist.
- [x] `.gitignore`, `.githooks/pre-push`, `tools/install-githooks.cmd` — direct pushes to
  `dev`/`main` are blocked locally as well as by CI guards, once you run
  `tools\install-githooks.cmd`.
- [x] `opencode.json.example` + `tooling/opencode/` — run `tools\bootstrap-opencode.cmd`
  (or `.ps1`) to get a working local OpenCode setup.
- [x] `mkdocs.yml` + `docs/README.md` + `.github/workflows/docs.yml` — MkDocs Material site,
  deploys on push to `main` if GitHub Pages is enabled. Delete all three if you don't want docs.
- [ ] Rename `src/REPLACE_ME/` and fill in every other `REPLACE_ME*` placeholder (see table
  above) once you know your real package/image/add-on names.
