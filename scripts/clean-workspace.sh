#!/usr/bin/env bash
# Prune merged-work leftovers from the AutomationNexus workspace-root clones.
#
# Over time, agent/human sessions finish the feature-branch -> PR -> merge flow
# but leave local git state behind: harness worktree-isolation sandboxes under
# <repo>/.claude/worktrees/ (auto-removed ONLY if unchanged -- so any that did
# real work leak forever), merged-and-remote-deleted local branches, and main
# checkouts left parked on a branch whose PR already merged. Stale local state
# is a collision-protocol hazard: another session can misread it as active work.
# This script sweeps every clone under the workspace root and removes ONLY the
# provably-merged leftovers, never anything with live work.
#
# A leftover is "provably merged" (safe to prune) when EITHER:
#   * its tip commit is an ancestor of origin/dev, origin/main, or origin/master
#     (catches fast-forward / rebase merges), OR
#   * `gh` reports a MERGED PR whose head is that branch (catches squash merges,
#     where the pre-squash commits are NOT ancestors of the base).
# Anything else -- uncommitted changes, unpushed commits with no merged PR, or an
# OPEN PR -- is KEPT and reported, never touched.
#
# The workspace root is NOT a git repository, so this operates on the sibling
# clones directly; nothing is pushed.
#
# Usage:
#   scripts/clean-workspace.sh            # DRY RUN: report what would be pruned; no changes
#   scripts/clean-workspace.sh --check    # same as bare (explicit dry run)
#   scripts/clean-workspace.sh --prune    # actually remove the provably-merged leftovers
#
# gh is optional: without it (or unauthenticated), squash-merged branches that
# aren't ancestors of a base can't be confirmed merged, so they are conservatively
# KEPT and reported -- the script never guesses a branch is merged.
set -euo pipefail
# The .github clone is a dot-directory; without dotglob the `*/` sweep below would
# silently skip it (and any other dot-named clone). nullglob avoids a literal `*/`.
shopt -s dotglob nullglob

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE_ROOT="$(cd "${REPO_DIR}/.." && pwd)"
ORG="AutomationNexus"

# Sanity: refuse to touch anything unless the parent dir looks like the org workspace.
for expected in CognitiveSystems MediaRefinery ModelDeck Uploadarr; do
  if [ ! -d "${WORKSPACE_ROOT}/${expected}" ]; then
    echo "ERROR: ${WORKSPACE_ROOT} does not look like the ${ORG} workspace root" >&2
    echo "       (missing ${expected}/). Refusing to touch anything." >&2
    exit 1
  fi
done

MODE="${1:---check}"
case "$MODE" in
  --check|--prune) ;;
  *) echo "usage: $0 [--check|--prune]" >&2; exit 2 ;;
esac

HAVE_GH=0
if command -v gh >/dev/null 2>&1 && gh auth status >/dev/null 2>&1; then HAVE_GH=1; fi

PROTECTED_RE='^(dev|main|master)$'
would=0   # count of prunable leftovers found
acted=0   # count actually pruned
kept=0    # count kept for review

log()  { printf '%s\n' "$*"; }
note() { printf '    %s\n' "$*"; }

# echo the base ref that contains $tip, or empty if none
contained_in_base() {
  local repo="$1" tip="$2" base
  for base in origin/dev origin/main origin/master; do
    git -C "$repo" show-ref --verify --quiet "refs/remotes/$base" 2>/dev/null || continue
    if git -C "$repo" merge-base --is-ancestor "$tip" "$base" 2>/dev/null; then
      printf '%s' "$base"; return 0
    fi
  done
  return 1
}

# 0 = branch is provably merged; 1 = not provable (keep)
branch_is_merged() {
  local repo="$1" br="$2" tip
  tip="$(git -C "$repo" rev-parse "$br" 2>/dev/null)" || return 1
  contained_in_base "$repo" "$tip" >/dev/null && return 0
  if [ "$HAVE_GH" -eq 1 ]; then
    gh pr list --repo "${ORG}/${repo##*/}" --head "$br" --state merged \
      --json number --jq '.[0].number' 2>/dev/null | grep -q '[0-9]' && return 0
  fi
  return 1
}

# default target branch for a repo: dev if it exists on origin, else main, else master
default_base_branch() {
  local repo="$1"
  for b in dev main master; do
    git -C "$repo" show-ref --verify --quiet "refs/remotes/origin/$b" 2>/dev/null && { printf '%s' "$b"; return; }
  done
  printf 'main'
}

