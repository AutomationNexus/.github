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
