---
description: Prune merged-work git leftovers (stale worktrees, merged branches, parked checkouts) from the workspace-root clones.
argument-hint: "[--check | --prune]"
---

1. Run `scripts/clean-workspace.sh --check` (from the `.github` clone, Git Bash) and show
   the dry-run report: which stale worktrees, merged local branches, and parked checkouts
   *would* be pruned, and which are kept (active work / unmerged / open PR).
2. `--check` (the default) changes nothing. A worktree or branch is only ever listed as
   prunable when its tip is an ancestor of `origin/dev`/`main`/`master`, or `gh` reports a
   MERGED PR for it (squash-merge aware). Anything with uncommitted changes, unmerged
   commits with no merged PR, or an open PR is kept and reported — never touched.
3. To actually remove them, get explicit user confirmation first — this is destructive
   local cleanup (`human-confirmation-required` per `CLAUDE.md`'s "Unified authority and
   confirmation") — then run `scripts/clean-workspace.sh --prune` and report what was
   removed vs kept.
4. Never `--prune` as part of a status sweep or unprompted. The operation is local-only —
   it never pushes and never touches a protected trunk — but it does delete local branches
   and remove worktrees, so it stays behind an explicit confirmation.

Why this exists: the harness auto-removes an isolation worktree only when it is unchanged,
so any worktree that did real work leaks after its PR merges; sibling worktrees and merged
local branches leak the same way, and a clone can be left parked on an already-merged
branch. Stale local state is a collision-protocol hazard — another session can misread it
as active work — so run this after multi-agent sweeps. See `/org-status`, which surfaces
the same leftovers read-only.
