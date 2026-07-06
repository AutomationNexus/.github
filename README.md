# automationnexus/.github

Org-wide GitHub Actions reusable workflows, repo templates, and shared config for AutomationNexus.

## Reusable workflows (`.github/workflows/`, pin `@v1`)

| Workflow | Purpose | Key inputs / secrets |
|----------|---------|----------------------|
| `ci.yml` | Unified CI: guards + hygiene + lint + test + optional frontend/e2e/integration/security/ha/addon | `branch-model`, `auto-revert`, `runner-labels`, `has-*`, `lint-paths`, `security-paths`, `pip-install-cmd`, `test-cmd`, `pre/post-test-cmd`, e2e-* · secrets: `ci-bot-app-id`, `ci-bot-app-private-key` |
| `auto-merge.yml` | Waits for PR checks, then merges via CI-Bot App | secrets: `ci-bot-app-id`, `ci-bot-app-private-key` |
| `promote-dev-to-main.yml` | Verifies dev CI, opens dev→main PR, waits for its CI, merges | `runner-labels`, `exclude-paths` (paths main owns exclusively; promoted via a throwaway branch instead of dev directly) · CI-Bot secrets |
| `nightly.yml` | Nightly Docker build from dev | `image-name`, `platforms`, `force_run`, `has-frontend`, `coverage-threshold`, `pip-install-cmd`, `test-cmd` |
| `release-docker.yml` | Tag (from pyproject) → build/push GHCR → Release → Trivy | `image-name`, `platforms`, `tag_name`, `has-frontend`, `has-validation` |
| `release-pypi.yml` | Tag (from pyproject) → build wheel → PyPI upload (token) → Release | `has-frontend`, `tag_name` · secret: `pypi-api-token` |
| `semgrep.yml` | SAST scan | none |
| `docs.yml` | MkDocs Material → GitHub Pages | none |

Tags: `@v1` (stable) and `@latest` track the current release. Pin to a SHA for stricter security.

## Authentication model

- **CI-Bot GitHub App** (`AutomationNexus CI Bot`, app id `4168350`) performs all merges/promotions/
  cross-repo syncs. App-token pushes cascade to downstream workflows (unlike `GITHUB_TOKEN`).
  Every consumer repo stores `CI_BOT_APP_ID` + `CI_BOT_APP_PRIVATE_KEY` as repo secrets and the App
  must be installed on the repo.
- **No PATs.** The old `REPO_DISPATCH_PAT` is fully removed.
- **PyPI**: token-based (`PYPI_API_TOKEN`) because PyPI OIDC trusted publishing rejects reusable
  workflows. Docker/GHCR uses the built-in `GITHUB_TOKEN`.

## Branch protection

- **Public repos**: rulesets `protect-dev` / `protect-main` with the CI-Bot App as bypass actor — see
  `.github/rulesets/`.
- **Private repos** (GitHub Free can't use rulesets): CI guards + `auto-revert: true` in `ci.yml`.

## CI/CD flow

```
feature → PR to dev → ci.yml (guards/lint/test/…) + semgrep → auto-merge (CI-Bot, after green) → dev
dev → nightly.yml (build :nightly)
promote-dev-to-main (CI-Bot): dev CI green → dev→main PR → its CI green → merge
main push → release-{docker|pypi}.yml → tag (from pyproject) → publish → GitHub Release
```

## New repos

- **Full guide**: [`docs/new-repo-guide.md`](docs/new-repo-guide.md) — click-to-create + the
  `scripts/bootstrap-repo.sh` one-shot that wires branches, default branch, secrets, and protection.
- **Starter bundles**: `.github/templates/<group>/` — copy the whole `.github/` for the matching group:
  - `A-python-docker`, `B-python-pypi`, `C-docker-ha-addon`, `D-infra-main-only`, `E-ha-config`
  - See `.github/templates/README.md` for the group table and per-group setup.
  - **After editing any starter bundle, run `scripts/sync-templates.sh`** — it does not auto-sync to the `AutomationNexus/template-*` repos.

## AI tooling

The org uses **Claude Code**. Convention: `CLAUDE.md` and
`.claude/agents|commands|settings.json` are **committed on `dev`**, stripped from `main`
by `.github/dev-only-paths`; only `CLAUDE.local.md` and `.claude/settings.local.json` are
gitignored (personal, never shared). No model/provider/router config lives in any repo —
Claude Code talks directly to Anthropic with the operator's own account.

See [`docs/ai-migration.md`](docs/ai-migration.md) for the full decision record, model-tier
mapping, and per-repo rollout status.
