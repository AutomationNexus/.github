# Delivery board quickstart

**Board:** <https://github.com/orgs/AutomationNexus/projects/1> — the single
org-wide Project (`AutomationNexus — Delivery`). **Issues are the cards.** A
pull request never gets its own card — open the issue it closes and check its
built-in **Linked pull requests** field to see the PR(s) behind it; the
issue's **Status** is derived from those linked PR(s) automatically. Full
field/automation reference: [`org-project.md`](org-project.md). Live snapshot
from the CLI/agent side: `/board-status` (see below).

## The 3 saved views

| View | Layout | Use it for |
|---|---|---|
| Board — Ongoing work *(default)* | Board, grouped by Status | Day-to-day "what's moving" glance |
| By Repo | Table, grouped by Repository | Per-repo load / cross-repo comparison |
| Release pipeline | Table, filtered to On Dev/Promote Pending/Released, grouped by Repository | What's about to ship, per repo |

## Status pipeline

`Backlog → In Progress → In Review → On Dev → Promote Pending → Released`,
plus `Done` (a closed issue with no versioned release — e.g. a decision, a
docs-only fix, wontfix) and a manual-only `Blocked` state that sits outside
the forward flow.

- **Backlog** — not started / open with no classifiable linked PR yet.
- **In Progress** — actively being worked (set by hand; nothing derives this
  one automatically from a PR state).
- **In Review** — the issue has an open PR against `dev` (or `main`, for
  repos with no `dev`).
- **On Dev** — the issue's PR merged to `dev`, not yet released to `main`.
- **Promote Pending** — a dev→main promote PR is open for the issue's repo.
- **Released** — the issue's linked PR's merge commit is reachable from
  `main`'s current tip (or `main` HEAD directly, for repos with no version
  tags/no `dev`).
- **Done** — the issue is closed and none of its linked PRs reached a
  shippable stage (or it has no linked PR at all) — a completed deliverable
  that isn't a versioned release.
- **Blocked** — manual only; never set or cleared automatically.

**`In Review → On Dev → Promote Pending → Released`, and closed→`Done`, are
all automated hourly** (the `org-project-sync.yml` cron sweep), computed from
each issue's linked pull request(s) — see [`org-project.md`](org-project.md)
for exactly how a linked PR's state maps to a stage. Status only ever
**advances**, never regresses, and never touches `Blocked` or an item already
at `Released`. `Done` can still advance to `Released` later (that's a
correction, e.g. a PR merges after the issue was already closed as `Done`),
but nothing downgrades a `Done` back down the ordinary pipeline.

If an issue's Status isn't moving the way you expect, check that its PR is
actually **linked** to it (a closing keyword like `Fixes #123` in the PR
body/description, or a manual link in the issue sidebar) — an unlinked PR is
invisible to the sync no matter how far along it is.

## Automated for you vs. set by hand

**Automated:**

- Intake — each repo's `add-to-project.yml` caller adds new **issues** to the
  board on open (PRs are intentionally not added as separate cards).
- New issue defaults to **Backlog** if it has no Status yet.
- The Status pipeline transitions above, derived from linked PRs.
- **Area/Type** filled from the issue's labels (`bug`→bug,
  `enhancement`→feature, `documentation`→docs, `security`→security,
  `chore`→chore) — only when unset, never overriding a manual value.
- The weekly **"📊 Delivery digest"** tracking issue (Monday mornings).

**Set by hand (humans, in the UI):**

- **Area/Type**, if the issue has none of the labels above.
- **Blocked**, and clearing it again once unblocked.
- Optionally, an **Iteration**/sprint assignment (native GitHub field, not
  required by anything above).

## Triaging a new item (checklist)

1. If the issue has no `bug`/`enhancement`/`documentation`/`security`/`chore`
   label, set **Area/Type** manually.
2. When you open the fixing PR, link it to the issue (a closing keyword, or a
   manual link) so the board can actually see it and derive Status.
3. If work is genuinely blocked, set **Blocked** by hand; clear it yourself
   once it isn't anymore.

## More

- Live delivery-board summary any time: `/board-status` (dispatches
  `org-inspector`, read-only — query only, never writes Project fields).
- Weekly rollup: the **"📊 Delivery digest"** issue in `.github` (Status
  counts including `Done`, in-flight item ages, last-7-days releases, and a
  reconciliation count of any non-issue legacy items still on the board).
- Full field list, automation internals, derived-status table, and
  rollout/credential details: [`org-project.md`](org-project.md).
