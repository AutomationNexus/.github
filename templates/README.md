# New-repo starter bundles

Copy one group's `.github/workflows/*` (and `.github/dev-only-paths`) into a new repo,
replace the `REPLACE_ME*` placeholders, then add the required secrets.

| Group | Use for | Branch model | Release | Runners |
|-------|---------|--------------|---------|---------|
| **A — python-docker** | Python service shipping a Docker image | main-dev | `release-docker` + `nightly` | `["ubuntu-latest"]` (public) |
| **B — python-pypi** | Python package published to PyPI | main-dev | `release-pypi` | `["ubuntu-latest"]` |
| **C — ha-addon** | Docker app + in-repo HA add-on folder(s) (proven pattern: ModelDeck) | main-dev | `release-docker` + `nightly` (in-repo pointer bumps, no separate add-on release) | `["ubuntu-latest"]` |
| **D — infra-main-only** | Image/infra builder, single branch | main-only | custom build | `["ubuntu-latest"]` |
| **E — ha-config** | Home Assistant config repo | main-dev | none | self-hosted/ubuntu |

## Secrets every repo needs
- `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY` — the AutomationNexus CI Bot GitHub App (install the App on the repo first).

## Extra secrets by group
- **B (PyPI):** `PYPI_API_TOKEN` (project- or account-scoped). Add as a repo secret.
- Docker/GHCR push uses the built-in `GITHUB_TOKEN` — no extra secret.

## Private repos (GitHub Free, no rulesets)
Set `auto-revert: true` in `ci.yml` and rely on the CI guards. Public repos instead get
rulesets (`protect-dev`/`protect-main`) with the CI-Bot App as bypass actor — see
`../rulesets/`.

## Self-hosted (ARC) repos
Use `runner-labels: '["linux","x64","k3s","ubuntu-latest"]'` in every wrapper.

## AI tooling (local-only vs shared)
- Local-only (gitignored, never committed): `opencode.json`, `.opencode/`, `CLAUDE.md`, `AGENTS.md`.
- Shared templates (committed): `tooling/opencode/**`, `opencode.json.example`, `tools/bootstrap-opencode.*`.
- `.github/dev-only-paths` blocks the local-only files from ever reaching `main`.

## Keeping the 5 template repos in sync -- mandatory after any change here

The 5 `AutomationNexus/template-*` GitHub repos (`template-python-docker`,
`template-python-pypi`, `template-ha-addon`, `template-infra-main-only`,
`template-ha-config`) are **not** auto-synced from this directory -- they were caught
badly out of date once already (missing an org-wide bug fix, and one still had an
entire superseded pattern). After changing anything under `templates/<group>/`, run:

```bash
scripts/sync-templates.sh          # all 5 groups
scripts/sync-templates.sh C        # just one group
```

before considering the change done. This is not optional -- it's exactly the kind of
gap that silently reintroduces already-fixed bugs into every new repo created
afterward.
