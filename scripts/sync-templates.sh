#!/usr/bin/env bash
# Resync all 5 template-* repos from templates/<group>/ (the canonical starter bundles).
# Run this after ANY change to templates/<group>/ — the template repos do NOT auto-sync.
# This is what makes "templates are rebuilt from the canonical starter bundles" (see
# templates/README.md) actually true, instead of an aspirational doc line.
#
# Usage:
#   scripts/sync-templates.sh          # sync all 5 groups
#   scripts/sync-templates.sh C        # sync only group C
#
# Note: copies/overwrites files; does not delete a file from a template repo if it was
# removed from the source bundle (rare — handle that case manually if it happens).
#
# Requires: gh (authenticated, repo scope), git.
set -euo pipefail

TEMPLATES_DIR="$(cd "$(dirname "$0")/../templates" && pwd)"
WORK_DIR="$(mktemp -d)"
trap 'rm -rf "$WORK_DIR"' EXIT

group_repo() {
  case "$1" in
    A) echo "template-python-docker" ;;
    B) echo "template-python-pypi" ;;
    C) echo "template-ha-addon" ;;
    D) echo "template-infra-main-only" ;;
    E) echo "template-ha-config" ;;
    *) echo "unknown group: $1" >&2; exit 1 ;;
  esac
}

group_dir() {
  case "$1" in
    A) echo "A-python-docker" ;;
    B) echo "B-python-pypi" ;;
    C) echo "C-ha-addon" ;;
    D) echo "D-infra-main-only" ;;
    E) echo "E-ha-config" ;;
  esac
}

GROUPS="${1:-A B C D E}"

for GROUP in $GROUPS; do
  REPO_NAME="$(group_repo "$GROUP")"
  REPO="AutomationNexus/${REPO_NAME}"
  DIR_NAME="$(group_dir "$GROUP")"
  SRC="${TEMPLATES_DIR}/${DIR_NAME}"
  echo "==> Syncing group ${GROUP} -> ${REPO}"

  CLONE_DIR="${WORK_DIR}/${GROUP}"
  gh repo clone "$REPO" "$CLONE_DIR" -- --quiet

  cp -r "${SRC}/.github/." "${CLONE_DIR}/.github/"
  cp "${SRC}/README.md" "${CLONE_DIR}/README.md"
  if [ -d "${SRC}/tools" ]; then
    mkdir -p "${CLONE_DIR}/tools"
    cp -r "${SRC}/tools/." "${CLONE_DIR}/tools/"
  fi
  find "${CLONE_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

  (
    cd "$CLONE_DIR"
    if [ -z "$(git status --porcelain)" ]; then
      echo "    already in sync"
    else
      git add -A
      git commit -q -m "chore: resync from automationnexus/.github templates/${DIR_NAME}"
      git push -q origin main
      echo "    pushed sync commit"
    fi
  )
done

echo "==> Done."
