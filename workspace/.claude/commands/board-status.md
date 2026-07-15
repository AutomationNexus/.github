---
description: "Live delivery-board summary from org Project #1 (read-only)."
argument-hint: [optional repo name or Status to filter]
---

Dispatch `org-inspector` to query org Project #1 (`AutomationNexus — Delivery`) via
`gh api graphql` and return a compact summary: total items; counts by Status; counts by
Repository; in-flight items (`In Review` / `On Dev` / `Promote Pending`) as `repo#num`;
at-risk items (Track not "On track"); and items Released in the last 7 days. Filter to:
$ARGUMENTS (default: all items) — a repo name or a Status value.

Read-only — query only, never write Project fields or repo state.

This command is the delivery-board counterpart to `/org-status` (which covers repo/CI
state, not the Project board) — see `docs/board-guide.md` for the board's saved views,
Status pipeline, and what's automated vs. set by hand.
