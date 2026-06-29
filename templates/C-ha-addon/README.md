# Group C — Home Assistant add-on (main-dev)

Template for a Home Assistant add-on repo. Matches ModelDeck-HAOS.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`
(this repo only holds thin wrappers in `.github/workflows/`).

---

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-ha-addon \
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

| Input | What | Example |
|------|------|---------|
| arg 1 | `owner/repo` of your new repo | `AutomationNexus/MyAddon` |
| arg 2 | group letter | `C` |
| arg 3 | visibility | `private` or `public` |
| env `CI_BOT_APP_ID` | CI-Bot App id | `4168350` |
| env `CI_BOT_APP_PRIVATE_KEY_PATH` | path to the App `.pem` | your Downloads path |

What it does: sets the CI-Bot App repo secrets, creates `dev` as default, and
(public only) applies the rulesets.

## 3. Replace placeholders

- `.github/workflows/release.yml`: `REPLACE_ME_ADDON_DIR` → the add-on folder that holds
  `config.yaml` (the version is read from there).

## 4. Add your add-on, then PR into `dev`

Feature branch → PR to `dev` (auto-merge on green). Promote dev→main to tag + release.

## Notes

- CI runs add-on metadata validation (`has-addon-validate: true`).
- If this add-on is synced from a parent image repo, copy the parent's sync job from
  ModelDeck `release.yml` (`sync-haos-stable`) — it uses the **CI-Bot App token**, never a PAT.
- A nightly add-on roll/publish workflow is repo-specific; copy from ModelDeck-HAOS if needed.
- Private repo: protection is CI guards + `auto-revert: true` (already set). Public gets rulesets.
