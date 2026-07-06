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
| `CognitiveSystems` | ✅ done | Pilot. 5 agents + 1 new (`security-auditor`), 5 commands, `.claude/settings.json`, full retire |
| `ModelDeck` | ✅ done | Dual-domain (Python service + HA add-on): 6 agents (`mqtt-engineer`, `addon-engineer`, `qa-gatekeeper`, `addon-qa-gatekeeper`, `reviewer`, `security-auditor`), 8 commands |
| `MediaRefinery` | ✅ done | 6 agents, 5 commands. **Found and fixed a real bug**: an unanchored `agents/` rule in `.gitignore` was silently swallowing `.claude/agents/` — anchored to `/agents/` |
| `Uploadarr` | ✅ done | 6 agents, 5 commands. Pre-existing stray `$null` file in repo root left untouched (unrelated to this migration) |
| `HomeAssistant` | ✅ done | Most complex: 8 agents (incl. `drift-sync`, `live-inspector` on haiku), 8 commands, full permission denylist. **Found and fixed a real CI-breaking bug**: `tools/check_repo_hygiene.py` hard-failed if `CLAUDE.md`/`.claude/` were tracked at all (no branch-awareness) — removed them from its forbidden lists since they're now intentionally committed on `dev`. This repo's `.gitignore`/`dev-only-paths` also never had `CLAUDE.md`/`.claude/` entries at all (gap vs. other repos) — added to `dev-only-paths` only (not `.gitignore`, since they must be committable on `dev`) |
| `ARCRunner` | ✅ done | **Main-only exception applied**: no `dev` branch exists, so `CLAUDE.md`/`.claude/` are committed directly on `main` (documented in the file itself). Minimal surface (1 Dockerfile, 1 workflow, no secrets) — only `qa-gatekeeper` (haiku); no architect/reviewer/security-auditor, to avoid over-engineering |
| `template-python-docker` / `-pypi` / `-docker-ha-addon` / `-infra-main-only` / `-ha-config` | pending | Regenerated from `templates/_shared/` + group bundles via `scripts/sync-templates.sh` — **not run yet** (pushes to remote `AutomationNexus/template-*` repos; requires explicit approval to execute) |
| `better-ccflare` | pending archival | Not migrated by design. Fork of `snipeship/ccflare`, a Claude API load-balancer proxy — out of scope for this org's dev-tooling migration. Archival steps (README notice, `gh repo archive`, machine cleanup) not yet executed — see below. |

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

## Lessons learned during rollout (check these in every remaining repo)

1. **Gitignore collisions**: some repos have unrelated bare patterns like `agents/`
   (meant for a top-level local-only planning folder) that unintentionally also match
   `.claude/agents/` and silently gitignore every subagent file. Always run
   `git check-ignore -v .claude/agents/<any-file>` after adding agents, before committing.
2. **Bespoke hygiene/secret scripts**: at least one repo (`HomeAssistant`) had a custom
   `tools/check_repo_hygiene.py` that hard-failed CI if `CLAUDE.md`/`.claude/` were tracked
   at all, with no branch-awareness. Grep any repo-specific QA/hygiene script for
   `CLAUDE.md`, `.claude`, `AGENTS.md` before assuming the standard dev-only convention
   will pass CI — update the script's forbidden-list if needed and verify by actually
   running the script locally with the new files staged.
3. **`.env.*` wildcard vs. `.env.example`**: Claude Code's `permissions.deny` takes
   precedence over `allow`, so a broad `Read(**/.env.*)` deny will also block the intended
   `.env.example`. Check whether the repo actually has other real `.env.*` variants; if not,
   deny only the exact `.env` file instead of the wildcard.
4. **`git add -A` can stage unrelated pre-existing cruft** (e.g. a stray `$null` file) —
   review `git status --short` before committing and unstage anything not part of the
   migration.

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
