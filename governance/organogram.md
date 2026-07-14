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
| `.github` | meta | `master` | meta-core | canonical-source | automationnexus-platform | needs-verification |
| `CognitiveSystems` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `MediaRefinery` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `ModelDeck` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `Uploadarr` | full | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `HomeAssistant` | config-only | `dev` | full-core | consumer | automationnexus-app-maintainers | needs-verification |
| `ARCRunner` | minimal | `main` | minimal | excluded | automationnexus-platform | exception |
| `template-python-docker` | template (A) | `main` | stub | template-target | automationnexus-platform | needs-verification |
| `template-python-pypi` | template (B) | `main` | stub | template-target | automationnexus-platform | needs-verification |
| `template-docker-ha-addon` | template (C) | `main` | stub | template-target | automationnexus-platform | needs-verification |
| `template-infra-main-only` | template (D) | `main` | stub | template-target | automationnexus-platform | needs-verification |
| `template-ha-config` | template (E) | `main` | stub | template-target | automationnexus-platform | needs-verification |

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
   ModelDeck, Uploadarr, HomeAssistant, ARCRunner); the 5 template repos are
   confirmed out of sync with a canonical change (commit `39558a0`,
   2026-07-11) that added the full shared core to groups A/B/C/E and a new
   `execute.md` to group D — none of it has reached the live repos yet.
   One existing registry note (`template-infra-main-only` claiming
   "re-verified, no drift") was found to be false and has been corrected.
   `registry.yml` and `workspace/CLAUDE.md` (`pyproject.toml`/`bump-type`
   phrasing) updated accordingly, 2026-07-14.

### Still open

Two items remain, both staged and human-gated — neither is a defect this
audit can resolve on its own:

1. **A human-confirmed `scripts/sync-templates.sh` run** to close the
   confirmed template-repo drift documented in `conformance.md` and in
   each of the 5 template repos' `registry.yml` entries. This is the org's
   one standing direct-push-to-`main` exception
   (`exceptions: sync-templates-direct-push`) — always requires the human
   to name the exact repos/options in the current turn before it runs. A
   follow-up registry edit should also reconsider `team_policy: stub` for
   groups A/B/C/E once their live state matches canonical (their canonical
   is no longer a bare `qa-gatekeeper` stub).
2. **The human-confirmed rollout items in plan Sections 5/6/7** — human
   GitHub team creation, CODEOWNERS rollout beyond the 3 repos that have
   any CODEOWNERS file today (CognitiveSystems and HomeAssistant use an
   individual `@t-abraham` fallback per Section 5's sanctioned temporary
   state; MediaRefinery's is inert/fully commented out; the other 9 repos
   have no CODEOWNERS file at all), live ruleset/security-setting changes,
   and `sync-shared-claude.sh`/`sync-workspace.sh` runs.
