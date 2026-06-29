# Group A — Python service + Docker (main-dev)

For a Python service that ships a Docker image to GHCR. Matches MediaRefinery / ModelDeck / Uploadarr.

## Setup
1. Copy `.github/workflows/*` and `.github/dev-only-paths` into the new repo.
2. Replace `REPLACE_ME`:
   - `ci.yml`: `security-paths: src/<pkg>`, set `has-frontend`/`has-e2e` and `pip-install-cmd`/`test-cmd`.
   - `nightly.yml` + `release.yml`: `image-name: automationnexus/<repo>`.
3. Install the **AutomationNexus CI Bot** App on the repo; add secrets `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`.
4. Public repo: apply rulesets from `../../rulesets/`. Private repo: set `auto-revert: true` in `ci.yml`.
5. Add the AI gitignore snippet (`../_shared/gitignore-ai-snippet`) to `.gitignore`.

## Self-hosted (ARC) runners
Set `runner-labels: '["linux","x64","k3s","ubuntu-latest"]'` in every wrapper.
