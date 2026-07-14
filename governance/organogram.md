# Organogram

Rendered view of `registry.yml`. If this file and the registry ever disagree,
the registry wins — re-run `python scripts/validate-governance.py` and
regenerate this file's tables by hand until a generator exists.

## Human governance (outside the AI rank chain)

These are the only entities holding real GitHub permissions.

| Team | Default repo permission | Purpose | State |
|---|---|---|---|
| `automationnexus-admins` | admin | Org ownership, billing, ruleset/security-setting changes, final escalation | desired |
| `automationnexus-platform` | maintain | Owns `.github` — reusable workflows, templates, scripts, rulesets, this registry | desired |
| `automationnexus-security` | triage | Security-sensitive paths org-wide — workflows, permissions, secrets hygiene, denylists | desired |
| `automationnexus-release` | write | Promote/release paths — dispatch triggers, release workflows, tag/version policy | desired |
| `automationnexus-app-maintainers` | write | Application/config source for the versioned app repos and HomeAssistant config | desired |

All five are `state: desired` — none has been confirmed to exist live yet.
See plan Section 6 (deferred to a separately-confirmed privileged rollout,
not this PR).

## AI rank chain

Every node below is a Claude Code role, not a GitHub identity — see
`README.md`'s "Humans vs. AI" section. `escalation_target` always terminates
at a human operator.

```
                                human operator
                                      |
                    -----------------------------------
                    |                                  |
             chief-architect                    security-officer
           (org-lead, read-only)             (org-lead, read-only)
                    |
      -----------------------------------------
      |               |                |               |
platform-engineer  release-manager  template-steward  org-inspector
 (org-lead,         (org-lead,        (org-lead,        (org-operational,
  repo-write)        cross-repo-write, repo-write)       read-only)
                      confirmation-
                      required)
      |
      v
 .github meta-repo team (architect, workflow-engineer, reviewer,
 security-auditor, qa-gatekeeper — full roster present)

Every full/config-only repo (independently, not a child of any org agent):
 architect -> {domain engineers} -> reviewer -> security-auditor -> qa-gatekeeper
 (repo-core team, read-only except domain engineers which are repo-write)
```

