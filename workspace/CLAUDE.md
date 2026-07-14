# CLAUDE.md — AutomationNexus workspace root

This is the local workspace root containing clones of every `AutomationNexus`
GitHub org repo. **It is not itself a git repository.** Claude Code walks up
parent directories collecting `CLAUDE.md` files, so this file auto-loads for
any session opened inside any repo below — you don't need to go looking for
it. Treat it as the org-wide source of truth: consult it whenever a repo's
own `CLAUDE.md` doesn't cover something, or when CI/promote/versioning looks
broken and you're not sure why.

> **This file is generated.** Canonical source: the `automationnexus/.github`
> repo, `workspace/CLAUDE.md`. Edit there (PR to `master`), then run
> `scripts/sync-workspace.sh` — hand-edits here get flagged as drift and
> overwritten (after a backup) on the next sync.

The canonical source of truth for org agents, commands, human teams, repo
ownership, and documented exceptions is `automationnexus/.github`'s
`governance/registry.yml` — see `governance/README.md` for terminology and the
human-vs-AI distinction, and `governance/organogram.md` for a rendered
hierarchy and repo/team/task matrix. This file's Org roster table below is a
convenience summary; the registry is authoritative if they ever disagree.

## Org map

- **`.github`** (`automationnexus/.github`) — the meta-repo. Owns every
  reusable GitHub Actions workflow (`uses:
  automationnexus/.github/.github/workflows/<name>.yml@v1`), the 5
  `templates/<group>/` starter bundles, and `scripts/sync-templates.sh`. Uses
  `master` as its trunk (no `dev`/`main` split — it isn't an application).
- **Real app repos**: `CognitiveSystems`, `MediaRefinery`, `ModelDeck`,
  `Uploadarr` — each has `dev`/`main`, a `pyproject.toml`, and a
  `release.yml` that tags `vX.Y.Z`. These 4 are the full auto-versioning
  scope (see below). `HomeAssistant` also has `dev`/`main` and a promote
  workflow but no `pyproject.toml` — it's a Home Assistant config repo, not
  a versioned package. `ARCRunner` is `main`-only (no `dev`, no promote
  workflow, no `pyproject.toml`) — it just builds a runner Docker image.
- **Templates** (`template-python-docker`, `template-python-pypi`,
  `template-docker-ha-addon`, `template-ha-config`,
  `template-infra-main-only`) — real, live starter repos synced from
  `.github/templates/` by `scripts/sync-templates.sh`. Only the first two
  (Python app groups) carry `pyproject.toml`/`bump-type`.

## Branch/PR flow (hard rule)

**Never push directly to `dev` or `main`** (or `master` in `.github`) in any
repo. Always: feature branch → PR → `dev` → CI green →
`auto-merge.yml`/CI-Bot merges automatically → `dev` → (green) →
`promote-dev-to-main.yml` → PR → `main` → `release.yml` publishes.

- `promote-dev-to-main.yml` is normally a manual `workflow_dispatch`. ModelDeck
  additionally has a `push`-triggered add-on-only path (see its own
  `CLAUDE.md`) that auto-promotes `modeldeck/**` changes without a version
  bump.
- Repos without a `dev` branch (`ARCRunner`, all 5 templates) use feature
  branch → PR → `main` directly instead.
- **One documented, narrow exception**: `scripts/sync-templates.sh`
  direct-pushes sync commits to the 5 `template-*` repos' `main` branch. Those
  repos have no `dev` branch and no CI gating that push — it's the script's
  own intentional design (see `.github/CLAUDE.md`). Even so, always get
  explicit human confirmation before running it — never run it unprompted.

## Reusable-workflow architecture

Every consumer repo calls shared workflows via
`uses: automationnexus/.github/.github/workflows/<name>.yml@v1`. If a
consumer repo needs new behavior, the fix is a new **generic input** on the
shared workflow in `.github` — never a one-off fork/inline copy in the
consumer repo. Precedent inputs: `build-args`, `main-source-allow-glob`,
`exclude-paths`, `strip-dev-only-paths`, `bump-type`.

## Auto-versioning (`bump-type`)

`promote-dev-to-main.yml` takes a `workflow_dispatch` input `bump-type`:
`patch` (default) / `minor` / `major`. It computes the next `X.Y.Z`:

- Source of truth = the latest `vX.Y.Z` git tag reachable on `main` (fallback:
  `main`'s current `pyproject.toml` version; fallback `0.0.0` for a first-ever
  release).
- **patch**: `Z += 1`, wrapping — once `Z` would exceed `99`, `Y += 1` and
  `Z` resets to `1`.
- **minor**: `Y += 1`, `Z` resets to `1`.
- **major**: `X += 1`, `Y` and `Z` reset to `1`.

The computed version is written to `pyproject.toml` on the promote branch as
part of the reconciliation commit, and the promote PR title gets a
`(Minor)`/`(Major)` suffix for visibility (the dispatch input, not the title
text, is what actually drives the bump). **Never hand-edit a version in
`pyproject.toml`** — it's fully automated now.

Scope: CognitiveSystems, MediaRefinery, ModelDeck, Uploadarr,
`template-python-docker`, `template-python-pypi`. ModelDeck's `push`-triggered
add-on-only promote path always passes `bump-type: none` — it must never bump
the app version. HomeAssistant has the input available (it inherited it from
the shared workflow) but it's a no-op there — no `pyproject.toml` to write to.

## Why a temp branch

A version-bump/reconciliation commit can't be pushed straight to `dev` or
`main` — their rulesets reject direct pushes even from the CI-Bot's bypass
identity. Whenever `exclude-paths`, `strip-dev-only-paths=true`, or
`bump-type != none` is set, the promote workflow instead builds a throwaway
`sync/publish-main-promote-<run>-<n>` branch from the current `main` snapshot,
merges `dev` into it (with dev winning ordinary content conflicts), restores
explicitly main-owned `exclude-paths`, strips dev-only paths, and applies the
version bump before PRing *that* branch into `main`. A retry rebuilds the branch
from freshly fetched refs if `main` moves during the promotion.

## Concurrent-agent protocol

These repos are actively worked on by other Claude Code sessions, often at
the same time as you. **Never trust a stale view of a repo's state.**

- Before acting on a PR/branch/workflow, re-check it live:
  `gh pr view <n> --json state,mergeable,mergeStateStatus,statusCheckRollup`,
  `gh run list --workflow=<name> --limit 10`.
- Don't assume a `cancelled` workflow run failed outright — it may have
  already pushed a branch/opened a PR that later merged independently. Check
  for a resulting PR/tag before concluding it did nothing.
- Never touch another branch's uncommitted work in a shared local clone. If
  you need to work off `dev`/`main` while another branch has dirty state, use
  `git worktree add ../<repo>-<purpose> -b <branch> origin/dev` instead of
  checking out over it.
- A local checkout sitting on an old feature branch usually just means that
  branch's PR already merged — fetch and re-branch off the fresh
  `origin/dev`/`origin/main`, don't assume you need to reuse or clean it up
  first.

### Mandatory collision protocol

Run this sequence before any multi-repo or multi-agent action, and re-run
the last two steps immediately before any outward-facing operation:

1. **Start with branch, dirty-tree, remote PR, and relevant workflow
   checks** — `git status --short --branch`, `gh pr list`, `gh run list` for
   every repo the task touches, before planning sequencing or dispatching
   work.
2. **Detect active branches/PRs or local work touching the same repo/
   paths** — another session's feature branch, an open PR against the same
   files, or a workflow run already in flight counts as active work, not
   noise.
3. **Never overwrite or clean another session's work** — no
   `git reset --hard`, `git clean`, or force-checkout over a branch you did
   not create this turn, even if it looks stale or abandoned.
4. **Use a worktree when isolation is required and supported; otherwise
   pause and narrow scope, or escalate** — `git worktree add
   ../<repo>-<purpose> -b <branch> origin/dev` keeps a dirty branch
   untouched. If a worktree isn't viable (no git repo present — e.g. this
   workspace root itself), narrow the task to a non-colliding slice or ask
   the human before proceeding.
