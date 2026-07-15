# Org-wide delivery board (GitHub Project)

`AutomationNexus — Delivery` is the single org-level Project v2 that aggregates
Issues and PRs from every repo into one board / table / roadmap.

- **Project:** <https://github.com/orgs/AutomationNexus/projects/1>
- **Why one project (not one per repo):** GitHub has no org-wide rollup across
  multiple Projects. A single Project + the built-in `Repository` field gives a
  true cross-repo view; per-repo projects would not.

## What is codified vs. UI-only

| Layer | Owned by | Notes |
|-------|----------|-------|
| Custom fields + Status stages | `scripts/bootstrap-org-project.sh` | Idempotent; re-runnable source of truth for the board's shape |
| Items (Status of open and merged PRs) | `.github/workflows/org-project-sync.yml` | Runs hourly (cron `:17`) plus manual dispatch |
| Item intake | Per-repo **auto-add** workflow | UI-only toggle (see below) |
| Saved views, native **Iteration** field | Humans, in the UI | The GitHub API cannot create these |

## Fields

Built-in `Status` is reshaped into the delivery pipeline; the rest are custom:

- **Status** (pipeline): `Backlog · In Progress · In Review · On Dev · Promote Pending · Released · Blocked`
- **Area/Type**: `feature · bug · chore · release · platform · security · docs`
- **Bump type**: `patch · minor · major · none · n-a` (only meaningful for the 6 auto-versioning repos)
- **Release target** (text) · **Priority** (`P0–P3`) · **Track** (`On track · At risk · Off track`)
- **Start date** / **Target date** (feed the roadmap)
- **Iteration** — add manually (API cannot create iteration fields): Project → **+** new field → Iteration, weekly.

## Saved views to create (UI, ~2 min)

Open the Project, use the **＋** next to the view tabs. For each: pick the layout,
then set grouping/filter via the view's **⋯** menu.

1. **Board — Ongoing work** *(default)* — layout **Board**, group by **Status**.
2. **By Repo** — layout **Table**, group by **Repository**.
3. **Roadmap** — layout **Roadmap**, set date fields to **Start date → Target date**, marker on **Iteration**, zoom **Month**.
4. **Release pipeline** — layout **Table**, filter `status:"On Dev","Promote Pending","Released"`, group by **Repository**.
5. **Current sprint** — layout **Board**, filter `iteration:@current`, group by **Status**.
6. **At risk** — layout **Table**, filter `-track:"On track"`.
7. **Security / audits** — layout **Table**, filter `area-type:security` (add `,label:security` to include labelled items).

## Workflow toggles (UI, Project → ⋯ → Workflows)

Two of these are already handled in code and are **optional** as UI toggles:

- **Auto-add to project** — *(optional; covered by the `add-to-project.yml` caller in every repo)* enable per repo as a UI backstop if desired (filter `is:issue,pr is:open`).
- **Item added → Status: Backlog** — *(optional; the hourly sync now defaults any status-less item to Backlog)* enable in the UI too if you want it to happen instantly rather than on the next sync.
- **Item closed → Status: Released** is intentionally not enabled: closing a feature PR merged into `dev` does not mean the change was released to `main`.
- **Auto-archive items** — *(UI-only; no API)* archived after e.g. 30 days closed.

## Enabling the automated sync

`org-project-sync.yml` reads PRs with a scoped CI-Bot App token and writes org-Project
fields; `GITHUB_TOKEN` is retained with `contents: read` but cannot write org Projects.
The App token is restricted to `CognitiveSystems`, `MediaRefinery`, `ModelDeck`, `Uploadarr`,
and `HomeAssistant`, with pull-requests read, contents read, and organization-projects
write. The `contents: read` grant (added alongside the On Dev/Released reconciliation
below) is read-only widening for the REST tag-listing and compare calls; it does not
add any new write scope.

