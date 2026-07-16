# Org-wide delivery board (GitHub Project)

> Looking for a human "how do I use this board" quickstart instead of the
> field/automation reference below? See [`board-guide.md`](board-guide.md).

`AutomationNexus — Delivery` is the single org-level Project v2 that tracks
Issues from every repo in one board / table. **The board is ISSUE-CENTRIC and
LEAN:**

- **Issues are the cards.** A pull request never gets its own card — its
  relationship to the issue it closes is surfaced through the built-in
  **Linked pull requests** field on the issue's card instead. This mirrors how
  GitHub already links a PR to the issue(s) it closes (via a closing keyword
  in the PR body, or a manual link) — the board just reads that existing
  relationship rather than tracking the PR as a second, separate item.
- **Status is derived, not set by hand (for pipeline stages).** Each issue's
  `Status` reflects the furthest-progressed linked PR across the whole `dev →
  promote → main → release` pipeline — see "How Status is derived" below.
- **The field set is lean.** Only `Status`, `Area/Type`, and the built-in
  `Repository` / `Linked pull requests` fields matter now. The earlier
  planning layer (`Bump type`, `Priority`, `Track`, `Release target`, `Start
  date`, `Target date`) was dropped — none of it was read or written by any
  automation, so it was pure unused surface area.

- **Project:** <https://github.com/orgs/AutomationNexus/projects/1>
- **Why one project (not one per repo):** GitHub has no org-wide rollup across
  multiple Projects. A single Project + the built-in `Repository` field gives a
  true cross-repo view; per-repo projects would not.

## What is codified vs. UI-only

| Layer | Owned by | Notes |
|-------|----------|-------|
| Custom fields + Status stages | `scripts/bootstrap-org-project.sh` | Field creation is idempotent; the Status *options* step is create-only (fresh boards only) — see the script's own comments |
| Item intake (issues only) | `.github/workflows/add-to-project.yml` | Reusable workflow every repo calls; gated to `issues` events — see "Per-repo intake" below |
| Status (derived from linked PRs) + Area/Type auto-fill | `.github/workflows/org-project-sync.yml` | Runs hourly (cron `:17`) plus manual dispatch |
| Saved views, native **Iteration** field | Humans, in the UI | The GitHub API cannot create these |

## Fields

Built-in `Status` is reshaped into the delivery pipeline; `Area/Type` is the
one remaining custom field; `Repository` and `Linked pull requests` are
native GitHub Project fields (no setup needed) that the lean view set below
relies on:

- **Status** (pipeline): `Backlog · In Progress · In Review · On Dev · Promote Pending · Done · Released · Blocked`
- **Area/Type**: `feature · bug · chore · release · platform · security · docs`
- **Repository** *(native)* — which repo the issue belongs to.
- **Linked pull requests** *(native)* — GitHub's own built-in surface for a PR
  linked to this issue; this is how a PR's progress becomes visible on an
  issue's card without a separate PR card existing.
- **Iteration** — optional; add manually (API cannot create iteration fields)
  if a team wants a UI-only "Current sprint" filter: Project → **+** new field
  → Iteration, weekly. Not required by anything in this doc.

## How Status is derived

`org-project-sync.yml` computes each issue's Status from its linked pull
request(s) — resolved via the GraphQL
`closedByPullRequestsReferences(includeClosedPrs:true)` connection on the
issue, which covers both open and closed/merged linking PRs, including PRs
linked from another repo. Each linked PR classifies into at most one stage:

| Linked PR state | Stage |
|---|---|
| Open, base `dev` | **In Review** |
| Open, base `main`, head `sync/publish-main-promote-*` | **Promote Pending** |
| Merged to `dev`, merge commit reachable from `main`'s tip | **Released** |
| Merged to `dev`, merge commit not yet reachable from `main` | **On Dev** |
| Merged to `main`, head `sync/publish-main-*` | **Released** |
| Merged straight to `main` in a main-only repo (e.g. `ARCRunner`) | **Released** |
| Anything else (closed unmerged; merged to another base; out-of-scope repo) | *(not classifiable)* |

If an issue has more than one linked PR, the **furthest-progressed**
classifiable stage wins (`Released` > `Promote Pending`/`On Dev`/`In Review`
by rank — see the rank table below). If **no** linked PR is classifiable:

- a **closed** issue goes to **Done** (a completed deliverable with no
  versioned release — meta/decision work, a `.github`-only change, wontfix,
  etc.) — skipped rather than failing if the board doesn't have the `Done`
  option yet;
- an **open** issue with no status yet defaults to **Backlog** (existing
  default; never overrides an existing status).

