# New-repo starter bundles

Copy one group's `.github/workflows/*` (and `.github/dev-only-paths`) into a new repo,
replace the `REPLACE_ME*` placeholders, then add the required secrets.

| Group | Use for | Branch model | Release | Runners |
|-------|---------|--------------|---------|---------|
| **A — python-docker** | Python service shipping a Docker image | main-dev | `release-docker` + `nightly` | `["ubuntu-latest"]` (public) |
| **B — python-pypi** | Python package published to PyPI | main-dev | `release-pypi` | `["ubuntu-latest"]` |
| **C — docker-ha-addon** | Docker app + in-repo HA add-on folder(s) (proven pattern: ModelDeck) | main-dev | `release-docker` + `nightly` (in-repo pointer bumps, no separate add-on release) | `["ubuntu-latest"]` |
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

## AI tooling (Claude Code)
- Full-team groups A/B/C/E ship the org-standard shared core from
  `_shared/.claude/`: `architect` (sonnet/high), `qa-gatekeeper` (haiku), `reviewer`
  (sonnet), `security-auditor` (sonnet/high), plus `/execute`, `/qa`, `/prepush`,
  `/release`. The group-specific `.claude/` directory overlays that core (e.g. C's
  add-on QA, E's yamllint/HA QA) and wins on conflicts.
- Group D deliberately mirrors ARCRunner's minimal-team exception: only
  `qa-gatekeeper` + `/execute`/`/qa`/`/prepush`; shared core copy is skipped.
- Every group gets `.claude/settings.json` from
  `_shared/.claude/settings.json.template` at sync time. A/B/C/D correctly have no
  bundle-level settings copy; E legitimately overlays it with `secrets.yaml` denies.
  This is composition, not a missing file.
- Each group ships a real, ready-to-use `CLAUDE.md`; no bootstrap step needed — just
  open the repo in Claude Code.
- Convention: `CLAUDE.md`/`.claude/` are committed on `dev`, stripped from `main` by
  `.github/dev-only-paths` (group D / main-only repos are a documented exception — see
  that group's `CLAUDE.md`). Only `CLAUDE.local.md` and `.claude/settings.local.json` are
  gitignored (personal, never shared).
- No model/provider/router config in any template — Claude Code talks directly to
  Anthropic with the operator's own account.

## Keeping the 5 template repos in sync -- mandatory after any change here

The 5 `AutomationNexus/template-*` GitHub repos (`template-python-docker`,
`template-python-pypi`, `template-docker-ha-addon`, `template-infra-main-only`,
`template-ha-config`) are **not** auto-synced from this directory -- they were caught
badly out of date once already (missing an org-wide bug fix, and one still had an
entire superseded pattern). After changing anything under `templates/<group>/`, run:

```bash
scripts/sync-templates.sh --check  # read-only orphan report first
scripts/sync-templates.sh          # all 5 groups (direct push; human-confirmed)
scripts/sync-templates.sh C        # just one group
```

before considering the change done. This is not optional -- it's exactly the kind of
gap that silently reintroduces already-fixed bugs into every new repo created
afterward.