5. **Re-check live state before pushes, PR operations, workflow dispatches,
   merges, promotions, or admin changes** — the state captured in step 1 can
   be minutes stale by the time you act; a second `gh pr view`/`gh run list`
   immediately before the mutating call is not redundant.
6. **If remote state changed during work, reconcile and report the race
   rather than proceeding from a stale plan** — e.g. a target branch moved,
   a PR you meant to update already merged, or a workflow you were about to
   dispatch already ran. Tell the user what changed and what you're doing
   about it instead of silently continuing the original plan.

### Durable vs. transient state

Coordinate through **durable shared state** — evidence that persists and
that any session, yours or another agent's, can independently re-verify:

- the canonical governance registry (`governance/registry.yml`) and
  `CLAUDE.md` instructions across the org;
- git branch/commit history and clean-working-tree evidence;
- PR, check, workflow-run, and release state on GitHub;
- explicit handoff/handback packets (see "Handoff packet" / "Handback
  packet" below).

The task list and conversation transcript are **transient orchestration
state** — real within a session, but invisible to any other session and not
something another agent or a future session can rely on. Do not turn them
into committed scratchpads: don't commit agent-to-agent status reports,
progress logs, or coordination files to a repo unless that repo's
deliverables explicitly require them. A repo's own `CLAUDE.local.md` may
hold personal resume notes (CognitiveSystems' is a live example) but it is
gitignored and personal — never canonical, never committed, never something
another session should be expected to have read.

## CI-Bot GitHub App

Privileged operations (merges, promote-branch pushes, PR creation) mint a
short-lived token via `actions/create-github-app-token@v1` for the CI-Bot
GitHub App — never `GITHUB_TOKEN` or a personal PAT. This is what lets a
bot-driven push/merge correctly cascade downstream workflow triggers.

## Dev-only files convention

`CLAUDE.md` and `.claude/` are committed on `dev` but must never reach
`main`. Every consumer repo's `promote-dev-to-main.yml` wrapper must set
`strip-dev-only-paths: true` (plus a `.github/dev-only-paths` file) or these
files will land on `main` and fail `ci.yml`'s Guard Main Files check.

## Windows gotchas

- `core.autocrlf` normalizes LF→CRLF on checkout, so files with zero real
  content change still show as "modified" in working-tree status. Check the
  **staged** diff (`git diff --cached --quiet`) after `git add -A`, not
  working-tree `git status`, before deciding whether there's anything to
  commit.
- A bash `<<'EOF'` heredoc does NOT strip leading whitespace. Any Python (or
  other language) embedded in a `run: |` step's heredoc must be flush-left at
  column 0, even though that looks visually inconsistent with the surrounding
  YAML/bash indentation.
- Colon-containing git refs (e.g. `git show origin/branch:path`) can get
  mangled by Git Bash's path conversion — prefix with `MSYS_NO_PATHCONV=1` if
  a command behaves strangely on a ref like that.

## Emergency / doubt checklist

Something looks broken, or you're not sure of current state? Run these
first, don't guess from memory:

```
gh pr checks <n>
gh pr view <n> --repo AutomationNexus/<repo> --json state,mergeable,mergeStateStatus,statusCheckRollup
gh run list --workflow="<workflow name>" --limit 10 --json databaseId,status,conclusion,event,createdAt
gh workflow list
```

If the shared-workflow *internals* are the question (not a specific repo's
symptom), `automationnexus/.github`'s own `README.md` and `CLAUDE.md` are the
canonical source — read those before guessing at what a generic input does.

## Agent organization (org tier ↔ repo tier)

This workspace runs a two-tier Claude Code agent organization:

- **Org tier ("CTO desk")** — a session opened at THIS directory (the
  workspace root) loads `.claude/agents/` (6 org agents) and
  `.claude/commands/` (org commands). Use it for cross-repo planning, status
  sweeps, promote/release orchestration, template/workspace syncs,
  shared-workflow design in `.github`, and org-wide security audits.
- **Repo tier (departments)** — a session opened inside a repo loads only
  that repo's `.claude/` team (domain engineers, QA gate, repo commands).
  Use it for all implementation work on that repo.

Key mechanic: **`CLAUDE.md` cascades up parent directories;
`.claude/agents/` and `.claude/commands/` do not.** That is why the tiers
are location-bound — this file is visible from every repo session, but the
org agents are not.

### Org roster

| Agent | Model | Role |
|-------|-------|------|
| `chief-architect` | sonnet (high effort) | Cross-repo planning + routing; emits per-repo handoff briefs |
| `platform-engineer` | sonnet | `.github` meta-repo internals: reusable workflows, templates, scripts, rulesets |
| `release-manager` | sonnet (high effort) | Promote/release orchestration across repos (human-confirmed dispatches only) |
| `security-officer` | sonnet (high effort) | Org-wide security audits, read-only |
| `org-inspector` | haiku | Read-only live status sweeps — the "emergency checklist" as an agent |
| `template-steward` | sonnet | `templates/` bundles ↔ `template-*` repos ↔ app-repo shared layer consistency |

Commands: `/org-status` (status sweep), `/dispatch` (route a task),
`/promote` (dev→main release runbook), `/org-audit` (security sweep),
`/sync-templates` (template repo sync, human-confirmed), `/sync-workspace`
(root copy refresh), `/new-repo` (guided repo bootstrap).

### Org-root operating protocol

A workspace-root session is the **orchestrator/CTO desk**, not a hidden
super-repo engineer. Every non-trivial request follows this lifecycle:

1. **Classify and route.** Identify the request type and route it:
   status → `org-inspector` (`/org-status`); cross-repo design → `chief-architect`
   (`/dispatch`); `.github` platform work → `platform-engineer`; release/promote
   → `release-manager` (`/promote`); security → `security-officer` (`/org-audit`);
   template drift → `template-steward` (`/sync-templates`); new repo →
   `chief-architect` (`/new-repo`).
2. **Refresh state.** Before planning or acting, capture local branch/dirty
   state and live PR/workflow/ruleset state for every affected repo — see
   "Concurrent-agent protocol" above and the "Emergency / doubt checklist"
   below. A `cancelled` run is ambiguous until you check for a resulting
   PR/tag; don't assume it did nothing.
3. **Build the dependency graph.** Shared-workflow/canonical `.github`
   changes land first; consumers follow; workspace/template propagation
   (`sync-workspace.sh`/`sync-shared-claude.sh`/`sync-templates.sh`) only
   happens after the canonical change merges.
4. **Delegate bounded work.** Every org-agent assignment names scope, inputs,
   allowed actions, output format, dependencies, and completion criteria. No
   agent expands its own scope or performs an outward-facing action that was
   delegated only as research — see "Unified authority" below.
5. **Produce repo handoffs.** Repo-tier agents are location-bound and cannot
   be spawned from the root — `/dispatch` emits a handoff brief per affected
   repo instead (see "Handoff packet" below).
6. **Collect handbacks.** Require each repo session to return the handback
   packet (see below) before treating that repo's slice as done.
7. **Close out from live evidence.** Re-check PR/check/release state before
   declaring the cross-repo task complete; record unresolved blockers and
   `permission-limited` checks explicitly rather than omitting them.

For small mechanical cross-repo edits, the root session may edit files and
open PRs directly instead of producing a full handoff — allowed, but follow
each repo's `CLAUDE.md` and run its QA gate commands manually (its QA agents
aren't loaded here).

#### Handoff packet (org → repo)

Every `/dispatch` handoff brief includes:

- repository and execution order relative to other repos in this task;
- goal, non-goals, starting/target branch;
- likely paths and relevant `CLAUDE.md` constraints;
- required repo agents/commands and risk track (see repo-tier standard below);
- shared-workflow/template dependencies this repo's change relies on;
- file ownership and forbidden overlap (when more than one repo/agent touches
  related paths);
- permission/secret constraints;
- review, security, QA, runtime, and rollback requirements;
- expected PR target, release/version impact, and escalation triggers;
- the required handback fields (below) — restated so the repo session knows
  what it must return.

#### Handback packet (repo → org)

Every repo session working from a handoff brief returns:

- repo, branch, PR, commits, files changed;
- tests/QA/runtime verification, with pass/fail evidence — not just "ran QA";
- review/security disposition;
- deviations from the brief and any integration conflicts found;
- open risks, follow-up work, and any promote/release/admin action still
  required.

The org root reconciles handbacks against the dependency graph from step 3
before marking the cross-repo task complete.

### Agent result envelope

The handoff/handback packets above are the report contract for an entire repo
session's work against a brief. One level down, every **individual agent
assignment** — org tier or repo tier, dispatched via the Agent tool or by
name, in a single session or across many — returns this envelope instead of
free-form prose:

- assignment ID (a short label the invoking session can match request→result
  by) and the parent task it serves;
- scope completed **and** scope not attempted — state the latter explicitly;
  "didn't get to X" is a result, not a caveat to bury in a footnote;
- findings or changes, with file:line or file/path evidence — no unsupported
  claims;
- assumptions made and any contracts affected (API/schema/workflow/shared
  file);
- validation run and validation explicitly omitted, and why;
- blockers, risks, a confidence level, and the recommended next recipient
  (main session, a specific peer agent, or human);
- state-changing actions actually performed — normally **none** for
  research/review agents (`architect`, `reviewer`, `security-auditor`,
  `qa-gatekeeper`, `org-inspector`, `security-officer`, `chief-architect`).
  A non-empty list here from an agent whose `mutation_class`/
  `confirmation_class` in `governance/registry.yml` is `read-only` is itself
  a defect to report up, not something to silently accept.

The orchestrating session (main session, or the repo session assembling a
handback) integrates these envelopes. Agents do not exchange them directly
with each other outside of what the orchestrating session relays — a peer
agent's envelope is evidence for the orchestrator's decision, never a
standing authorization for another agent's next action (see "Unified
authority and confirmation" below).

### Unified authority and confirmation

- Read-only agents remain read-only regardless of what a peer agent requests.
- A peer agent may recommend an action or request analysis; it cannot grant
  permission, user approval, elevated scope, or authorize a
  destructive/outward-facing operation on another agent's behalf.
- A state-changing action requires both authority from the main session's
  task **and**, for the classes below, explicit human confirmation naming
  the action, repo, target, and material options in the current turn.
- Always confirm before: a `sync-templates.sh` direct-push run, a
  promote/release dispatch, repo/secret creation, any non-`GET` admin API
  call, a ruleset/team/security-setting change, or a force-overwrite of
  generated workspace drift (`sync-workspace.sh --force`).
- No direct push to a protected trunk (`dev`/`main`/`master`) from any
  session, org or repo tier — the sole standing exception is
  `sync-templates.sh`'s documented direct-push to the 5 `template-*` repos'
  `main`.
- No consumer repo forks a shared workflow to avoid escalating to
  `platform-engineer`/`.github` — see "Reusable-workflow architecture" above.

Every command's `confirmation_class` in `governance/registry.yml`
(`read-only` / `repo-write` / `cross-repo-write` / `admin-state` /
`human-confirmation-required`) is a ceiling, not a suggestion: an agent
invoked by a `read-only` command cannot make a `human-confirmation-required`
change just because a user asked for one inside that conversation.

### Escalation (repo → org)

A repo session that hits a cross-repo or shared-workflow problem must not
fork the shared workflow (see "Reusable-workflow architecture" above). Stop
and take it to a workspace-root session (`/dispatch`) or straight to the
`automationnexus/.github` repo.

### Repo-tier standard

Every full repo team shares 4 core roles — `architect` (sonnet, high
effort), `qa-gatekeeper` (haiku), `reviewer` (sonnet), `security-auditor`
(sonnet, high effort) — plus repo-specific domain engineers and commands.
Canonical core text lives in `automationnexus/.github` at
`templates/_shared/.claude/`; each repo keeps its own `description:` line
and anything below the `<!-- repo-specific -->` marker in those files.
Propagate shared-core updates with `scripts/sync-shared-claude.sh`
(PR-based, respects protected branches). ARCRunner keeps a deliberately
minimal team (`qa-gatekeeper` only) — a documented exception, excluded from
propagation.

## Editing this file / the root .claude

The root copies of `CLAUDE.md` and `.claude/` are **generated** — canonical
source: `automationnexus/.github`, `workspace/` directory. Edit there, PR to
`master`, then run `scripts/sync-workspace.sh` (or `/sync-workspace` from a
root session). Hand-edits at the root are flagged as drift and only
overwritten after an automatic timestamped backup.
