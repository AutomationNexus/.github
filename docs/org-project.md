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
| Items (Status of open PRs) | `.github/workflows/org-project-sync.yml` | Manual-dispatch until the App permission below is granted |
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
- **Item closed → Status: Released** *(note: also fires for feature PRs merged into `dev`; the sync workflow corrects those on its next run)*
- **Auto-archive items** — archived after e.g. 30 days closed.

## Enabling the automated sync

`org-project-sync.yml` writes org-Project fields from Actions, which
`GITHUB_TOKEN` cannot do. Before it will run:

1. Grant the **CI-Bot GitHub App** the org permission
   `organization_projects: write` (Settings → GitHub Apps → CI-Bot → Permissions),
   and accept the permission update for the org install.
2. Trigger one manual run (Actions → **Org Project Sync** → Run workflow) and
   confirm it updates Status without error.
3. Uncomment the `schedule:` block in the workflow to make it hands-off.