Status only ever **advances**, never regresses: `Backlog(0) < In
Progress(1) < In Review(2) < On Dev(3) < Promote Pending(4) < Done(5) <
Released(6)`. `Done` deliberately ranks just *below* `Released`, not tied
with it — an issue already at `Done` can still advance to `Released` if a
linked PR is later found to have actually shipped (that's a correction, not
a downgrade), while the same guard stops every ordinary pipeline stage from
overwriting `Done`, and stops `Done` itself from ever overwriting `Released`.
`Blocked` and items already at `Released` are treated as manual-only and are
never touched by the sweep. A digest-tracking issue (the perpetual
"📊 Delivery digest" issue that `board-digest.yml` maintains) is skipped
entirely — it is never a real deliverable even if it's ever closed.

Any REST/compare error for a given linked PR fails open to `On Dev` and is
counted, rather than aborting the sweep; a systemic failure to resolve a
repo's release tag/ref itself (not a specific PR's compare call) is counted
separately under `ref_resolution_errors`.

**Legacy PR cards:** a pull-request-content item still on the board from
before this redesign is left completely untouched by the sweep (never
classified, never given a Status write) — it is counted in the run summary
as a non-issue item, and should be cleared via the **Auto-archive items**
workflow toggle (see below) or archived by hand. New PR items should stop
appearing once every consumer repo's `add-to-project.yml` caller is running
against the gated `@v1` (see "Per-repo intake" below).

## Saved views to create (UI, ~2 min)

Open the Project, use the **＋** next to the view tabs. For each: pick the
layout, then set grouping/filter via the view's **⋯** menu. Lean by design —
three views cover the whole issue-centric model:

1. **Board — Ongoing work** *(default)* — layout **Board**, group by **Status**.
2. **By Repo** — layout **Table**, group by **Repository**.
3. **Release pipeline** — layout **Table**, filter
   `status:"On Dev","Promote Pending","Released"`, group by **Repository**.

(Earlier revisions of this board also had `Roadmap`, `Current sprint`, `At
risk`, and `Security / audits` views — `Roadmap` and `At risk` depended on
fields dropped in this redesign (`Start date`/`Target date`, `Track`) and no
longer apply; `Current sprint` and `Security / audits` are still possible to
recreate from `Iteration`/`Area/Type` if a team wants them, but aren't part
of the lean default set.)

## Workflow toggles (UI, Project → ⋯ → Workflows)

- **Auto-add to project** — this board is issue-centric now: if this UI
  toggle is enabled as a backstop, filter it to `is:issue` (not
  `is:issue,pr`), matching `add-to-project.yml`'s own `issues`-only gate (see
  below) — otherwise this UI-only path can still add stray PR cards that no
  code path will ever classify.
- **Item added → Status: Backlog** — *(optional; the hourly sync now defaults
  any status-less item to Backlog)* enable in the UI too if you want it to
  happen instantly rather than on the next sync.
