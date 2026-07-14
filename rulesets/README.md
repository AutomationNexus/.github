# Rulesets (public repos only)

GitHub Free does not support rulesets/branch protection on **private** repos —
those rely on the CI guards + `auto-revert: true` instead.

`actor_id: 4168350` is the **AutomationNexus CI Bot** App (bypass actor) so promote/
auto-merge can push. If the App ID ever changes, update both JSON files.

Apply to a public repo:
```
gh api repos/AutomationNexus/<repo>/rulesets -X POST --input protect-main.json
gh api repos/AutomationNexus/<repo>/rulesets -X POST --input protect-dev.json   # skip for main-only repos
```

Required checks are the universally-present ones (`ci / hygiene`, `ci / lint`,
`semgrep / Semgrep`) so a skipped optional job never blocks merges.

## `.github` itself (`protect-master.json`)

`.github`'s own trunk is `master` (no dev/main split — see the repo's `CLAUDE.md`). Apply:
```
gh api repos/AutomationNexus/.github/rulesets -X POST --input protect-master.json
```

`.github`'s workflow files under `.github/workflows/` (`ci.yml`, `semgrep.yml`, etc.) are
`workflow_call`-only reusable-workflow *definitions* for consumer repos — `.github` never
triggered them on itself, so before this ruleset existed its own PRs reported zero status
checks. `self-ci.yml` and `self-semgrep.yml` are the thin caller wrappers that give
`.github` the same `ci / hygiene`, `ci / lint`, `semgrep / Semgrep` checks every consumer
repo already has (same pattern as `ARCRunner/.github/workflows/ci.yml` for the `main-only`
branch model and `CognitiveSystems/.github/workflows/semgrep.yml`) — named `self-*` only
because `ci.yml`/`semgrep.yml` are already taken by the reusable-workflow source files in
this same directory. Without them, `required_status_checks` in `protect-master.json` would
require checks that never report and permanently block every PR into `master`.
