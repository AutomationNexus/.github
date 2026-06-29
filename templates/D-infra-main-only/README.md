# Group D — Infra / image builder (main-only)

For single-branch infra repos. Matches ARCRunner.

## Setup
1. Copy `.github/workflows/ci.yml`, `semgrep.yml`, `.github/dev-only-paths`.
2. For an image builder, rename `build-image.yml.example` -> `build-image.yml` and set `IMAGE` + Dockerfile path.
3. Install the **AutomationNexus CI Bot** App; add `CI_BOT_APP_ID`, `CI_BOT_APP_PRIVATE_KEY`.
4. Apply only the `protect-main` ruleset (no dev branch).

## Notes
- `branch-model: main-only` — PRs go feature -> main; no dev branch, no promote/nightly.
- Image push uses the built-in `GITHUB_TOKEN` (no extra secret).
