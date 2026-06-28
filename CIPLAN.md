# Org CI Standardization Plan

## Repo Categorization

| Repo | Template | Runner | Has Frontend | Has E2E | Has Integration | Has Security | Has Semgrep | Has Nightly | Has Docs | Release Type |
|------|----------|--------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|---|
| CognitiveSystems | main-dev | `[linux,x64,k3s,ubuntu-latest]` | ✓ | ✓ | - | ✓ | +Add | - | - | pypi |
| HomeAssistant | main-dev | `[linux,x64,k3s,ubuntu-latest]` | - | - | - | - | - | - | - | none (addon-validate) |
| MediaRefinery | main-dev | `["ubuntu-latest"]` | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | docker |
| ModelDeck | main-dev | `["ubuntu-latest"]` | - | - | ✓(mosquitto) | ✓ | ✓ | ✓ | ✓ | docker + haos-sync |
| ModelDeck-HAOS | main-dev | `["ubuntu-latest"]` | - | - | - | - | - | ✓(bespoke) | - | addon |
| Uploadarr | main-dev | `[linux,x64,k3s,ubuntu-latest]` | ✓ | ✓ | - | ✓ | ✓ | ✓ | ✓ | docker |
| ARCRunner | main-only | `["ubuntu-latest"]` | - | - | - | - | - | - | - | none (img-build) |

## Reusable Workflows (`automationnexus/.github`)

### ci-main-dev.yml — Full CI (main+dev)
- Guards: guard-dev-push, guard-main-push, guard-dev-source, guard-main-source, guard-main-files (step-level early-exit, never SKIPPED)
- hygiene, lint, test-standards (always run)
- frontend, test, e2e, integration, security, ha-validate, addon-validate (gated by inputs)
- Status checks get `ci / ` prefix
- Secrets: inherit

### ci-main-only.yml — Simplified CI (main-only)
- Guards: guard-main-push, guard-main-source
- hygiene, optional lint/test/security/build

### auto-merge.yml — Squash feat→dev, merge commit dev→main
- Called by local `pull_request_target` wrapper
- Permissions: contents:write, pull-requests:write

### promote-dev-to-main.yml — PR-based promotion
- Gate: green dev CI → open or find dev→main PR → gh pr merge --auto --merge
- Uses GITHUB_TOKEN (no PAT needed)

### release-docker.yml — GHCR Docker publish
- Inputs: image-name, platforms, runner-labels
- Jobs: prepare → [lint+test+frontend if main_push] → build-and-push → trivy-scan → github-release

### release-pypi.yml — PyPI OIDC publish
- Jobs: prepare → verify-dev-ci → [lint+test+frontend if main_push] → publish (ubuntu-24.04) → github-release
- Consumer must set `permissions: id-token: write` + `environment: pypi`

### release-addon.yml — Tag + GitHub Release
- Version from config.yaml, tag + GH Release

### nightly.yml — Docker nightly from dev
- detect-changes → lint+test+frontend → move-tag → build-and-push → trivy-scan

### semgrep.yml — SAST scan
- push/PR to main,dev + weekly schedule

### docs.yml — MkDocs → Pages
### Versions
- actions/checkout@v6, setup-python@v6, setup-node@v5, github-script@v8
- docker/setup-buildx-action@v4, docker/login-action@v4, docker/build-push-action@v7
- actions/upload-artifact@v7, actions/download-artifact@v8
- softprops/action-gh-release@v3
- aquasecurity/trivy-action@master (optional, advisory)
- actions/deploy-pages@v5, actions/upload-pages-artifact@v5

## Rulesets
- protect-main.json: PR required, no deletions, no fast-forward
  - Required: Guard Main Source Branch, hygiene, lint, test-standards, Python Tests, Semgrep (prefix: `ci / `)
- protect-dev.json: same structure, different contexts
- protect-main-only.json: for ARCRunner

## Key Decisions
- Reusable workflows, copy-paste eliminated
- PR-based promote (not force-push)
- pull_request_target auto-merge
- 3 release templates (not 1)
- All repos unified with same guard/hygiene/auto-merge structure
- Parity gaps fixed during migration
- Check names get `ci / ` prefix; rulesets updated accordingly
