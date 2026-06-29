# Group E — Home Assistant config (main-dev)

For a Home Assistant configuration repo. Matches HomeAssistant.

## Setup
1. Copy `.github/workflows/*` and `.github/dev-only-paths` into the new repo.
2. Install the **AutomationNexus CI Bot** App; add `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`.
3. Usually private on Free plan -> `auto-revert: true` is preset (guards enforce branch policy).
   If public, set it false and apply rulesets from `../../rulesets/`.

## Notes
- CI runs HA config check (`has-ha-validate: true`) and yamllint (`has-yaml-lint: true`).
- Provide `secrets.yaml.example`; the HA validate job copies it to `secrets.yaml` automatically.
- No release/nightly (config repo).