log "clean-workspace: mode=${MODE}  root=${WORKSPACE_ROOT}  gh=$([ $HAVE_GH -eq 1 ] && echo yes || echo no)"
log ""

for path in "${WORKSPACE_ROOT}"/*/; do
  repo="${path%/}"; name="$(basename "$repo")"
  [ -d "${repo}/.git" ] || continue
  git -C "$repo" fetch origin --quiet 2>/dev/null || true
  header_printed=0
  # Must return 0 even when already printed -- it's called as a bare statement
  # under `set -e`, so a non-zero return would abort the whole sweep.
  header() { if [ "$header_printed" -eq 0 ]; then log "== ${name} =="; header_printed=1; fi; return 0; }

  # 1) Agent worktrees under .claude/worktrees/ whose branch is merged and clean.
  while IFS= read -r wt; do
    [ -n "$wt" ] || continue
    case "$wt" in *"/.claude/worktrees/"*) ;; *) continue ;; esac
    wbr="$(git -C "$wt" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
    if [ -n "$(git -C "$wt" status --porcelain 2>/dev/null)" ]; then
      header; note "KEEP worktree ${wt##*/} [${wbr}] -- uncommitted changes"; kept=$((kept+1)); continue
    fi
    if branch_is_merged "$repo" "$wbr"; then
      header; would=$((would+1))
      if [ "$MODE" = "--prune" ]; then
        git -C "$repo" worktree remove --force "$wt" 2>/dev/null && { note "removed worktree ${wt##*/} [${wbr}]"; acted=$((acted+1)); } \
          || note "FAILED to remove worktree ${wt##*/}"
      else
        note "would remove worktree ${wt##*/} [${wbr}] (merged)"
      fi
    else
      header; note "KEEP worktree ${wt##*/} [${wbr}] -- not provably merged"; kept=$((kept+1))
    fi
  done < <(git -C "$repo" worktree list --porcelain 2>/dev/null | awk '/^worktree /{print $2}')
  [ "$MODE" = "--prune" ] && git -C "$repo" worktree prune 2>/dev/null || true

  # 2) Re-point a main checkout parked on a merged (non-protected) branch.
  cur="$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  if ! echo "$cur" | grep -qE "$PROTECTED_RE"; then
    if [ -n "$(git -C "$repo" status --porcelain 2>/dev/null)" ]; then
      header; note "KEEP checkout on [${cur}] -- working tree dirty (not re-pointing)"; kept=$((kept+1))
    elif branch_is_merged "$repo" "$cur"; then
      base="$(default_base_branch "$repo")"; header; would=$((would+1))
      if [ "$MODE" = "--prune" ]; then
        git -C "$repo" switch "$base" 2>/dev/null || git -C "$repo" switch -c "$base" --track "origin/$base" 2>/dev/null
        git -C "$repo" merge --ff-only "origin/$base" >/dev/null 2>&1 || true
        note "re-pointed checkout [${cur}] -> ${base}"; acted=$((acted+1))
      else
        note "would re-point checkout [${cur}] -> ${base} (merged)"
      fi
    else
      header; note "KEEP checkout on [${cur}] -- not provably merged (active work?)"; kept=$((kept+1))
    fi
  fi

  # 3) Delete non-protected local branches that are provably merged and not checked out.
  cur="$(git -C "$repo" rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
  while IFS= read -r br; do
    [ -n "$br" ] || continue
    echo "$br" | grep -qE "$PROTECTED_RE" && continue
    [ "$br" = "$cur" ] && continue                      # never delete the checked-out branch
    git -C "$repo" worktree list --porcelain 2>/dev/null | grep -q "branch refs/heads/$br$" && continue
    if branch_is_merged "$repo" "$br"; then
      header; would=$((would+1))
      if [ "$MODE" = "--prune" ]; then
        git -C "$repo" branch -D "$br" >/dev/null 2>&1 && { note "deleted branch ${br}"; acted=$((acted+1)); } \
          || note "FAILED to delete branch ${br}"
      else
        note "would delete branch ${br} (merged)"
      fi
    else
      header; note "KEEP branch ${br} -- not provably merged (active work?)"; kept=$((kept+1))
    fi
  done < <(git -C "$repo" for-each-ref --format='%(refname:short)' refs/heads 2>/dev/null)
done

log ""
if [ "$MODE" = "--prune" ]; then
  log "clean-workspace: pruned ${acted} leftover(s); kept ${kept} for review."
else
  log "clean-workspace: ${would} leftover(s) would be pruned; ${kept} kept for review."
  [ "$would" -gt 0 ] && log "Re-run with --prune to remove them."
fi
exit 0
