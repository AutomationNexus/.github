# Group D — Infra / image builder (main-only)

Template for a single-branch infra repo. Matches ARCRunner.
No `dev` branch, no promote/nightly — feature branches go straight to `main` via PR.

CI/CD is provided by the org reusable workflows in `automationnexus/.github@v1`.

---

## 1. Create your repo from this template

**Use this template → Create a new repository** (owner `AutomationNexus`), or:

```bash
gh repo create AutomationNexus/<your-repo> \
  --template AutomationNexus/template-infra-main-only \
  --private --clone
```

## 2. Bootstrap (one-time)

Run in **Git Bash / WSL** from a clone of the org `.github` repo:

```bash
cd /c/Users/<you>/.../GitHub/.github

CI_BOT_APP_ID=4168350 \
CI_BOT_APP_PRIVATE_KEY_PATH="/c/Users/<you>/Downloads/automationnexus-ci-bot.<date>.private-key.pem" \
bash scripts/bootstrap-repo.sh AutomationNexus/<your-repo> D <private|public>
```

| Input | What | Example |
|------|------|---------|
| arg 1 | `owner/repo` of your new repo | `AutomationNexus/MyInfra` |
| arg 2 | group letter | `D` |
| arg 3 | visibility | `private` or `public` |
| env `CI_BOT_APP_ID` | CI-Bot App id | `4168350` |
| env `CI_BOT_APP_PRIVATE_KEY_PATH` | path to the App `.pem` | your Downloads path |

What it does (group D): sets the CI-Bot App repo secrets and (public only) applies the
`protect-main` ruleset. It does **not** create a `dev` branch (main-only model).

## 3. For an image builder

Rename `.github/workflows/build-image.yml.example` → `build-image.yml` and set
`IMAGE` + the Dockerfile path.

## 4. Add your code, then PR into `main`

`branch-model: main-only` — feature branches → PR to `main`. Image push uses the built-in
`GITHUB_TOKEN` (no extra secret).
