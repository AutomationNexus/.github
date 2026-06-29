# Group B — Python package -> PyPI (main-dev)

For a Python package published to PyPI. Matches CognitiveSystems.

## Setup
1. Copy `.github/workflows/*` and `.github/dev-only-paths` into the new repo.
2. Replace `REPLACE_ME` in `ci.yml` (`security-paths`), set `pip-install-cmd`/`test-cmd`,
   and `has-frontend: true` + `spa-artifact-path` if it bundles a built SPA.
3. Install the **AutomationNexus CI Bot** App; add `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`.
4. **PyPI:** create an API token (project-scoped once the project exists on PyPI; account-scoped
   for the very first publish) and add it as repo secret **`PYPI_API_TOKEN`**.
5. Version is read from `pyproject.toml` — bump it before promoting; the release tags `v<version>`
   and no-ops if that version is unchanged.
6. Public repo: apply rulesets from `../../rulesets/`. Private repo: `auto-revert: true` in `ci.yml`.

## Note on PyPI + reusable workflows
PyPI OIDC trusted publishing does **not** support reusable workflows, so this flow uses an
API token (works from the shared reusable). That is why `PYPI_API_TOKEN` is required.
