# Group C — Home Assistant add-on (main-dev)

For a Home Assistant add-on repo. Matches ModelDeck-HAOS.

## Setup
1. Copy `.github/workflows/*` and `.github/dev-only-paths` into the new repo.
2. Replace `REPLACE_ME_ADDON_DIR` in `release.yml` with the add-on folder (the one holding `config.yaml`).
3. Install the **AutomationNexus CI Bot** App; add `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`.
4. Public repo: apply rulesets from `../../rulesets/`. Private repo: `auto-revert: true` in `ci.yml`.

## Notes
- CI runs add-on metadata validation (`has-addon-validate: true`).
- If this add-on is synced from a parent image repo, add the parent's sync job (see ModelDeck
  `release.yml` `sync-haos-stable`) using the CI-Bot App token — never a PAT.
- A nightly add-on roll/publish workflow is repo-specific; copy from ModelDeck-HAOS if needed.
