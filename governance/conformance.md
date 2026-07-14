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
| `MediaRefinery` | full | full-core | conformant | `domain_agents` registry correction confirmed live. CODEOWNERS present but inert (fully commented out). |
| `ModelDeck` | full | full-core | exception (confirmed) | `main` default branch is a documented, re-verified exception. Architect routing + settings.json denies confirmed fixed live. |
| `Uploadarr` | full | full-core | conformant | `domain_agents` registry correction confirmed live. |
| `HomeAssistant` | config-only | full-core | conformant | Full 8-role roster + `dry-run-deploy` orchestration entry confirmed live, exact match. |
| `ARCRunner` | minimal | minimal | exception (confirmed) | Deliberately `qa-gatekeeper`-only; internally consistent with registry and its own `CLAUDE.md`. |
| `template-python-docker` | template (A) | stub | needs-sync-decision | Live missing architect/reviewer/security-auditor + execute/release commands added to canonical 2026-07-11 (commit `39558a0`). |
| `template-python-pypi` | template (B) | stub | needs-sync-decision | Same gap as group A. |
| `template-docker-ha-addon` | template (C) | stub | needs-sync-decision | Same gap as group A. `pyproject.toml` presence is correct/expected, not drift. |
| `template-infra-main-only` | template (D) | stub | defect (corrected) | Registry previously claimed "no drift, re-verified" -- false. Live is missing `execute.md`, added to canonical D bundle in the same commit. Registry note corrected 2026-07-14. |
| `template-ha-config` | template (E) | stub | needs-sync-decision | Same gap as group A. `secrets.yaml`-aware settings.json overlay is correct/expected, not drift. |

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
- `.github/CODEOWNERS` confirmed still fully commented out (no active owner line) -- registered as inert per plan Section 5's "temporary individual fallback" allowance, not yet actioned.
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

## Template repos (A/B/C/D/E) -- confirmed sync drift

All 5 live `template-*` repos' last sync commit predates `.github` commit
`39558a0` ("feat: add org-tier and standardized repo agent teams", merged
2026-07-11T23:48:54+02:00), which:

- added `architect.md`, `qa-gatekeeper.md`, `reviewer.md`, `security-auditor.md`
  to `templates/_shared/.claude/agents/`, and `execute.md`, `release.md` to
  `templates/_shared/.claude/commands/` -- composed by `sync-templates.sh`
  into every group **except D** (D intentionally skips the `_shared` copy,
  mirroring the ARCRunner minimal-team exception);
- added a **group-D-specific** `execute.md` directly to
  `templates/D-infra-main-only/.claude/commands/`.

None of this has reached the live repos yet:

| Repo | Live last sync | Missing vs. canonical |
|---|---|---|
| `template-python-docker` (A) | 2026-07-09T20:00:07+02:00 | `architect.md`, `reviewer.md`, `security-auditor.md`, `execute.md`, `release.md` |
| `template-python-pypi` (B) | 2026-07-09T20:00:11+02:00 | same 5 files |
| `template-docker-ha-addon` (C) | 2026-07-09T20:00:15+02:00 | same 5 files |
| `template-infra-main-only` (D) | 2026-07-09T20:00:22+02:00 | `execute.md` only |
| `template-ha-config` (E) | 2026-07-09T20:00:18+02:00 | same 5 files as A/B/C |

Each live repo's existing `qa-gatekeeper` + `qa`/`prepush` files are
byte-identical to their canonical counterparts -- the drift is purely
**missing** files/content, not divergent content. Each repo's `CLAUDE.md`
Subagents/Slash-commands sections are correspondingly behind (still
describing the pre-`39558a0` stub, including one stale "opus/sonnet/opus...
once the repo has real scope beyond the stub" line per group -- this is
the one place stale model-tier prose *does* still exist; see the note
below on why organogram.md's item #7 didn't catch it).

Registry-level corrections already made (2026-07-14, this branch):

- `template-infra-main-only`'s registry note previously claimed "re-verified
  live 2026-07-14, matches canonical exactly, no drift" -- **this was false**
  (evidently checked against a pre-`39558a0` canonical snapshot). Corrected
  in `registry.yml`.
- All 5 template repos' `registry.yml` entries now carry a `notes:` field
  documenting the confirmed drift and that each `review_trigger` ("canonical
  gains commands/agents beyond the stub") has already fired as of
  `39558a0`.
- Root `workspace/CLAUDE.md`'s "only the first two [groups] carry
  `pyproject.toml`/`bump-type`" line was imprecise -- group C also carries
  a `pyproject.toml` (build/test tooling), just not `bump-type` scope.
  Corrected to state the two facts separately.

**Not done here, and must not be done without explicit human confirmation
naming the exact script/repos/options in that turn:** running
`scripts/sync-templates.sh` to actually close the gap. This is the
pre-existing, permanent, human-confirmed direct-push exception
(`exceptions: sync-templates-direct-push` in `registry.yml`) -- it applies
here unchanged. See `organogram.md`'s "Still open" and the confirmation
checklist this audit feeds into.

Once synced, a follow-up governance edit should reconsider whether
`team_policy: stub` still accurately describes groups A/B/C/E (their
canonical is now the full shared core, not a bare `qa-gatekeeper`) --
flagged in each repo's `registry.yml` notes rather than resolved here,
since it's a policy classification change that should land alongside the
sync itself, not ahead of it.

### Why the stale model-tier prose in template `CLAUDE.md`s wasn't caught by organogram.md item #7

Organogram.md's "Resolved" item #7 (this session, earlier) swept prose
locations for stale `opus/sonnet/opus`-tier claims and found none -- that
sweep covered `docs/ai-migration.md`, root/template `CLAUDE.md`/`README.md`
*canonical* files, `organogram.md`, and `workspace/CLAUDE.md`. It did not
re-derive live-repo drift, because at the time nothing had flagged the
live template repos as unsynced -- that finding only surfaced from this
conformance audit's direct live-vs-canonical file comparison. The stale
"opus/sonnet/opus... beyond the stub" phrasing that remains in the 4 live
template repos' `CLAUDE.md`s (A/B/C/E) is a symptom of the same sync gap
documented above, not a separate prose defect -- it will be resolved by
the same `scripts/sync-templates.sh` run, not by a separate prose edit.
