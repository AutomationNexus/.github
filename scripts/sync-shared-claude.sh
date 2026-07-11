#!/usr/bin/env bash
# Propagate the shared-core Claude Code layer (templates/_shared/.claude/agents +
# commands -- architect, qa-gatekeeper, reviewer, security-auditor, /execute, /qa,
# /prepush, /release) to the org's app repos.
#
# Unlike sync-templates.sh (direct push to the unprotected template repos), app repos
# have protected dev branches -- so this script pushes a FEATURE BRANCH and opens a PR
# to dev for each repo; auto-merge.yml takes it from there. Safe to run any time; repos
# already in sync produce no commit and no PR.
#
# Per-repo customization is preserved on merge: each target file keeps its own
# `description:` frontmatter line and everything below its `<!-- repo-specific -->`
# marker. Only the shared skeleton above the marker is refreshed.
#
# This script never touches: settings.json, domain-engineer agents, repo-specific
# commands, CLAUDE.md. ARCRunner is deliberately excluded (documented minimal-team
# exception -- see workspace/CLAUDE.md "Repo-tier standard").
#
# Usage:
#   scripts/sync-shared-claude.sh                  # all 5 target repos
#   scripts/sync-shared-claude.sh Uploadarr        # one repo
#
# Requires: gh (authenticated, repo scope), git.
set -euo pipefail

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SHARED_CLAUDE="${REPO_DIR}/templates/_shared/.claude"
WORK_DIR="$(mktemp -d)"
# `|| true`: see sync-templates.sh -- Windows can hold handles open briefly.
trap 'rm -rf "$WORK_DIR" 2>/dev/null || true' EXIT

repo_prefix() {
  case "$1" in
    CognitiveSystems) echo "cs" ;;
    MediaRefinery)    echo "mr" ;;
    ModelDeck)        echo "md" ;;
    Uploadarr)        echo "ua" ;;
    HomeAssistant)    echo "ha" ;;
    *) echo "unknown/unsupported target repo: $1" >&2; exit 1 ;;
  esac
}

# Paths relative to _shared/.claude/ on the source side and .claude/ on the target side.
SHARED_FILES=(
  "agents/architect.md"
  "agents/qa-gatekeeper.md"
  "agents/reviewer.md"
  "agents/security-auditor.md"
  "commands/execute.md"
  "commands/qa.md"
  "commands/prepush.md"
  "commands/release.md"
)

MARKER='<!-- repo-specific -->'

# Merge one shared file into a target repo copy:
#   result = shared content up to and including the marker line,
#            with the target's own `description:` frontmatter line kept,
#            followed by the target's content below its own marker.
merge_file() {
  local shared="$1" target="$2"
  if [ ! -f "$target" ]; then
    mkdir -p "$(dirname "$target")"
    cp "$shared" "$target"
    return
  fi
  # Safety for the one-time rollout: existing repo files predate the marker convention.
  # Never replace them with the generic skeleton — skip until the controlled per-repo
  # standardization PR inserts the marker. After that, future runs merge safely.
  if ! grep -Fq -- "$MARKER" "$target"; then
    echo "    WARN: skipping ${target} (no repo-specific marker; migrate manually first)" >&2
    return
  fi
  local tmp="${target}.syncmerge"
  awk -v marker="$MARKER" '{print} index($0, marker){exit}' "$shared" > "$tmp"
  local desc
  desc="$(grep -m1 '^description:' "$target" || true)"
  if [ -n "$desc" ]; then
    awk -v d="$desc" '!done && /^description:/{print d; done=1; next} {print}' \
      "$tmp" > "${tmp}.2" && mv "${tmp}.2" "$tmp"
  fi
  awk -v marker="$MARKER" 'found{print} index($0, marker){found=1}' "$target" >> "$tmp"
  mv "$tmp" "$target"
}

if [ "$#" -eq 0 ]; then
  TARGETS=(CognitiveSystems MediaRefinery ModelDeck Uploadarr HomeAssistant)
else
  TARGETS=("$@")
fi

STAMP="$(date -u +%Y%m%d)"
FAILURES=()

for NAME in "${TARGETS[@]}"; do
  PREFIX="$(repo_prefix "$NAME")"
  REPO="AutomationNexus/${NAME}"
  BRANCH="${PREFIX}-sync-shared-claude-${STAMP}"
  echo "==> ${REPO}"

  CLONE_DIR="${WORK_DIR}/${NAME}"
  if ! gh repo clone "$REPO" "$CLONE_DIR" -- --quiet; then
    echo "    FAILED: could not clone ${REPO}" >&2
    FAILURES+=("$NAME")
    continue
  fi

  (
    cd "$CLONE_DIR"
    # App repos keep .claude/ on dev (dev-only convention). NOTE: ModelDeck's default
    # branch is main (stripped of .claude/) -- never use the clone default. Resume the
    # same-day remote sync branch if it already exists; otherwise branch from origin/dev.
    if git show-ref --verify --quiet "refs/remotes/origin/${BRANCH}"; then
      git checkout -q -b "$BRANCH" "origin/${BRANCH}"
    else
      git checkout -q -b "$BRANCH" origin/dev
    fi

    for rel in "${SHARED_FILES[@]}"; do
      merge_file "${SHARED_CLAUDE}/${rel}" ".claude/${rel}"
    done
    # Staged diff, not working-tree status: avoids Windows CRLF false positives
    # (see sync-templates.sh for the full explanation).
    git add -A -- .claude
    if git diff --cached --quiet; then
      echo "    already in sync"
    else
      git commit -q -m "chore: sync shared-core .claude layer from automationnexus/.github templates/_shared"
      git push -q origin "$BRANCH"
      if gh pr list --repo "$REPO" --state open --head "$BRANCH" --json number --jq 'length > 0' | grep -q true; then
        echo "    updated existing PR from ${BRANCH}"
      else
        gh pr create --repo "$REPO" --base dev --head "$BRANCH" \
          --title "chore: sync shared-core .claude layer" \
          --body "Automated propagation of templates/_shared/.claude (agents: architect, qa-gatekeeper, reviewer, security-auditor; commands: execute, qa, prepush, release) from automationnexus/.github via scripts/sync-shared-claude.sh. Per-repo description lines and content below the repo-specific marker are preserved. Dev-only files; no runtime impact."
        echo "    opened PR from ${BRANCH}"
      fi
    fi
    exit 0
  ) || {
    echo "    FAILED: ${REPO}" >&2
    FAILURES+=("$NAME")
    continue
  }
done

if [ "${#FAILURES[@]}" -gt 0 ]; then
  echo "==> Completed with failures: ${FAILURES[*]}" >&2
  exit 1
fi
echo "==> Done."
exit 0
