# AI workflow migration to Claude Code

> Status: **COMPLETE.** Decisions below are final; this doc records the rollout.

## Decisions (final)

| # | Question | Decision |
|---|----------|----------|
| 1 | Are `CLAUDE.md` / `.claude/` committed to `main`? | **No — dev-only.** Committed on `dev`, stripped from `main` by `.github/dev-only-paths` (same mechanism as `DEVELOPMENT.md`). `main` stays a lean public artifact. |
| 2 | Fate of retired AI-tooling machinery? | **Deleted in the same PR that adds the Claude Code files** for that repo. No parallel-tool period, no archive copies — git history preserves everything. |
| 3 | `better-ccflare` (Claude/Anthropic proxy fork) | **Archived entirely**, not migrated. It is a standalone tool, not part of this org's dev workflow. See "better-ccflare" below. |
| 4 | Model tiering | Use **opus / sonnet / haiku** tiers per agent role, plus thinking-effort directives in the prompt body (Claude Code has no per-agent `effort:` field — see `docs/ai-model-tiers.md` if introduced later, or the table below). |

## Model tier mapping (org-wide default)

| Role | Claude Code tier | Thinking directive |
|------|------------------|--------------------|
| Architect / design agent | `opus` | "think harder" in prompt |
| Security auditor | `opus` | "think hard" in prompt |
| Reviewer | `sonnet` | "think hard" in prompt |
| Domain engineer (implementation) | `sonnet` | default |
| QA gatekeeper (mechanical: lint/test/report) | `haiku` | none |
| Live inspector / read-only ops | `haiku` | none |
| Deep escalation | `opus` | use `/model opus` or `opusplan` in the main session instead of a dedicated agent |

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

Removed: retired AI-tooling config, bootstrap scripts, and generated runtime folders.

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
| `better-ccflare` | ⚠️ blocked | Not migrated by design (out of scope). **Archival could not be completed**: the repo `tombii/better-ccflare` is owned by a different GitHub account than the one authenticated for this migration (`t-abraham`, read-only access — `pull: true, push: false, admin: false`). Archiving or editing the README requires the repo owner's own action. |

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

**Status: steps 1–3 not executed** — the authenticated `gh` account for this migration
(`t-abraham`) has only read access to `tombii/better-ccflare` (not admin/push), so it
cannot archive the repo or push a README change. This needs to be done by whoever has
admin rights on that repo (log in as `tombii`, or ask them to run the archive step).
Step 4 was checked on this machine: no `better-ccflare` process, listening port
(8080/8081/8082/8889), Windows service, or `ANTHROPIC_BASE_URL`/`ANTHROPIC_AUTH_TOKEN`
env var was found — nothing to decommission locally.

## Local app uninstall — explicitly deferred

The operator asked to **not** uninstall the local legacy app/package/config during this pass.
All of it remains installed and untouched on this machine. If it is uninstalled later,
also revoke any related OAuth grant from the Anthropic account security page if full
deprovisioning is ever wanted.

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
