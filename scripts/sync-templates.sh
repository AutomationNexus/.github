#!/usr/bin/env bash
# Resync all 5 template-* repos from templates/_shared/ (base layer, every group) +
# templates/<group>/ (group-specific overlay) -- together the canonical starter bundles.
# Run this after ANY change under templates/ -- the template repos do NOT auto-sync.
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
SHARED="${TEMPLATES_DIR}/_shared"
WORK_DIR="$(mktemp -d)"
# `|| true`: on Windows, a git/gh subprocess can still hold a file handle open in
# $WORK_DIR for a moment after this script's own work is done, making `rm -rf` fail here.
# Since this is an EXIT trap, an unhandled failure here would silently become the whole
# script's reported exit code even though the actual sync work already succeeded.
trap 'rm -rf "$WORK_DIR" 2>/dev/null || true' EXIT

group_repo() {
  case "$1" in
    A) echo "template-python-docker" ;;
    B) echo "template-python-pypi" ;;
    C) echo "template-docker-ha-addon" ;;
    D) echo "template-infra-main-only" ;;
    E) echo "template-ha-config" ;;
    *) echo "unknown group: $1" >&2; exit 1 ;;
  esac
}

group_dir() {
  case "$1" in
    A) echo "A-python-docker" ;;
    B) echo "B-python-pypi" ;;
    C) echo "C-docker-ha-addon" ;;
    D) echo "D-infra-main-only" ;;
    E) echo "E-ha-config" ;;
  esac
}

# Copy a file if it exists at $1, to destination $2 (creating parent dirs).
copy_file() {
  local src="$1" dest="$2"
  if [ -f "$src" ]; then
    mkdir -p "$(dirname "$dest")"
    cp "$src" "$dest"
  fi
}

# Copy a directory's contents if it exists at $1, into destination $2.
copy_dir() {
  local src="$1" dest="$2"
  if [ -d "$src" ]; then
    mkdir -p "$dest"
    cp -r "${src}/." "${dest}/"
  fi
}

# NOTE: do not name this GROUPS -- bash reserves that as a builtin special variable
# (the invoking user's group IDs) and silently ignores assignments to it.
# Accept either no args (all 5), or one-or-more space-separated group letters as
# separate argv entries (e.g. `sync-templates.sh A B D`) -- NOT a single quoted string.
if [ "$#" -eq 0 ]; then
  TARGET_GROUPS=(A B C D E)
else
  TARGET_GROUPS=("$@")
fi

for GROUP in "${TARGET_GROUPS[@]}"; do
  REPO_NAME="$(group_repo "$GROUP")"
  REPO="AutomationNexus/${REPO_NAME}"
  DIR_NAME="$(group_dir "$GROUP")"
  SRC="${TEMPLATES_DIR}/${DIR_NAME}"
  echo "==> Syncing group ${GROUP} -> ${REPO}"

  CLONE_DIR="${WORK_DIR}/${GROUP}"
  gh repo clone "$REPO" "$CLONE_DIR" -- --quiet

  # ---- 1. _shared/ base layer (every group gets this) ----
  copy_file "${SHARED}/gitignore" "${CLONE_DIR}/.gitignore"
  copy_dir  "${SHARED}/githooks" "${CLONE_DIR}/.githooks"
  copy_dir  "${SHARED}/tools" "${CLONE_DIR}/tools"
  copy_file "${SHARED}/dev-only-paths" "${CLONE_DIR}/.github/dev-only-paths"
  # Claude Code seed: generic settings.json baseline for every group. Each group's own
  # real CLAUDE.md + .claude/agents/commands are copied below in the group overlay step
  # (CLAUDE.md.template in _shared/ is reference-only, not copied as a live file).
  copy_file "${SHARED}/.claude/settings.json.template" "${CLONE_DIR}/.claude/settings.json"

  # ---- 2. group-specific overlay (canonical starter bundle, wins on conflicts) ----
  copy_dir  "${SRC}/.github" "${CLONE_DIR}/.github"
  copy_file "${SRC}/README.md" "${CLONE_DIR}/README.md"
  copy_file "${SRC}/CLAUDE.md" "${CLONE_DIR}/CLAUDE.md"
  copy_dir  "${SRC}/.claude" "${CLONE_DIR}/.claude"
  copy_dir  "${SRC}/tools" "${CLONE_DIR}/tools"
  copy_file "${SRC}/pyproject.toml" "${CLONE_DIR}/pyproject.toml"
  copy_file "${SRC}/Dockerfile" "${CLONE_DIR}/Dockerfile"
  copy_file "${SRC}/.dockerignore" "${CLONE_DIR}/.dockerignore"
  copy_dir  "${SRC}/src" "${CLONE_DIR}/src"
  copy_dir  "${SRC}/tests" "${CLONE_DIR}/tests"
  copy_file "${SRC}/mkdocs.yml" "${CLONE_DIR}/mkdocs.yml"
  copy_dir  "${SRC}/docs" "${CLONE_DIR}/docs"
  copy_file "${SRC}/configuration.yaml" "${CLONE_DIR}/configuration.yaml"
  copy_file "${SRC}/automations.yaml" "${CLONE_DIR}/automations.yaml"
  copy_file "${SRC}/scripts.yaml" "${CLONE_DIR}/scripts.yaml"
  copy_file "${SRC}/scenes.yaml" "${CLONE_DIR}/scenes.yaml"
  copy_file "${SRC}/secrets.yaml.example" "${CLONE_DIR}/secrets.yaml.example"
  copy_file "${SRC}/.yamllint.yml" "${CLONE_DIR}/.yamllint.yml"

  find "${CLONE_DIR}" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
  find "${CLONE_DIR}" -name "*.egg-info" -type d -exec rm -rf {} + 2>/dev/null || true

  (
    cd "$CLONE_DIR"
    # NOTE: check the *staged* diff (git diff --cached), not `git status --porcelain`
    # on the working tree. On Windows, core.autocrlf normalizes LF -> CRLF on checkout,
    # so files with zero real content difference still show as "modified" in working-tree
    # status -- `git add -A` then stages them, but the resulting blob is identical to
    # HEAD's, so `git commit` correctly finds nothing to commit and exits non-zero,
    # which used to kill this whole script under `set -e` after processing only the
    # first affected group. Checking the index against HEAD avoids the false positive.
    git add -A
    if git diff --cached --quiet; then
      echo "    already in sync"
    else
      git commit -q -m "chore: resync from automationnexus/.github templates/_shared + ${DIR_NAME}"
      git push -q origin main
      echo "    pushed sync commit"
    fi
    exit 0
  )
done

echo "==> Done."
exit 0
