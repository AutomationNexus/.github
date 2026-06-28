# automationnexus/.github

Org-wide GitHub Actions reusable templates and shared configuration for AutomationNexus.

## Reusable Workflows

| Workflow | When to use | Inputs |
|----------|------------|--------|
| `ci-main-dev.yml` | Repos with `main` + `dev` branches | runner-labels, has-frontend, has-e2e, has-integration, has-security, has-ha-validate, has-addon-validate |
| `ci-main-only.yml` | Repos with only `main` branch | runner-labels, has-lint, has-test, has-security |
| `auto-merge.yml` | Called by local `pull_request_target` wrapper | none |
| `promote-dev-to-main.yml` | Manual dev → main promotion | runner-labels |
| `release-docker.yml` | Docker image → GHCR | image-name, platforms, has-frontend |
| `release-pypi.yml` | Python package → PyPI (OIDC) | has-frontend |
| `release-addon.yml` | HA add-on tag + Release | config-path |
| `nightly.yml` | Nightly Docker build from dev | image-name, platforms, has-frontend |
| `semgrep.yml` | SAST scan | none |
| `docs.yml` | MkDocs → GitHub Pages | none |

## Usage

Each consumer repo keeps thin wrapper workflows that call these templates.

Example `ci.yml`:
```yaml
name: CI
on:
  pull_request: { branches: [main, dev] }
  push: { branches: [main, dev] }
jobs:
  ci:
    uses: automationnexus/.github/.github/workflows/ci-main-dev.yml@v1
    secrets: inherit
    with:
      runner-labels: '["ubuntu-latest"]'
      has-frontend: true
      has-security: true
      coverage-threshold: 90
```

Version: `@v1` branch. Pin to SHA for stricter security.

## Rulesets

Standard branch protection rules in `.github/rulesets/`. Apply per-repo with:
```
gh api repos/<org>/<repo>/rulesets -X POST --input .github/rulesets/protect-main.json
```
