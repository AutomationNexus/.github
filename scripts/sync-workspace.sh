#!/usr/bin/env bash
# Sync the canonical workspace-root Claude Code layer (workspace/CLAUDE.md +
# workspace/.claude/) from this repo to the AutomationNexus workspace root -- the
# local directory that contains all the org repo clones. The workspace root is NOT
# a git repository, so this is a local copy, not a push. The canonical source is
# versioned HERE; never hand-edit the root copies (this script overwrites them).
#
# Usage:
#   scripts/sync-workspace.sh --check   # report drift between canonical and root; no changes
#   scripts/sync-workspace.sh           # copy; refuses if existing root copies have drifted
#   scripts/sync-workspace.sh --force   # copy even over drifted root copies (backup taken first)
#
# Before any overwrite, the current root CLAUDE.md/.claude are snapshotted to
# workspace/.backups/<UTC-stamp>/ (gitignored) -- nothing is ever lost.
#
# Note: copies/overwrites files; does not delete a root file that was removed from
# workspace/ (rare -- handle that manually if it happens).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SRC="${REPO_DIR}/workspace"
WORKSPACE_ROOT="$(cd "${REPO_DIR}/.." && pwd)"

# Sanity: refuse to touch anything unless the parent dir looks like the org workspace.
for expected in CognitiveSystems MediaRefinery ModelDeck Uploadarr; do
  if [ ! -d "${WORKSPACE_ROOT}/${expected}" ]; then
    echo "ERROR: ${WORKSPACE_ROOT} does not look like the AutomationNexus workspace root" >&2
    echo "       (missing ${expected}/). Refusing to touch anything." >&2
    exit 1
  fi
done

MODE="${1:-copy}"
case "$MODE" in
  --check|--force|copy) ;;
  *) echo "usage: $0 [--check|--force]" >&2; exit 2 ;;
esac

# Managed file list: everything under workspace/ except this repo's own docs/backups.
managed_files() {
  ( cd "$SRC" && find . -type f \
      ! -name 'README.md' \
      ! -path './.backups/*' \
      | sed 's|^\./||' )
}

DRIFTED=()
MISSING=()
while IFS= read -r rel; do
  dest="${WORKSPACE_ROOT}/${rel}"
  if [ ! -f "$dest" ]; then
    MISSING+=("$rel")
  elif ! diff -q "${SRC}/${rel}" "$dest" >/dev/null 2>&1; then
    DRIFTED+=("$rel")
  fi
done < <(managed_files)

if [ "${#DRIFTED[@]}" -gt 0 ]; then
  echo "Drift (root copy differs from canonical workspace/):"
  printf '  %s\n' "${DRIFTED[@]}"
fi
if [ "${#MISSING[@]}" -gt 0 ]; then
  echo "Missing at root (will be created on copy):"
  printf '  %s\n' "${MISSING[@]}"
fi
if [ "${#DRIFTED[@]}" -eq 0 ] && [ "${#MISSING[@]}" -eq 0 ]; then
  echo "Workspace root is in sync with workspace/."
  exit 0
fi

if [ "$MODE" = "--check" ]; then
  exit 1
fi

if [ "${#DRIFTED[@]}" -gt 0 ] && [ "$MODE" != "--force" ]; then
  echo "" >&2
  echo "Refusing to overwrite drifted root copies. If the drift is expected (the" >&2
  echo "canonical workspace/ changed), or the root was hand-edited and you accept" >&2
  echo "losing those edits (a backup is taken first), re-run with --force." >&2
  exit 1
fi

# Snapshot the current root copies before any overwrite.
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
BACKUP_DIR="${SRC}/.backups/${STAMP}"
mkdir -p "$BACKUP_DIR"
[ -f "${WORKSPACE_ROOT}/CLAUDE.md" ] && cp "${WORKSPACE_ROOT}/CLAUDE.md" "${BACKUP_DIR}/CLAUDE.md"
if [ -d "${WORKSPACE_ROOT}/.claude" ]; then
  mkdir -p "${BACKUP_DIR}/.claude"
  cp -r "${WORKSPACE_ROOT}/.claude/." "${BACKUP_DIR}/.claude/"
fi
echo "Backed up current root copies to workspace/.backups/${STAMP}/"

# Copy canonical -> root.
while IFS= read -r rel; do
  mkdir -p "$(dirname "${WORKSPACE_ROOT}/${rel}")"
  cp "${SRC}/${rel}" "${WORKSPACE_ROOT}/${rel}"
done < <(managed_files)

echo "Copied workspace/ -> ${WORKSPACE_ROOT}"
echo ""
echo "Reminder: the canonical source is .github/workspace/ (this repo). Changes to it"
echo "go through feature branch -> PR -> master; never hand-edit the root copies."
exit 0
