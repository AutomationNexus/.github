# Governance

Canonical source of truth for who — and what — does work across the
AutomationNexus org, and under what authority.

- **`registry.yml`** — the data. Repositories, AI agents, AI commands, human
  GitHub teams, ownership, branch models, sync mechanisms, and documented
  exceptions.
- **`schema.json`** — the structural contract for `registry.yml`. Documentation
  and (when `jsonschema` happens to be installed) a validation aid;
  `scripts/validate-governance.py`'s hand-rolled checks are authoritative
  either way, since this repo has no dependency management of its own and
  cannot assume `jsonschema` is present.
- **`organogram.md`** — the same data rendered as a readable hierarchy and a
  repo/team/task matrix, for humans skimming rather than diffing YAML.

Edit `registry.yml` on a feature branch, PR it to `master`, and run
`python scripts/validate-governance.py` before requesting review. Never
hand-edit a *generated* copy (the workspace-root `CLAUDE.md`/`.claude/`, or a
synced repo's `.claude/`) to patch drift found here — fix it here and re-run
the relevant sync script (`sync-workspace.sh`, `sync-shared-claude.sh`, or
`sync-templates.sh`).

## Humans vs. AI — the one rule that matters

**AI agents are not GitHub identities.** They hold no GitHub permissions,
appear in no `CODEOWNERS` file, belong to no org team, and cannot authenticate
to anything. Every AI agent in `registry.yml` (`org_agents`, `repo_core_team`,
and each repo's `domain_agents`) is a **Claude Code role**: a prompt, a model
tier, a tool allowlist, and a place in the routing/escalation graph — nothing
more. All of it runs under whichever human operator's Claude Code session and
GitHub credentials happen to be active.

**`human_teams`** are the only entities that hold real GitHub state: repo
permissions, `CODEOWNERS` review assignment, ruleset bypass actors (alongside
the CI-Bot GitHub App), and org membership. When this registry says an agent's
`escalation_target` is `human`, that means the operator, not any team slug —
teams are a permissions/ownership construct, not an escalation target.

Two fields on every agent entry exist specifically to keep this boundary
enforceable rather than aspirational:

- **`mutation_class`** — what the agent is structurally permitted to do
  (`read-only`, `repo-write`, `cross-repo-write`, `admin-state`,
  `human-confirmation-required`). A `read-only` agent making a state change is
  always a bug, never a judgment call.
- **`escalation_target`** — who or what the agent hands unresolved work to.
  Following the chain from any agent always terminates at `human` — there is
  no purely-AI approval loop anywhere in this org.

## Verification states

Every entry that claims something is true of the live org (a repo's branch
flow, a team's existence, a repo's team composition) carries a `state`:

| State | Meaning |
|---|---|
| `active` | Implemented and confirmed live (or not the kind of thing that needs a live check). |
| `desired` | Documented target; not yet implemented. Not a live-state claim. |
| `exception` | Intentional, permanent deviation from the default policy — see `exceptions:` on the entry. |
| `needs-verification` | May exist; not yet confirmed against live GitHub state. |
| `permission-limited` | A live check was attempted and blocked by credential/plan scope — never collapse this into a pass or a fail. |

`needs-verification` is the honest default for anything not yet re-checked
live after this registry was authored. Do not upgrade an entry to `active`
without an actual `gh`/API check; do not downgrade a `permission-limited`
result to `needs-verification` just because a check merely wasn't retried.

## Authority classes

Every command (`org_commands`, `repo_core_commands`, and any repo-local
command) declares a `confirmation_class` from `authority_classes`:
`read-only`, `repo-write`, `cross-repo-write`, `admin-state`,
`human-confirmation-required`. A command's class is a ceiling, not a
suggestion — an agent invoked by a `read-only` command cannot make a
`human-confirmation-required` change just because a user asked nicely inside
that conversation.

## Rank vs. authority

Being higher in `org_agents`' `rank` (`org-lead` vs `org-operational`) is a
**reporting/escalation** position, not a grant of write authority. A
`chief-architect` recommendation still requires the same human confirmation a
`release-manager` dispatch does; rank changes who routes work and who a
blocked agent escalates to, not what any agent is allowed to mutate.

## Exceptions are first-class, not gaps

An entry with `state: exception` (ARCRunner's minimal team, the 5 template
repos' stub teams, `sync-templates-direct-push`,
`modeldeck-addon-auto-promote`) is a deliberate, reviewed deviation — each one
carries `rationale`, `owner`, and `review_trigger`. Finding one of these is
not a defect to silently fix; it's a signal to check whether the
`review_trigger` condition has since been met.

## See also

- `organogram.md` — rendered hierarchy and repo/team/task matrix.
- `../workspace/CLAUDE.md` — org-root operating protocol for a session opened
  at the workspace root.
- `../templates/_shared/CLAUDE.md.template` — repo-tier risk-track model
  (Tracks A–D) that every full repo's `/execute` implements.
- `../docs/ai-migration.md` — model-tier mapping and per-repo AI rollout
  history.
