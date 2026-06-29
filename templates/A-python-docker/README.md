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
- `.github/workflows/nightly.yml` + `release.yml`: `image-name: automationnexus/<repo>`.

## 4. Add your code, then PR into `dev`

Direct pushes to `dev`/`main` are blocked by guards. Open a feature branch → PR to `dev`.
Auto-merge merges when CI is green. Promote dev→main with the **Promote dev to main** workflow.

## Notes

- **Self-hosted (ARC) runners:** set `runner-labels: '["linux","x64","k3s","ubuntu-latest"]'` in every wrapper.
- **Private repo:** rulesets aren't available on GitHub Free, so protection is the CI guards +
  `auto-revert: true` (already set in `ci.yml`). Public repos get rulesets via bootstrap.
- Docker/GHCR push uses the built-in `GITHUB_TOKEN` — no extra secret.
