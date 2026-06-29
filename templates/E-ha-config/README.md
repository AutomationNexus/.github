# Group E — Home Assistant config (main-dev)

Template for a Home Assistant configuration repo. Matches HomeAssistant.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`
(this repo only holds thin wrappers in `.github/workflows/`).

---

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-ha-config \
  --private --clone
```

## 2. Bootstrap (one-time)

Run in **Git Bash / WSL** from a clone of the org `.github` repo:

```bash
cd /c/Users/<you>/.../GitHub/.github

CI_BOT_APP_ID=4168350 \
CI_BOT_APP_PRIVATE_KEY_PATH="/c/Users/<you>/Downloads/automationnexus-ci-bot.<date>.private-key.pem" \
bash scripts/bootstrap-repo.sh AutomationNexus/<your-repo> E <private|public>
```

| Input | What | Example |
|------|------|---------|
| arg 1 | `owner/repo` of your new repo | `AutomationNexus/MyHAConfig` |
| arg 2 | group letter | `E` |
| arg 3 | visibility | `private` or `public` |
| env `CI_BOT_APP_ID` | CI-Bot App id | `4168350` |
| env `CI_BOT_APP_PRIVATE_KEY_PATH` | path to the App `.pem` | your Downloads path |

What it does: sets the CI-Bot App repo secrets, creates `dev` as default, and
(public only) applies the rulesets.

## 3. Add files

- Provide `secrets.yaml.example`; the HA validate job copies it to `secrets.yaml` automatically.

## 4. Edit config, then PR into `dev`

Feature branch → PR to `dev` (auto-merge on green). Promote dev→main with the
**Promote dev to main** workflow.

## Notes

- CI runs HA config check (`has-ha-validate: true`) and yamllint (`has-yaml-lint: true`).
- Usually private on Free → protection is CI guards + `auto-revert: true` (already set).
  If public, the bootstrap applies rulesets instead.
- No release/nightly (config repo).
