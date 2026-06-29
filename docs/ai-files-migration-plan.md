# Plan: migrate AI instruction files to the standard (committed) convention

> Status: PROPOSAL — no repo changes made yet. Review, then approve per-repo rollout.

## Why

Anthropic's Claude Code docs treat **shared AI instructions as version-controlled team files**:

- `CLAUDE.md`, `.claude/rules/*.md`, `AGENTS.md` → **committed** ("shared with your team through version control").
- Only personal/secret files → gitignored: `CLAUDE.local.md` (sandbox URLs, personal test data).
- Auto-memory lives outside the repo (`~/.claude/projects/<project>/memory/`) and is never committed.

Our repos currently do the opposite: they **gitignore** `CLAUDE.md`/`AGENTS.md`/`opencode.json`/`.opencode/`
and ship `tooling/opencode/*` + `tools/bootstrap-opencode.*` that copy templates into the gitignored
live files. That works but is non-standard, adds a bootstrap step, and means the canonical instructions
are not visible/reviewable in the repo.

## Target layout (per repo)

| File | State | Rationale |
|------|-------|-----------|
| `CLAUDE.md` (or `AGENTS.md` + `CLAUDE.md` that imports it) | **committed** | Team-shared project instructions |
| `.claude/rules/*.md` | **committed** | Path-scoped shared rules |
| `opencode.json` | **committed** if it holds no secrets; else commit `opencode.json.example` and gitignore the live one | OpenCode project config |
| `CLAUDE.local.md` | **gitignored** | Personal per-project notes |
| `.opencode/` runtime, auto-memory | **gitignored** | Machine-local state |
| `tooling/opencode/*` | keep as-is OR fold into the committed files | Currently the source of truth; becomes redundant once canonical files are committed |

## Migration steps (per repo, via PR to dev)

1. Decide the canonical file: `CLAUDE.md` (recommended) or `AGENTS.md` + a one-line `CLAUDE.md` that does `@AGENTS.md`.
2. Generate it from the existing `tooling/opencode/*` content (project-rules → CLAUDE.md; agents/commands → `.claude/`), or run `/init`.
3. Remove `CLAUDE.md`, `AGENTS.md`, `opencode.json` (if secret-free) from `.gitignore`; keep `CLAUDE.local.md`, `.opencode/`, auto-memory ignored.
4. Update `.github/dev-only-paths`: stop blocking the now-committed files; keep blocking `CLAUDE.local.md` and any secret-bearing files. (If you still want these dev-only and never on `main`, that is a separate choice — see note.)
5. Decide the fate of `tools/bootstrap-opencode.*` + `tooling/opencode/*`: keep for OpenCode-specific seeding, or delete if fully replaced by committed `CLAUDE.md`/`.claude/`.
6. Open PR to dev, let CI run, merge, then promote.

## Important nuance: dev-only vs committed-to-main

Our `dev-only-paths` currently keeps AI files **off `main`** entirely. The standard convention commits
them everywhere (including main). Two consistent options:

- **Option 1 (standard):** commit AI instructions to both dev and main. Simplest, matches docs. Drop the AI entries from `dev-only-paths`.
- **Option 2 (dev-only):** commit them but keep them dev-only via `dev-only-paths` so `main` stays lean. Non-standard but matches your current "main is clean" preference.

Pick one before rollout.

## Rollout order (suggested)

1. Pilot: CognitiveSystems (most developed opencode tooling).
2. Verify CI + a release still pass.
3. Roll to ModelDeck, MediaRefinery, Uploadarr, ModelDeck-HAOS, HomeAssistant, ARCRunner.

## Decisions needed from you

1. Canonical file: `CLAUDE.md` only, or `AGENTS.md` + importing `CLAUDE.md`?
2. Commit AI files to main too (Option 1) or keep dev-only (Option 2)?
3. Keep `tooling/opencode/` + bootstrap, or retire it once canonical files are committed?