The sweep is item-driven: for every Project item linked to a pull request in scope
(same-org, non-cross-repository, one of the five synced repos) it classifies the PR's
GraphQL `state`/`baseRefName`/`headRefName` into `In Review`, `Promote Pending`, `On
Dev`, or `Released`. `On Dev` vs. `Released` for a PR merged to `dev` is resolved by
comparing its merge commit against the newest semantic-version tag reachable from
`main` (or `main`'s HEAD sha for `HomeAssistant`, which has no version tags) via the
GitHub compare API; a merge commit at or behind that ref is `Released`, otherwise `On
Dev`. Status only ever advances forward through `Backlog → In Progress → In Review →
On Dev → Promote Pending → Released` — the sweep never downgrades a status and never
touches `Blocked` or items already `Released` (both are treated as manual-only). A
pull request that is merged directly into `main` (for example, a completed promote
PR) is deliberately left unclassified: its `dev`-side item already advances to
`Released` once that same merge commit is reachable from the release ref, so no
separate `main`-merge transition is needed. Any REST/compare error for a given PR
fails open to `On Dev` and is counted, rather than aborting the sweep.

The previous open-PR REST sweep still runs, but only as an independent, detect-only
cross-check now: it flags a `cross_check_mismatch` when its own `In
Review`/`Promote Pending` expectation disagrees with what the item-driven pass
concluded, but it no longer writes Project fields itself.

Before it will run:

1. Grant the **CI-Bot GitHub App** the org permission
   `organization_projects: write` (Settings → GitHub Apps → CI-Bot → Permissions),
   and accept the permission update for the org install.
2. Store `CI_BOT_APP_ID` and `CI_BOT_APP_PRIVATE_KEY` as repo secrets on `.github` or as
   selected organization secrets. These uppercase stored names may be mapped to lowercase
   reusable-workflow aliases by callers; they refer to the same credentials.
3. Run **Org Project Sync** manually with `dry_run: true` first. Manual dry runs never
   mutate Project items; set `dry_run: false` only after reviewing the summary. The hourly
   schedule event runs in mutation mode automatically. The summary reports scanned repos,
   up to 1,000 open PRs/candidates per repository, would-update, actual updated,
   already-correct, missing Project item, and skipped/out-of-scope counts. The workflow
   skips cross-repository or non-`AutomationNexus` PRs. It does not post comments.
4. Rotate or revoke credentials by revoking the old App key, replacing the local secret
   value, and repeating the dry run. Never print or commit secret values.

A manual `write_probe: true` dispatch runs only a self-contained write test — it creates
a temporary draft item, sets and verifies its Status, then deletes it — and skips the
reconciliation sweep entirely; use it to confirm write access before a real run. The
probe always mutates (its whole point is a write test), so it overrides `dry_run`.

The `schedule:` block is active: the sweep runs hourly (`cron: "17 * * * *"`) in mutation
mode. `workflow_dispatch` remains for manual dry-runs, write probes, and troubleshooting.

## Staleness -> At risk

The same sweep flags stale in-scope PR items by setting **Track** to `At risk`:
`In Review` past 7 days (from PR `createdAt`), `Promote Pending` past 3 days (from
PR `createdAt`), `On Dev` past 5 days (from PR `mergedAt`). It only touches items
whose Track is unset or already `On track` — it never overrides a manually-set
`Off track` or `At risk`, and it never sets `On track`. This is optional: if the
board has no Track field, the pass is skipped entirely.

## Per-repo intake (`add-to-project.yml`)

`org-project-sync.yml` reconciles `Status` on a schedule; it does not itself add new
items to the Project. Intake is handled two ways (belt-and-suspenders): the UI-only
**Auto-add to project** workflow toggle (see above), and the reusable
`add-to-project.yml` workflow that each repo calls. The reusable workflow mints a
CI-Bot App token scoped to the calling repo only (`organization-projects: write`, plus
`issues: read` and `pull-requests: read` so `actions/add-to-project` can resolve the
triggering item) and adds the triggering issue/PR to Project #1.

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

## Area/Type auto-fill

The same sweep also fills the **Area/Type** field from each linked issue/PR's labels
(`bug`→`bug`, `enhancement`→`feature`, `documentation`→`docs`, `security`→`security`,
`chore`→`chore`) whenever it is currently unset — it never overrides a manually-set
value. This is an enhancement, not core: if the board has no Area/Type field, the pass
is skipped entirely and the rest of the sync still runs normally.

Coverage note: it fills Area/Type for **PRs** (all synced repos) and for **issues in
public repos**. Issues in **private** repos (e.g. HomeAssistant) are only reachable once
the **CI-Bot App is granted `Issues: read`** (it currently is not), so until then those
items are left for manual triage. Granting that permission is the only step needed —
the workflow already requests `permission-issues: read` on its token.

## Weekly digest

`.github/workflows/board-digest.yml` runs Monday mornings (cron `23 8 * * 1`, plus
manual dispatch) and finds-or-creates a single `.github` tracking issue titled
"📊 Delivery digest," replacing its body each run with current Status/Track counts,
in-flight item ages, at-risk items, and releases from the last 7 days. It never
opens a second issue — the stable title is the lookup key — and it reads the board
with a read-only CI-Bot App token while writing the issue with `GITHUB_TOKEN`.
