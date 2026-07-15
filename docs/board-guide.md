# Delivery board quickstart

**Board:** <https://github.com/orgs/AutomationNexus/projects/1> — the single
org-wide Project (`AutomationNexus — Delivery`) that rolls up Issues and PRs
from every repo into one board/table/roadmap. Full field/automation reference:
[`org-project.md`](org-project.md). Live snapshot from the CLI/agent side:
`/board-status` (see below).

## The 7 saved views

| View | Layout | Use it for |
|---|---|---|
| Board — Ongoing work *(default)* | Board, grouped by Status | Day-to-day "what's moving" glance |
| By Repo | Table, grouped by Repository | Per-repo load / cross-repo comparison |
| Roadmap | Roadmap (Start → Target date, Iteration marker) | Planning/scheduling, month zoom |
| Release pipeline | Table, filtered to On Dev/Promote Pending/Released, grouped by Repository | What's about to ship, per repo |
| Current sprint | Board, filtered to `iteration:@current`, grouped by Status | This sprint's work only |
| At risk | Table, filtered to `-track:"On track"` | Everything needing attention now |
| Security / audits | Table, filtered to `area-type:security` | Security-tagged work across repos |

## Status pipeline

`Backlog → In Progress → In Review → On Dev → Promote Pending → Released`,
plus a manual-only `Blocked` state that sits outside the forward flow.

- **Backlog** — not started.
- **In Progress** — actively being worked.
- **In Review** — open PR against `dev` (or `main` for repos with no `dev`).
- **On Dev** — PR merged to `dev`, not yet released to `main`.
- **Promote Pending** — a dev→main promote PR is open.
- **Released** — the change's merge commit is reachable from the latest
  release tag (or `main` HEAD, for repos with no version tags).
- **Blocked** — manual only; never set or cleared automatically.

**`In Review → On Dev → Released` transitions are automated, hourly** (the
`org-project-sync.yml` cron sweep). Status only ever advances forward — it
never downgrades a status and never touches `Blocked` or an item already
`Released`.

## Automated for you vs. set by hand

**Automated:**

- Intake — each repo's `add-to-project.yml` caller adds new issues/PRs to the
  board on open.
- New item defaults to **Backlog** if it has no Status yet.
- The Status pipeline transitions above (`In Review`/`On Dev`/`Released`).
- **Area/Type** filled from labels (`bug`→bug, `enhancement`→feature,
  `documentation`→docs, `security`→security, `chore`→chore) — only when unset,
  never overriding a manual value.
- **At-risk flagging** — Track is set to `At risk` for stale in-flight items:
  `In Review` past 7 days, `Promote Pending` past 3 days, `On Dev` past 5 days.
  Only touches items whose Track is unset or `On track` — never overrides a
  manually-set `Off track`/`At risk`, and never sets `On track` itself.
- The weekly **"📊 Delivery digest"** tracking issue (Monday mornings).

**Set by hand (humans, in the UI):**

- **Priority** (`P0`–`P3`).
- A manual **Track** override — set `On track` yourself, or set `Off track`
  when the automated `At risk` flag isn't the right call.
- **Start date** / **Target date** (feeds the Roadmap view).
- Assigning an item to an **Iteration**/sprint.

## Triaging a new item (checklist)

1. Set **Priority** (`P0`–`P3`).
2. If the linked issue/PR has no `bug`/`enhancement`/`documentation`/
   `security`/`chore` label, set **Area/Type** manually.
3. If it's part of the current sprint, add it to the active **Iteration**.
4. If it's roadmap-relevant, set **Start date**/**Target date**.

## More

- Live delivery-board summary any time: `/board-status` (dispatches
  `org-inspector`, read-only — query only, never writes Project fields).
- Weekly rollup: the **"📊 Delivery digest"** issue in `.github`
  (Status/Track counts, in-flight item ages, at-risk items, last-7-days
  releases).
- Full field list, automation internals, and rollout/credential details:
  [`org-project.md`](org-project.md).