- **Item closed → Status: Done/Released** is intentionally **not** enabled:
  `org-project-sync.yml` is the sole source of truth for both transitions
  (closed-with-no-shippable-PR → `Done`; a linked PR actually reaching main →
  `Released`) — a competing UI automation writing the same field would race
  it and could set the wrong one (e.g. `Done` for an issue whose linked PR
  hasn't shipped yet).
- **Auto-archive items** — *(UI-only; no API)* archived after e.g. 30 days
  closed. Recommended specifically to clear out legacy PR-content items left
  over from before this redesign (see "How Status is derived" above).

## Enabling the automated sync

`org-project-sync.yml` reads issues (and their linked PRs) with a scoped
CI-Bot App token and writes org-Project fields; `GITHUB_TOKEN` is retained
with `contents: read` but cannot write org Projects. The App token is
restricted to `CognitiveSystems`, `MediaRefinery`, `ModelDeck`, `Uploadarr`,
`HomeAssistant`, and `ARCRunner`, with pull-requests read, issues read,
contents read, and organization-projects write.

The sweep is issue-driven: for every Project item that is an **Issue**, it
resolves the issue's linked pull request(s) and derives Status per the table
above — see "How Status is derived." `On Dev` vs. `Released` for a PR merged
to `dev` is resolved by comparing its merge commit against `main`'s current
tip via the GitHub compare API (reachable-from-tip, not exact ancestry to the
latest tag — see `#52` in the workflow's own comments for why): a merge
commit at or behind `main`'s tip is `Released`, otherwise `On Dev`.

A Project item that is a **pull request** (a legacy card from before this
redesign) is left fully untouched — see "Legacy PR cards" above.

Before it will run:

1. Grant the **CI-Bot GitHub App** the org permission
   `organization_projects: write` (Settings → GitHub Apps → CI-Bot → Permissions),
   and accept the permission update for the org install.
2. Store `CI_BOT_APP_ID` and `CI_BOT_APP_PRIVATE_KEY` as repo secrets on `.github` (or as
   selected organization secrets reachable from it). `org-project-sync.yml` reads them
   directly by these exact (uppercase) names — it is triggered by `workflow_dispatch`/
   `schedule`, not `workflow_call`, so no secret-name aliasing is involved here (that only
   applies to `add-to-project.yml`'s reusable-workflow `secrets:` input names — see "Per-repo
   intake" below).
3. Run **Org Project Sync** manually with `dry_run: true` first. Manual dry runs never
   mutate Project items; set `dry_run: false` only after reviewing the summary. The hourly
   schedule event runs in mutation mode automatically. The summary reports issues scanned,
   non-issue (legacy PR) items, linked PRs resolved, would-update/actual-updated/
   already-correct counts, target-stage buckets (including `Done`), and regressions
   suppressed. It does not post comments.
4. Rotate or revoke credentials by revoking the old App key, replacing the local secret
   value, and repeating the dry run. Never print or commit secret values.

A manual `write_probe: true` dispatch runs only a self-contained write test — it creates
a temporary draft item, sets and verifies its Status, then deletes it — and skips the
reconciliation sweep entirely; use it to confirm write access before a real run. The
probe always mutates (its whole point is a write test), so it overrides `dry_run`.

The `schedule:` block is active: the sweep runs hourly (`cron: "17 * * * *"`) in mutation
mode. `workflow_dispatch` remains for manual dry-runs, write probes, and troubleshooting.

## Per-repo intake (`add-to-project.yml`)

`org-project-sync.yml` reconciles `Status` on a schedule; it does not itself add new
items to the Project. Intake is event-driven: the reusable `add-to-project.yml`
workflow that each repo calls. It mints a CI-Bot App token scoped to the
calling repo only (`organization-projects: write`, plus `issues: read` and
`pull-requests: read` so `actions/add-to-project` can resolve the triggering
item) and adds the triggering **issue** to Project #1.

**Issue-centric gate:** the `add` job requires `github.event_name ==
'issues'` — a consumer wrapper's `pull_request` trigger (kept for
back-compat; existing wrappers still send both) is a harmless no-op rather
than adding a second, separate PR card. `github.event_name` reflects the
*calling* workflow's original trigger event, not `workflow_call` itself, so
this correctly distinguishes the two triggers even though both share this one
reusable workflow.

> **Rollout note:** this gate lands in the reusable workflow at its
> unreleased tip. Every consumer pins `@v1`, so **a `v1` tag advance is
> required** before any consumer actually stops adding PR cards — until then,
> existing `@v1` callers keep their pre-redesign behavior unchanged (which is
> also why this is a safe, backward-compatible default: the gate is additive,
> nothing existing breaks either way).

Each consumer repo adds a thin caller in its own `.github/workflows/`:

```yaml
# .github/workflows/add-to-project.yml (consumer repo)
on:
  issues:
    types: [opened, transferred]
  pull_request:
    types: [opened]

jobs:
  add:
    uses: automationnexus/.github/.github/workflows/add-to-project.yml@v1
    secrets:
      ci-bot-app-id: ${{ secrets.CI_BOT_APP_ID }}
      ci-bot-app-private-key: ${{ secrets.CI_BOT_APP_PRIVATE_KEY }}
```

No change is required to this consumer-side wrapper — the `pull_request`
trigger it still sends is exactly what the reusable workflow's gate now
no-ops on.

## Area/Type auto-fill

The same sweep also fills the **Area/Type** field on each **issue** item from
its labels (`bug`→`bug`, `enhancement`→`feature`, `documentation`→`docs`,
`security`→`security`, `chore`→`chore`) whenever it is currently unset — it
never overrides a manually-set value. This is an enhancement, not core: if
the board has no Area/Type field, the pass is skipped entirely and the rest
of the sync still runs normally. Legacy PR-content items are out of scope for
this pass too, same as for Status.

Coverage note: issues in **private** repos (e.g. HomeAssistant) are only
reachable once the **CI-Bot App is granted `Issues: read`** (it currently is
not), so until then those items are left for manual triage. Granting that
permission is the only step needed — the workflow already requests
`permission-issues: read` on its token.

## Weekly digest

`.github/workflows/board-digest.yml` runs Monday mornings (cron `23 8 * * 1`, plus
manual dispatch) and finds-or-creates a single `.github` tracking issue titled
"📊 Delivery digest," replacing its body each run with current Status counts
(now including `Done`), in-flight item ages, and releases from the last 7
days — plus a reconciliation line showing non-issue (legacy PR) items and
issues with no/unrecognized Status, so the printed counts always sum to the
real board population. It never opens a second issue — the stable title is
the lookup key — and it reads the board with a read-only CI-Bot App token
while writing the issue with `GITHUB_TOKEN`. The digest no longer has a
Track-based "at risk" section — `Track` was dropped from the board's field
set in the issue-centric redesign.
