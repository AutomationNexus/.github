# AI workflow migration: OpenCode → Claude Code

> Status: **APPROVED — in progress.** This supersedes `docs/ai-files-migration-plan.md`
> (kept for history). Decisions below are final; this doc tracks per-repo rollout.

## Decisions (final)

| # | Question | Decision |
|---|----------|----------|
| 1 | Are `CLAUDE.md` / `.claude/` committed to `main`? | **No — dev-only.** Committed on `dev`, stripped from `main` by `.github/dev-only-paths` (same mechanism as `DEVELOPMENT.md`). `main` stays a lean public artifact. |
| 2 | Fate of OpenCode machinery (`tooling/opencode/`, `tools/bootstrap-opencode.*`, `opencode.json*`)? | **Deleted in the same PR that adds the Claude Code files** for that repo. No parallel-tool period, no archive copies — git history preserves everything. |
| 3 | `better-ccflare` (Claude/Anthropic proxy fork) | **Archived entirely**, not migrated. It is a standalone tool, not part of this org's dev workflow. See "better-ccflare" below. |
| 4 | Model tiering | Replace flat OpenCode model strings with **opus / sonnet / haiku** tiers per agent role, plus thinking-effort directives in the prompt body (Claude Code has no per-agent `effort:` field — see `docs/ai-model-tiers.md` if introduced later, or the table below). |

## Model tier mapping (org-wide default)

| Role | Old (OpenCode) | New (Claude Code) | Thinking directive |
|------|----------------|--------------------|---------------------|
| Architect / design agent | `openai/gpt-5.5` (variant: high) | `opus` | "think harder" in prompt |
| Security auditor (new) | — | `opus` | "think hard" in prompt |
| Reviewer | `openai/gpt-5.5-pro` | `sonnet` | "think hard" in prompt |
| Domain engineer (implementation) | `anthropic/claude-sonnet-4-6` | `sonnet` | default |
| QA gatekeeper (mechanical: lint/test/report) | `openai/gpt-5.5` (variant: high) | `haiku` | none |
| Live inspector / read-only ops | — | `haiku` | none |
| `*-opus-solver` escalation agent | `anthropic/claude-opus-4-8` (variant: max) | **deleted** | use `/model opus` or `opusplan` in the main session instead of a dedicated agent |

Main-session default: `sonnet`. Use `opusplan` for planning-heavy sessions (opus plans,
sonnet executes) — this replaces the old `default_agent: plan` / `build` handoff.

## Per-repo layout after migration

```
<repo>/
  CLAUDE.md                    # dev-only (see decision 1)
  .claude/
    agents/*.md                # dev-only
    settings.json               # dev-only — permission denylist only, no secrets/models
    settings.local.json         # gitignored, never committed
  CLAUDE.local.md               # gitignored, never committed
```

Removed: `opencode.json`, `opencode.json.example`, `.opencode/`, `tooling/opencode/`,
`tools/bootstrap-opencode.cmd`, `tools/bootstrap-opencode.ps1`, `docs/runbooks/opencode-init.md`.

## Rollout status

| Repo | Status | Notes |
|------|--------|-------|
| `.github` (this repo) | ✅ baseline done | Org `CLAUDE.md`, this doc, `templates/_shared/CLAUDE.md.template`, gitignore/dev-only-paths cleanup |
| `CognitiveSystems` | ✅ pilot done | First full convert-and-retire; validated against the checklist below |
| `ModelDeck` | pending | Apply proven CognitiveSystems mapping |
| `MediaRefinery` | pending | Apply proven CognitiveSystems mapping |
| `Uploadarr` | pending | Apply proven CognitiveSystems mapping |
| `HomeAssistant` | pending | Apply proven CognitiveSystems mapping; note `ha-live-inspector` → haiku |
| `ARCRunner` | pending | **Main-only repo** — no `dev` branch exists, so decision 1's dev-only mechanism doesn't apply cleanly. Needs an explicit call: commit `CLAUDE.md`/`.claude/` on `main` as an exception, or keep them local-only (gitignored) for this repo only. Flag for user decision in that repo's PR. |
| `template-python-docker` / `-pypi` / `-docker-ha-addon` / `-infra-main-only` / `-ha-config` | pending | Regenerated from `templates/_shared/` + group bundles via `scripts/sync-templates.sh` after this repo's templates are updated |
| `better-ccflare` | archived | Not migrated. Fork of `snipeship/ccflare`, a Claude API load-balancer proxy — out of scope for this org's dev-tooling migration. See below. |

## better-ccflare — archival notes

`better-ccflare` is a standalone open-source project (a Claude/Anthropic account
load-balancer), not an internal dev tool, so it is **archived rather than migrated**:

1. Settle any open PRs/issues you care about preserving.
2. Add a short archival notice to `README.md` (fork status, pointer to upstream
   `snipeship/ccflare` or wherever you want users redirected).
3. Archive the GitHub repo: `gh repo archive tombii/better-ccflare` (or via repo settings).
4. **Machine cleanup** (not a repo change): make sure no local environment still points
   `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` at a better-ccflare instance, and stop/remove
   any running instance (systemd unit, Docker container). Claude Code should talk to
   Anthropic directly with your own account — no proxy in the standard workflow.

## Validation checklist (per repo, before marking rollout done)

- [ ] `CLAUDE.md` present on `dev`, absent from a fresh `main` checkout
      (`git show origin/main:CLAUDE.md` → error; `git show origin/dev:CLAUDE.md` → prints file)
- [ ] `.claude/agents/*.md` load correctly (open Claude Code in the repo, `/agents` lists them)
- [ ] Any slash commands under `.claude/commands/` work
- [ ] `rg -i "opencode|cursor-acp|gpt-5\.5"` returns nothing in tracked files
- [ ] No secrets committed (`.claude/settings.json` has no tokens/URLs, only permission rules)
- [ ] `opencode.json`, `.opencode/`, `tooling/opencode/`, `tools/bootstrap-opencode.*` deleted
      from the repo (git history preserves them if ever needed)
- [ ] `.gitignore` updated: `CLAUDE.md`/`.claude/` no longer force-ignored (must be committable
      on `dev`); `CLAUDE.local.md` + `.claude/settings.local.json` ARE ignored
- [ ] README's AI-tooling section (if any) reflects Claude Code, not OpenCode
- [ ] Existing lint/test/build commands still pass unchanged (this migration never touches
      application code)
