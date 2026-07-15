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

- **Auto-add to project** — enable one per repo (filter `is:issue,pr is:open`), for all 12 repos.
- **Item added → Status: Backlog**
- **Item closed → Status: Released** is intentionally not enabled: closing a feature PR merged into `dev` does not mean the change was released to `main`.
- **Auto-archive items** — archived after e.g. 30 days closed.

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
