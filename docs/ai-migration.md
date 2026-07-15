# AI workflow migration to Claude Code

> Status: **COMPLETE.** Decisions below are final; this doc records the rollout.
>
> This doc is a historical decision/rollout record. For the current, maintained
> org/repo agent roster, human GitHub teams, ownership, and exceptions, treat
> [`governance/registry.yml`](../governance/registry.yml) as authoritative —
> see [`governance/README.md`](../governance/README.md) and
> [`governance/organogram.md`](../governance/organogram.md). Where this doc's
> "Agent organization" or "Model tier mapping" sections ever disagree with the
> registry, the registry wins; this doc is not updated per-agent-change.

## Decisions (final)

| # | Question | Decision |
|---|----------|----------|
| 1 | Are `CLAUDE.md` / `.claude/` committed to `main`? | **No — dev-only.** Committed on `dev`, stripped from `main` by `.github/dev-only-paths` (same mechanism as `DEVELOPMENT.md`). `main` stays a lean public artifact. |
| 2 | Fate of retired AI-tooling machinery? | **Deleted in the same PR that adds the Claude Code files** for that repo. No parallel-tool period, no archive copies — git history preserves everything. |
| 3 | Model tiering | **Current standard:** leads (`architect`, `security-auditor`, org leads) use `sonnet` + `effort: high`; implementation/review uses `sonnet`; mechanical QA/inspection uses `haiku`. Deep escalation stays in the main session (`/model opus` or `opusplan`), not a dedicated agent. |

## Model tier mapping (org-wide default)

| Role | Claude Code tier | Effort / directive |
|------|------------------|--------------------|
| Architect / design agent | `sonnet` | `effort: high`; "think harder" |
| Security auditor / org security officer | `sonnet` | `effort: high`; "think hard" |
| Org release manager / chief architect | `sonnet` | `effort: high` |
| Reviewer | `sonnet` | "think hard" |
| Domain engineer (implementation) | `sonnet` | default |
| QA gatekeeper (mechanical: lint/test/report) | `haiku` | default |
| Live inspector / org inspector (read-only ops) | `haiku` | default |
| Deep escalation | `opus` | use `/model opus` or `opusplan` in the main session instead of a dedicated agent |

Main-session model is operator-selected. Use `opusplan` for planning-heavy sessions when
available; repo agents stay on the tiers above for consistency and predictable cost.

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

Removed: retired AI-tooling config, bootstrap scripts, and generated runtime folders.

## Agent organization (current standard)

The original migration established repo-tier teams. The org now adds a second tier:

- **Workspace-root session = CTO desk:** 6 org agents + 7 org commands, canonically
  versioned in this repo's `workspace/` and copied locally by
  `scripts/sync-workspace.sh`.
- **Repo session = department:** 4 shared-core roles (`architect`, `qa-gatekeeper`,
  `reviewer`, `security-auditor`) plus the repo's domain experts/commands. Canonical
  shared skeletons live in `templates/_shared/.claude/`; per-repo content below
  `<!-- repo-specific -->` remains local and is preserved by
  `scripts/sync-shared-claude.sh`.
- ARCRunner/group D remain deliberately minimal (`qa-gatekeeper` only) because their
  one-Dockerfile/one-workflow surface does not justify a full team.

`CLAUDE.md` cascades from the workspace root into repo sessions; `.claude/agents` and
`.claude/commands` do not. Therefore org→repo handoff is a written `/dispatch` brief,
not a nested subagent spawn.

## Rollout status

| Repo | Status | Notes |
|------|--------|-------|
| `.github` (this repo) | ✅ merged | [PR #12](https://github.com/AutomationNexus/.github/pull/12). Org `CLAUDE.md`, this doc, per-group `CLAUDE.md`/`.claude/` for all 5 templates, gitignore/dev-only-paths cleanup |
| `CognitiveSystems` | ✅ merged | [PR #27](https://github.com/AutomationNexus/CognitiveSystems/pull/27). Pilot. 5 agents + 1 new (`security-auditor`), 5 commands, `.claude/settings.json`, full retire |
| `ModelDeck` | ✅ merged | [PR #81](https://github.com/AutomationNexus/ModelDeck/pull/81). Dual-domain (Python service + HA add-on): 6 agents, 8 commands |
| `MediaRefinery` | ✅ merged | [PR #23](https://github.com/AutomationNexus/MediaRefinery/pull/23). 6 agents, 5 commands. **Found and fixed a real bug**: an unanchored `agents/` rule in `.gitignore` was silently swallowing `.claude/agents/` — anchored to `/agents/` |
| `Uploadarr` | ✅ merged | [PR #36](https://github.com/AutomationNexus/Uploadarr/pull/36). 6 agents, 5 commands |
| `HomeAssistant` | ✅ merged | [PR #43](https://github.com/AutomationNexus/HomeAssistant/pull/43). Most complex: 8 agents, 8 commands, full permission denylist. **Found and fixed a real CI-breaking bug**: `tools/check_repo_hygiene.py` hard-failed if `CLAUDE.md`/`.claude/` were tracked at all — fixed and verified |
| `ARCRunner` | ✅ merged | [PR #10](https://github.com/AutomationNexus/ARCRunner/pull/10). **Main-only exception applied**: `CLAUDE.md`/`.claude/` committed directly on `main`. Minimal surface — only `qa-gatekeeper` (haiku) |
| `template-python-docker` / `-pypi` / `-docker-ha-addon` / `-infra-main-only` / `-ha-config` | ✅ done | Regenerated via `scripts/sync-templates.sh` (run with Git Bash — WSL's `bash` on PATH doesn't have `gh`) and pushed directly to `main` on all 5 `AutomationNexus/template-*` repos. Stale retired AI-tool files (not deleted by the sync script, a documented limitation) manually removed from all 5 via a separate clone+push. Verified: each repo's `main` has no retired AI-tool paths and has `CLAUDE.md`. |

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
- [ ] `rg -i "cursor-acp|gpt-5\.5"` returns nothing in tracked files
- [ ] No secrets committed (`.claude/settings.json` has no tokens/URLs, only permission rules)
- [ ] Retired AI-tooling config, runtime folders, and bootstrap scripts deleted
      from the repo (git history preserves them if ever needed)
- [ ] `.gitignore` updated: `CLAUDE.md`/`.claude/` no longer force-ignored (must be committable
      on `dev`); `CLAUDE.local.md` + `.claude/settings.local.json` ARE ignored
- [ ] README's AI-tooling section (if any) reflects Claude Code
- [ ] Existing lint/test/build commands still pass unchanged (this migration never touches
      application code)
