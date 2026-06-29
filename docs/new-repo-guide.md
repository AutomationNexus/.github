# Creating a new AutomationNexus repo (groups A–E)

This guide gives you the fastest path to a new repo that already has the unified CI/CD,
branch protection, and secrets wired up.

## What CAN and CANNOT be auto-set

GitHub's "Use this template" (and `gh repo create --template`) copies **files only**. It does
**not** copy secrets, rulesets, branch protection, App installations, or extra branches. So the
realistic model is: **template gives you the files; a one-time bootstrap script wires the rest.**

| Thing | Auto from template? | How it gets set |
|------|--------------------|-----------------|
| Workflow files, dev-only-paths, gitignore | ✅ yes | template repo contents |
| `dev` branch (besides `main`) | ⚠️ only with "include all branches" | bootstrap creates `dev` |
| `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY` | ❌ no | bootstrap sets repo secrets |
| `PYPI_API_TOKEN` (group B) | ❌ no | bootstrap sets repo secret |
| CI-Bot **App installation** on the repo | ❌ no | one click in the App settings (or org "all repos" install) |
| Rulesets (public) / guards (private) | ❌ no | bootstrap applies `rulesets/*.json` |
| Default branch = dev | ❌ no | bootstrap sets it |

> Tip: if you install the **AutomationNexus CI Bot** App on **All repositories** at the org level,
> every new repo gets the App automatically and you only need the two App secrets (which are per-repo
> on Free because org secrets can't target private repos).

## Option 1 — Template repos (recommended, click-to-create)

We maintain one **template repository per group**: `automationnexus/template-<group>`
(e.g. `template-python-docker`). Each is a real repo marked as a GitHub *template*, containing the
group's `.github/` wrappers + starter files.

1. On the template repo page → **Use this template → Create a new repository**.
2. Name it, choose owner `AutomationNexus`, set visibility.
3. Run the bootstrap script (below) once to wire branches, secrets, default branch, protection.

To (re)create the template repos from the starter bundles in this repo, see
`templates/<group>/` and run `scripts/make-template-repos.sh` (maintainer task).

## Option 2 — `gh` one-liner from a template

```bash
gh repo create AutomationNexus/<new-repo> \
  --template AutomationNexus/template-python-docker \
  --private --clone
```

Then run the bootstrap script.

## Bootstrap script (wires everything the template can't)

`scripts/bootstrap-repo.sh` in this repo does, for a given repo + group:

1. Create `dev` branch from `main` and set **default branch = dev** (skip for group D / main-only).
2. Set repo secrets `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY` (reads values from your local env).
3. For group B: set `PYPI_API_TOKEN`.
4. Public repo: apply `rulesets/protect-main.json` (+ `protect-dev.json` unless main-only).
   Private repo: nothing (guards + auto-revert already in the wrappers).
5. Print the remaining manual step: install the CI-Bot App on the repo (if not org-wide).

Usage:
```bash
# env: CI_BOT_APP_ID, CI_BOT_APP_PRIVATE_KEY_PATH, (PYPI_API_TOKEN for group B)
scripts/bootstrap-repo.sh <owner/repo> <group:A|B|C|D|E> <public|private>
```

## Per-group placeholders to replace after creation

| Group | Replace |
|------|---------|
| A python-docker | `ci.yml` `security-paths`; `nightly.yml`+`release.yml` `image-name`; set `pip-install-cmd`/`test-cmd`, frontend/e2e toggles |
| B python-pypi | `ci.yml` `security-paths`; ensure `pyproject.toml` version; add `PYPI_API_TOKEN` secret |
| C ha-addon | `release.yml` `config-path` / add-on dir |
| D infra-main-only | `build-image.yml` `IMAGE` + Dockerfile path |
| E ha-config | provide `secrets.yaml.example` |

## After bootstrap: verify

```bash
gh secret list --repo AutomationNexus/<repo>
gh api repos/AutomationNexus/<repo>/rulesets --jq '[.[].name]'   # public only
gh api repos/AutomationNexus/<repo> --jq '.default_branch'
```
Open a test PR into dev and confirm CI + auto-merge behave.
