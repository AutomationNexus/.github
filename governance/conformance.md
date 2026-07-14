# Conformance record

Full per-repo AI-governance conformance audit, plan Section 14. Produced by
reading every repo's local sibling clone (`../../<repo>` from this file)
against `registry.yml`, plus the canonical `templates/` and
`templates/_shared/` bundles for the 5 template repos. Read-only audit --
no files were changed in any *other* repo to produce this record; only
`registry.yml`, `workspace/CLAUDE.md`, and this file were edited, in this
repo, on a feature branch.

Audit date: 2026-07-14. Re-run before trusting this record if significant
time has passed -- see each repo's own `CLAUDE.md`/`.claude/` as the live
source of truth; this file is a snapshot, not a generator.

## Status legend

- **conformant** -- expected vs. actual agents/commands/routing match the
  registry with no gaps.
- **defect** -- a real, actionable gap (broken reference, missing file,
  stale doc making a false claim).
- **exception (confirmed)** -- a registered, intentional deviation from the
  full/default policy; re-verified live and still coherent.
- **needs-sync-decision** -- canonical and live have diverged in a way that
  requires a specific propagation action (not a design defect).

## Summary table

| Repo | Class | Team policy | Status | Notes |
|---|---|---|---|---|
| `.github` | meta | meta-core | conformant | Full roster (architect, workflow-engineer, reviewer, security-auditor, qa-gatekeeper) present; this audit's own subject. |
| `CognitiveSystems` | full | full-core | conformant | `/pr` routing defect (PR #56) confirmed fixed live. |
| `MediaRefinery` | full | full-core | conformant | `domain_agents` registry correction confirmed live. Org-team CODEOWNERS active on `dev` (PR #35) and `main` (2026-07-14 promote). |
| `ModelDeck` | full | full-core | exception (confirmed) | `main` default branch is a documented, re-verified exception. Architect routing + settings.json denies confirmed fixed live. |
| `Uploadarr` | full | full-core | conformant | `domain_agents` registry correction confirmed live. |
| `HomeAssistant` | config-only | full-core | conformant | Full 8-role roster + `dry-run-deploy` orchestration entry confirmed live, exact match. |
| `ARCRunner` | minimal | minimal | exception (confirmed) | Deliberately `qa-gatekeeper`-only; internally consistent with registry and its own `CLAUDE.md`. |
| `template-python-docker` | template (A) | full-core | conformant | Synced live 2026-07-14 (`scripts/sync-templates.sh`, commit `abcc436`). `team_policy` promoted stub -> full-core. |
| `template-python-pypi` | template (B) | full-core | conformant | Synced live 2026-07-14 (commit `26d8524`). Same promotion. |
| `template-docker-ha-addon` | template (C) | full-core | conformant | Synced live 2026-07-14 (commit `513853a`). Same promotion. `pyproject.toml` presence is correct/expected, unrelated to the sync. |
| `template-infra-main-only` | template (D) | stub | conformant | Was already correctly synced since 2026-07-11 (commit `d225ea2`); this file's and `registry.yml`'s prior "missing `execute.md`" claims were false, produced by auditing a stale unfetched local clone. Re-verified against `origin/main` directly. `team_policy` correctly stays `stub` -- group D deliberately excludes the `_shared` core. |
| `template-ha-config` | template (E) | full-core | conformant | Synced live 2026-07-14 (commit `441b80c`). Same promotion. `secrets.yaml`-aware settings.json overlay was already correct, unrelated to the sync. |

No repo's AI-governance Markdown is classified `permission-limited` in this
pass -- every check here was a local file read, not a live GitHub API call
requiring elevated scope. (Live GitHub state -- teams, rulesets, security
settings -- is tracked separately; see "Still open" in `organogram.md`.)

## `.github` (meta)

- Core roster: `architect`, `workflow-engineer`, `reviewer`, `security-auditor`, `qa-gatekeeper` all present in `.claude/agents/`, matching `CLAUDE.md`'s "Meta-repo AI team" table.
- Commands: `/qa` (this session added the `test_governance_scenarios.py` conditional run to both `.claude/agents/qa-gatekeeper.md` and `.claude/commands/qa.md`).
- Governance package itself (`governance/registry.yml`, `schema.json`, `README.md`, `organogram.md`, `scripts/validate-governance.py`, `tests/test_governance_scenarios.py`) is the audit's own subject and is internally self-consistent (`python scripts/validate-governance.py` and `python -m unittest tests/test_governance_scenarios.py` both pass as of the last commit on this branch).
- Status: **conformant**.

## CognitiveSystems

- Core roster + domain agents (`service-engineer`, `frontend-engineer`) present, 1:1 match against `CLAUDE.md`'s Subagents table.
- Commands: `execute`, `prepush`, `qa`, `release`, `service` -- all 5 referenced in `CLAUDE.md`, all resolve. Zero `/pr` references remain (PR #56 fix confirmed live).
- No read-only-role tool violations. `.claude/settings.json` carries both `dev`/`main` push denies.
- Non-blocking cleanup item (not a governance defect): a stale git worktree at `CognitiveSystems/.claude/worktrees/agent-a1438d33e65b573e7/CLAUDE.md` still contains the pre-fix `/pr` text -- leftover from a 2026-07-12 session, predates the fix, doesn't affect the live root `CLAUDE.md`. Left untouched per the collision protocol (not this session's work to clean up).
- Status: **conformant**.

## MediaRefinery

- Core roster + domain agents (`backend-engineer`, `frontend-engineer`) present, matching the registry's 2026-07-14 correction (previously recorded as `[]`).
- Commands: `execute`, `frontend`, `prepush`, `qa`, `release` -- all resolve. Minor routing asymmetry (frontend-engineer has a dedicated `/frontend` dispatch command, backend-engineer does not) is noted but not a defect -- no broken reference results from it.
- `.github/CODEOWNERS` carries active org-team ownership (superseding the prior fully-commented-out placeholder this record previously called "inert") -- merged to `dev` via PR #35, and to `main` via the 2026-07-14 patch-bump promote.
- Status: **conformant**.

## ModelDeck

- Core roster + domain agents (`mqtt-engineer`, `addon-engineer`) + `extra_qa_gates: [addon-qa-gatekeeper]` present, 1:1 match. `architect` confirmed present in the routing table (PR #107 fix live).
- 8 commands split cleanly across the Python/MQTT side (`execute`, `prepush`, `qa`, `release`) and the HA add-on side (`addon-execute`, `addon-prepush`, `addon-qa`, `sync-schema`) -- no broken references.
- `.claude/settings.json` confirmed carrying both required denies verbatim: `"Bash(git push origin dev:*)"` and `"Bash(git push origin main:*)"`.
- Default branch `main` (not `dev`) reconfirmed live -- this is the registered exception (HA add-on store + `schedule:`-trigger rationale); not re-flagged.
- Status: **exception (confirmed)**.

## Uploadarr

- Core roster + domain agents (`tracker-engineer`, `frontend-engineer`) present, matching the registry's 2026-07-14 correction.
- Commands: `execute`, `prepush`, `qa`, `release`, `tracker` -- all resolve.
- An active worktree (`Uploadarr/.claude/worktrees/ua-release-checklist-fix`) exists for unrelated in-progress work -- out of this audit's scope, untracked, not touched.
- Status: **conformant**.

## HomeAssistant

- Full core roster + `domain_agents: [yaml-engineer, live-inspector, drift-sync, release-operator]` present, 8 agents on disk exactly matching the 8-row Subagents table.
- `extra_orchestration: [dry-run-deploy]` confirmed to resolve to `.claude/commands/deploy-dry-run.md`, which dispatches `release-operator` -- exactly the registered, non-agent-file orchestration entry the registry documents.
- 8 commands (`execute`, `qa`, `prepush`, `pr`, `push-qa`, `deploy-dry-run`, `release`, `sync`), all resolve, all internal agent references resolve.
- No `pyproject.toml` (correct -- config-only repo, not a versioned package).
- Status: **conformant**. (Registry's `state: needs-verification` for this repo can be considered satisfied by this pass; flipping the field itself is a registry-maintenance step, not done here to avoid conflating an audit finding with an editorial registry change outside this file's scope.)

## ARCRunner

- Minimal team (`qa-gatekeeper` only) matches `team_policy: minimal` and the registered `state: exception` exactly. `domain_agents: []` confirmed -- no domain agent files on disk.
- 3 commands (`execute`, `prepush`, `qa`), all scoped to `Dockerfile.runner` + `build-runner-image.yml`, all resolve.
- `CLAUDE.md`'s own text and `registry.yml`'s exception rationale agree with each other and with what's on disk -- the exception is coherent on both sides, not just declared on one.
- Status: **exception (confirmed)**.

## Template repos (A/B/C/D/E) -- sync drift, resolved 2026-07-14

An earlier pass of this audit found all 5 live `template-*` repos' last
sync commit predating `.github` commit `39558a0` ("feat: add org-tier and
standardized repo agent teams", merged 2026-07-11T23:48:54+02:00), which:

- added `architect.md`, `qa-gatekeeper.md`, `reviewer.md`, `security-auditor.md`
  to `templates/_shared/.claude/agents/`, and `execute.md`, `release.md` to
  `templates/_shared/.claude/commands/` -- composed by `sync-templates.sh`
  into every group **except D** (D intentionally skips the `_shared` copy,
  mirroring the ARCRunner minimal-team exception);
- added a **group-D-specific** `execute.md` directly to
  `templates/D-infra-main-only/.claude/commands/`.

**Resolution:** the repo owner explicitly confirmed running
`scripts/sync-templates.sh` (all 5 groups) on 2026-07-14. Result:

| Repo | Result | Commit |
|---|---|---|
| `template-python-docker` (A) | pushed sync commit | `abcc436` |
| `template-python-pypi` (B) | pushed sync commit | `26d8524` |
| `template-docker-ha-addon` (C) | pushed sync commit | `513853a` |
| `template-infra-main-only` (D) | **already in sync** | `d225ea2` (2026-07-11) |
| `template-ha-config` (E) | pushed sync commit | `441b80c` |

**Group D correction (important):** this audit's *earlier* finding that
group D was "missing `execute.md`" was **false**, and so was the
`registry.yml` "CORRECTED" note that repeated it. Both were produced by
reading this repo's *local* clone in the workspace root without fetching
first -- that local clone's `main` was 1 commit behind `origin/main`. The
live repo had actually been correctly synced since 2026-07-11T23:52:28+02:00
(commit `d225ea2`, ~4 minutes after `39558a0` landed), most likely by a
concurrent session's own sync run. This is a direct instance of the "never
trust a stale local view" warning in `workspace/CLAUDE.md`'s
concurrent-agent protocol -- re-verified this time by fetching
`origin/main` directly (`git -C template-infra-main-only fetch origin main`)
before drawing any conclusion, and all 5 local template-repo clones were
fast-forwarded to `origin/main` to prevent the same mistake going forward.

Each of A/B/C/E's `CLAUDE.md` Subagents/Slash-commands sections, previously
flagged as describing the pre-`39558a0` stub (including stale
"opus/sonnet/opus... once the repo has real scope beyond the stub" prose),
were overwritten by the sync along with the agent/command files themselves
-- resolved as a side effect, not a separate prose edit.

Registry-level corrections made (2026-07-14, this branch):

- Groups A/B/C/E: `state` -> `active`, `team_policy` `stub` -> `full-core`
  (their canonical is now the full shared core, not a bare
  `qa-gatekeeper`), and each group's now-obsolete "starter repo, full team
  unjustified" `exception:` block removed.
- Group D: `state` -> `active`; `team_policy` correctly remains `stub` (its
  exclusion from the `_shared` core is permanent policy, not a staged
  drift state); its `registry.yml` note now documents the correction chain
  above instead of repeating the false claim.
- Root `workspace/CLAUDE.md`'s "only the first two [groups] carry
  `pyproject.toml`/`bump-type`" line was imprecise -- group C also carries
  a `pyproject.toml` (build/test tooling), just not `bump-type` scope.
  Corrected to state the two facts separately (unrelated to the sync
  itself, found during the same pass).

### Why the stale model-tier prose in template `CLAUDE.md`s wasn't caught by organogram.md item #7 (historical)

Organogram.md's "Resolved" item #7 (this session, earlier) swept prose
locations for stale `opus/sonnet/opus`-tier claims and found none -- that
sweep covered `docs/ai-migration.md`, root/template `CLAUDE.md`/`README.md`
*canonical* files, `organogram.md`, and `workspace/CLAUDE.md`. It did not
re-derive live-repo drift, because at the time nothing had flagged the
live template repos as unsynced -- that finding only surfaced from this
conformance audit's direct live-vs-canonical file comparison. The stale
"opus/sonnet/opus... beyond the stub" phrasing that remained in the 4 live
template repos' `CLAUDE.md`s (A/B/C/E) was a symptom of the same sync gap
documented above -- it was resolved by the `scripts/sync-templates.sh` run
of 2026-07-14 (see "Template repos ... resolved" above), not by a separate
prose edit.

## CODEOWNERS `main`-branch consistency, resolved 2026-07-14

At the time of the original audit above, org-team CODEOWNERS was live on
every app repo's `dev` branch but had drifted independently on `main`
(CognitiveSystems/HomeAssistant: stale `* @t-abraham`; MediaRefinery:
commented-out placeholder -- the "inert" note corrected above; Uploadarr/
ModelDeck: missing entirely). All 5 app repos (CognitiveSystems,
MediaRefinery, Uploadarr, HomeAssistant, ModelDeck) now carry identical
org-team CODEOWNERS content on `main`, landed via real `bump-type: patch`
`promote-dev-to-main.yml` dispatches after a direct CODEOWNERS-only PR into
`main` proved structurally blocked by `ci.yml`'s `guard-main-source` check.
`git show origin/main:.github/CODEOWNERS` for each repo matches that repo's
`origin/dev` copy. See `organogram.md`'s "Resolved" item #12 for the full
account.
