# Group B — Python package → PyPI (main-dev)

Template for a Python package published to PyPI. Matches CognitiveSystems.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`
(this repo only holds thin wrappers in `.github/workflows/`).

---

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-python-pypi \
  --private --clone
```

## 2. Bootstrap (one-time)

Run in **Git Bash / WSL** from a clone of the org `.github` repo:

```bash
cd /c/Users/<you>/.../GitHub/.github

CI_BOT_APP_ID=4168350 \
CI_BOT_APP_PRIVATE_KEY_PATH="/c/Users/<you>/Downloads/automationnexus-ci-bot.<date>.private-key.pem" \
PYPI_API_TOKEN="pypi-..." \
bash scripts/bootstrap-repo.sh AutomationNexus/<your-repo> B <private|public>
```

| Input | What | Example |
|------|------|---------|
| arg 1 | `owner/repo` of your new repo | `AutomationNexus/MyPkg` |
| arg 2 | group letter | `B` |
| arg 3 | visibility | `private` or `public` |
| env `CI_BOT_APP_ID` | CI-Bot App id | `4168350` |
| env `CI_BOT_APP_PRIVATE_KEY_PATH` | path to the App `.pem` | your Downloads path |
| env `PYPI_API_TOKEN` | **group B only** — PyPI token | `pypi-...` |

What it does: sets `CI_BOT_APP_ID` / `CI_BOT_APP_PRIVATE_KEY` **and** `PYPI_API_TOKEN`
repo secrets, creates `dev` as default, and (public only) applies the rulesets.

> **PyPI token:** create it at pypi.org → Account → API tokens. Account-scoped for the
> first publish (the project may not exist yet); project-scoped once it does. PyPI OIDC
> trusted publishing does NOT support reusable workflows, which is why a token is used.

## 3. Replace placeholders

- `.github/workflows/ci.yml`: `security-paths: src/<pkg>`; set `pip-install-cmd`, `test-cmd`;
  add `has-frontend: true` + `spa-artifact-path` if it bundles a built SPA.
- Version is read from `pyproject.toml` — bump it before promoting; the release tags
  `v<version>` and no-ops if the version is unchanged.

## 4. Add your code, then PR into `dev`

Feature branch → PR to `dev` (auto-merge on green). Promote dev→main to publish to PyPI.

## Notes

- Private repo: protection is CI guards + `auto-revert: true` (already set). Public gets rulesets.

## Out of the box

This template ships a working, green-CI Python project as-is, before you replace anything:

- [x] `pyproject.toml` + `src/REPLACE_ME/` + `tests/test_smoke.py` — `pip install -e ".[dev]"` +
  `python -m pytest -q` pass unmodified. `security-paths: src/REPLACE_ME` already matches the
  stub package, so `bandit` passes too.
- [x] `.gitignore`, `.githooks/pre-push`, `tools/install-githooks.cmd` — direct pushes to
  `dev`/`main` are blocked locally as well as by CI guards, once you run
  `tools\install-githooks.cmd`.
- [x] `CLAUDE.md` + `.claude/agents/qa-gatekeeper.md` + `.claude/settings.json` — open the
  repo in Claude Code, no bootstrap step needed.
- [ ] Rename `src/REPLACE_ME/` and the `REPLACE_ME` placeholders (see step 3 above) once you
  know your real package name — not required for CI to pass, just for the name to be real.
- [ ] Bump `pyproject.toml` version before your first release.
