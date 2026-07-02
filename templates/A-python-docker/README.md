# Group A — Python service + Docker (main-dev)

Template for a Python service that ships a Docker image to GHCR.
Matches MediaRefinery / ModelDeck / Uploadarr.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`
(this repo only holds thin wrappers in `.github/workflows/`).

---

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-python-docker \
  --private --clone
```

## 2. Bootstrap (one-time wiring the template can't copy)

Run in **Git Bash / WSL** from a clone of the org `.github` repo
(`https://github.com/AutomationNexus/.github` → `scripts/bootstrap-repo.sh`):

```bash
cd /c/Users/<you>/.../GitHub/.github

CI_BOT_APP_ID=4168350 \
CI_BOT_APP_PRIVATE_KEY_PATH="/c/Users/<you>/Downloads/automationnexus-ci-bot.<date>.private-key.pem" \
bash scripts/bootstrap-repo.sh AutomationNexus/<your-repo> A <private|public>
```

| Input | What | Example |
|------|------|---------|
| arg 1 | `owner/repo` of your new repo | `AutomationNexus/MyService` |
| arg 2 | group letter | `A` |
| arg 3 | visibility | `private` or `public` |
| env `CI_BOT_APP_ID` | CI-Bot App id | `4168350` |
| env `CI_BOT_APP_PRIVATE_KEY_PATH` | path to the App `.pem` | your Downloads path |

What it does: sets the `CI_BOT_APP_ID` / `CI_BOT_APP_PRIVATE_KEY` repo secrets,
creates `dev` and makes it the default branch, and (public repos only) applies the
`protect-dev` + `protect-main` rulesets. The CI-Bot App is already installed org-wide,
so no per-repo App install is needed.

## 3. Replace placeholders

- `.github/workflows/ci.yml`: `security-paths: src/<pkg>`; set `has-frontend` / `has-e2e`,
  `pip-install-cmd`, `test-cmd`, `lint-paths`.
- `.github/workflows/nightly.yml` + `release.yml`: `image-name: automationnexus/<repo, lowercase>`
  -- Docker/GHCR rejects uppercase repository names even if your GitHub repo name has
  uppercase letters (e.g. `MyService` -> `image-name: automationnexus/myservice`).

## 4. Add your code, then PR into `dev`

Direct pushes to `dev`/`main` are blocked by guards. Open a feature branch → PR to `dev`.
Auto-merge merges when CI is green. Promote dev→main with the **Promote dev to main** workflow.

## Notes

- **Self-hosted (ARC) runners:** set `runner-labels: '["linux","x64","k3s","ubuntu-latest"]'` in every wrapper.
- **Private repo:** rulesets aren't available on GitHub Free, so protection is the CI guards +
  `auto-revert: true` (already set in `ci.yml`). Public repos get rulesets via bootstrap.
- Docker/GHCR push uses the built-in `GITHUB_TOKEN` — no extra secret.

## Out of the box

This template ships a working, green-CI Python project as-is, before you replace anything:

- [x] `pyproject.toml` + `src/REPLACE_ME/` + `tests/test_smoke.py` — `pip install -e ".[dev]"` +
  `python -m pytest -q` pass unmodified. `security-paths: src/REPLACE_ME` already matches the
  stub package, so `bandit` passes too.
- [x] `.gitignore`, `.githooks/pre-push`, `tools/install-githooks.cmd` — direct pushes to
  `dev`/`main` are blocked locally as well as by CI guards, once you run
  `tools\install-githooks.cmd`.
- [x] `opencode.json.example` + `tooling/opencode/` — run `tools\bootstrap-opencode.cmd`
  (or `.ps1`) to get a working local OpenCode setup.
- [x] `mkdocs.yml` + `docs/README.md` + `.github/workflows/docs.yml` — MkDocs Material site,
  deploys on push to `main` if GitHub Pages is enabled. Delete all three if you don't want docs.
- [ ] Rename `src/REPLACE_ME/` and the `REPLACE_ME` placeholders (see step 3 above) once you
  know your real package/image name — not required for CI to pass, just for the name to be real.
