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
 .github meta-repo team (workflow-engineer, + architect/security-auditor
 once added — see "Open items" below)

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
HomeAssistant's `live-inspector`/`drift-sync`/`release-operator` +
`dry-run-deploy`.

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

## Open items (not yet corrected — tracked here, fixed in later PRs per the rollout order)

These are known, registered defects/decisions — not silent gaps. Each is also
noted on its repo's `notes:` field in `registry.yml`. None is fixed in this
PR; fixing another repo's files is out of scope for the canonical `.github`
PR per the plan's staged rollout order (Section 7).

1. **`.github` meta-repo team** — `architect` and `security-auditor` are not
   yet added locally (this PR's Task #4 fixes this one, since it's within
   `.github` itself).
2. **CognitiveSystems** — `CLAUDE.md` routes to a nonexistent `/pr` command.
   Fix: either add a real `pr.md` with an assigned owner, or repoint the
   pipeline text at a valid existing action. Deferred to a CognitiveSystems
   feature-branch PR.
3. **ModelDeck routing table** — the `architect` agent exists locally but is
   missing from the visible subagent/routing table in `ModelDeck/CLAUDE.md`.
   Deferred to a ModelDeck feature-branch PR.
4. **ModelDeck default branch** — documented flow targets `dev`; live GitHub
   reportedly shows `main` as default. Needs a live re-check; resolve by
   either changing the default to `dev` or recording a deliberate exception
   with rationale.
5. **ModelDeck `.claude/settings.json`** — missing a
   `Bash(git push origin dev:*)` deny present in the shared baseline.
   Deferred to a ModelDeck feature-branch PR.
6. **Template group D (`template-infra-main-only`)** — canonical group D
   includes `/execute`; the live repo may not. Needs a policy decision:
   either the live repo should match the rendered canonical bundle, or its
   narrower command set is a registered exception.