`platform-engineer`, `release-manager`, and `template-steward` all escalate to
`chief-architect`, except `template-steward` which escalates to
`platform-engineer` first (template propagation is a `.github` platform
concern before it's a cross-repo one). `org-inspector` escalates to
`chief-architect`. `chief-architect` and `security-officer` escalate directly
to the human operator — no AI node is their parent.

Repo-core teams are **not** children of any org agent in the runtime sense —
org agents cannot spawn repo-tier agents (subagents cannot spawn subagents,
and `.claude/` doesn't cascade). The link is a **handoff brief**, produced by
`/dispatch`, not a spawn. See `../workspace/CLAUDE.md` → "Handoff protocol".

## Repository × team-policy × sync-role matrix

| Repo | Class | Default branch | Team policy | Sync role | Owning team | State |
|---|---|---|---|---|---|---|
| `.github` | meta | `master` | meta-core | canonical-source | automationnexus-platform | active |
| `CognitiveSystems` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `MediaRefinery` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `ModelDeck` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `Uploadarr` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `HomeAssistant` | config-only | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `ARCRunner` | minimal | `main` | minimal | excluded | automationnexus-platform | exception |
| `template-python-docker` | template (A) | `main` | full-core | template-target | automationnexus-platform | active |
| `template-python-pypi` | template (B) | `main` | full-core | template-target | automationnexus-platform | active |
| `template-docker-ha-addon` | template (C) | `main` | full-core | template-target | automationnexus-platform | active |
| `template-infra-main-only` | template (D) | `main` | stub | template-target | automationnexus-platform | active |
| `template-ha-config` | template (E) | `main` | full-core | template-target | automationnexus-platform | active |

`needs-verification` here specifically means: default branch, team
composition, and ruleset application have not been re-checked live since this
registry was authored — not that anything is known to be wrong. `ARCRunner`
is the one row genuinely settled as `exception` (documented, reviewed, not
pending a check).

## Repo-core team (every `full-core`/`meta-core` repo)

| Role | Model | Decision rights | Mutation class |
|---|---|---|---|
| `architect` | sonnet (high effort) | Proposes boundaries/sequencing/validation needs; does not implement | read-only |
| `qa-gatekeeper` | haiku | Final release/PR evidence gate; pass/fail, not preference | read-only |
| `reviewer` | sonnet | Independent challenge function; no rewrites unless explicitly assigned | read-only |
| `security-auditor` | sonnet (high effort) | Independent challenge function; no rewrites unless explicitly assigned | read-only |

Repo-local additions (`domain_agents`, `extra_qa_gates`, `extra_orchestration`
in `registry.yml`) are registered orchestration profiles, not defects: e.g.
ModelDeck's `mqtt-engineer`/`addon-engineer` + `addon-qa-gatekeeper`,
HomeAssistant's `yaml-engineer`/`live-inspector`/`drift-sync`/`release-operator`
+ `dry-run-deploy` (the last of these names the `/deploy-dry-run` command, not
an agent file -- `extra_orchestration` entries are not required to resolve to
a `.claude/agents/*.md` file the way `domain_agents`/`extra_qa_gates` are).
`scripts/validate-governance.py` now checks every full-core/meta-core repo's
`domain_agents` + `extra_qa_gates` against what's actually on disk in that
repo's sibling clone (see "Resolved" #7 below).

## Task routing (org-tier)

| Task type | Route to | Command |
|---|---|---|
| Current org state / "is something broken?" | `org-inspector` | `/org-status` |
| Cross-repo design / multi-repo planning | `chief-architect` | `/dispatch` |
| `.github` platform work (workflows, templates, rulesets, scripts) | `platform-engineer` | direct session in `.github`, or `/dispatch` |
| Release / promote | `release-manager` | `/promote` (human-confirmed) |
| Org-wide security review | `security-officer` | `/org-audit` |
| Template ↔ app-repo shared-layer drift | `template-steward` | `/sync-templates` (human-confirmed) |
| Workspace root refresh | `platform-engineer` | `/sync-workspace` (human-confirmed) |
| New repo | `chief-architect` | `/new-repo` (human-confirmed) |

## Open items

### Resolved

1. **`.github` meta-repo team** — `architect` and `security-auditor` are
   present in `.claude/agents/` alongside `workflow-engineer`, `reviewer`,
   `qa-gatekeeper`. Full roster confirmed live 2026-07-14.
2. **CognitiveSystems** — `CLAUDE.md` routed to a nonexistent `/pr` command.
   Fixed: pipeline text repointed at the real `/prepush` command, and the
   ambiguous "first four agents" wording replaced with "four core roles".
   Landed as CognitiveSystems PR #56.
3. **ModelDeck routing table** — the `architect` agent existed locally but
   was missing from the visible subagent/routing table in
   `ModelDeck/CLAUDE.md`. Fixed: added to the routing table and the
   Subagents table. Landed as ModelDeck PR #107.
4. **ModelDeck default branch** — re-checked live 2026-07-14: `main`, which
   matches `ModelDeck/CLAUDE.md`'s own documented rationale (HA add-on store
   and `schedule:` triggers both read the default branch). Not drift —
   recorded as a registered exception in `registry.yml` (see the `ModelDeck`
   entry's `exception:` block) rather than something to change.
5. **ModelDeck `.claude/settings.json`** — re-checked live 2026-07-14:
   already carries both `Bash(git push origin dev:*)` and
   `Bash(git push origin main:*)` denies. Already fixed by the time this was
   re-verified — no further action needed.
6. **Template group D (`template-infra-main-only`)** — re-checked live
   2026-07-14: `.claude/commands/` (`execute`, `prepush`, `qa`) and
   `.claude/agents/` (`qa-gatekeeper`) match the canonical
   `templates/D-infra-main-only/` bundle exactly. No drift, no policy
   decision needed.
7. **Stale `opus/sonnet/opus`-style model-tier prose** — swept every prose
   location that names a model/effort tier for an agent role (`docs/ai-
   migration.md`, root and template `CLAUDE.md`/`README.md` files, this
   file, `workspace/CLAUDE.md`) against each agent's own frontmatter and
   `registry.yml`. No stale or mismatched text found anywhere in the
   *canonical* sources — `opus` only ever appears as a documented
   main-session escalation directive (`/model opus`/`opusplan`), never as a
   per-agent tier claim. (A related but distinct instance of stale prose
   *was* later found in 4 live, unsynced template repos — see item #8; it's
   a sync-drift symptom, not a separate canonical-prose defect.)
8. **Full 12-repo conformance audit** — every repo's local clone inspected
   against `registry.yml`: core roster, domain agents, command references,
   routing-table completeness, read-only-role tool grants, and
   `settings.json` branch-protection denies. Full record:
   [`conformance.md`](conformance.md). Result: 7 of 12 repos conformant or
   a confirmed exception (`.github`, CognitiveSystems, MediaRefinery,
   ModelDeck, Uploadarr, HomeAssistant, ARCRunner); the 5 template repos
   were found out of sync with a canonical change (commit `39558a0`,
   2026-07-11) that added the full shared core to groups A/B/C/E and a new
   `execute.md` to group D. `registry.yml` and `workspace/CLAUDE.md`
   (`pyproject.toml`/`bump-type` phrasing) updated accordingly, 2026-07-14.
9. **`scripts/sync-workspace.sh --force` and `scripts/sync-templates.sh`
   (all 5 groups), human-confirmed 2026-07-14.** Workspace root refreshed
   (backup at `workspace/.backups/20260714T161034Z/`). Template sync pushed
   real fixes to groups A/B/C/E (commits `abcc436`/`26d8524`/`513853a`/
   `441b80c`) — `team_policy` promoted `stub` → `full-core` for those four,
   their prior "starter repo, full team unjustified" exception blocks
   removed since 39558a0 made the full core their standard rendered state.
   Group D reported **already in sync** — its live `main` had actually been
   correctly synced since 2026-07-11 (commit `d225ea2`, ~4 min after
   `39558a0` landed). This means item #8's audit finding for group D, and
   this file's own prior "CORRECTED" note about it, were both wrong: the
   audit checked this repo's *local* clone in the workspace, which was 1
   commit behind `origin/main` because nothing had fetched it — a direct
   instance of the "never trust a stale local view" warning in
   `workspace/CLAUDE.md`'s concurrent-agent protocol. Re-verified by
   fetching `origin/main` directly before trusting either claim. All 5
   local template-repo clones fast-forwarded to `origin/main` as part of
   this fix. `registry.yml`'s group D note now documents this correction
   chain instead of repeating the error.
10. **Human GitHub team creation, org-team-based CODEOWNERS rollout, and live
    ruleset/security-setting changes (plan Sections 5/6/7), human-confirmed
    2026-07-14.** All 5 org teams created (`automationnexus-owners`,
    `automationnexus-platform`, `automationnexus-security`,
    `automationnexus-release`, `automationnexus-app-maintainers`) with
    per-repo permissions assigned per this file's matrix; org-team-based
    `CODEOWNERS` rolled out to every repo (superseding the individual
    `@t-abraham` fallback CognitiveSystems/HomeAssistant carried, and
    MediaRefinery's inert commented-out file). Live ruleset/security changes
    applied across the org — surfaced and closed one genuine gap in the
    process: `.github` itself had zero live branch-protection ruleset and no
    `protect-master.json`, because its own reusable `ci.yml`/`semgrep.yml`
    are `workflow_call`-only definitions it never triggered on its own PRs
    (confirmed live: `.github` PR #24 originally reported an empty
    `statusCheckRollup`). Fixed by adding thin `self-ci.yml`/`self-semgrep.yml`
    caller wrappers (same pattern as `ARCRunner`'s `main-only` wrapper and
    `CognitiveSystems`'s semgrep caller) plus a `.yamllint` config (`extends:
    relaxed`, `line-length.max: 240` — precedent: `CognitiveSystems/.yamllint`)
    to accommodate this repo's own pre-existing long lines, then applying
    `protect-master.json` (`.github` PR #25). Applying the new ruleset
    retroactively blocked `.github` PR #24 (its head branch predated
    `self-ci.yml`, so the newly-required checks structurally couldn't report)
    — resolved by merging `master` into the PR branch so the checks would
    run, not by bypassing the ruleset. `.github` PR #24 then merged, landing
    this governance package on `master`.

### Still open

One item remains, staged and human-gated:

1. **`sync-shared-claude.sh` runs** — propagates `templates/_shared/.claude/`
   updates to the app repos via protected-branch-safe PRs to `dev`. Not yet
   run this pass. `sync-workspace.sh` and `sync-templates.sh` are done (see
   item #9); team creation, CODEOWNERS rollout, and ruleset/security changes
   are done (see item #10).
