#!/usr/bin/env bash
# Wire a freshly-created AutomationNexus repo: branches, default branch, secrets, protection.
# The template copies files; this does everything templates cannot.
#
# Usage:
#   CI_BOT_APP_ID=4168350 \
#   CI_BOT_APP_PRIVATE_KEY_PATH=/path/to/ci-bot.private-key.pem \
#   [PYPI_API_TOKEN=pypi-...] \
#   scripts/bootstrap-repo.sh <owner/repo> <A|B|C|D|E> <public|private>
#
# Requires: gh (authenticated with repo + admin scopes), jq.
set -euo pipefail

REPO="${1:?owner/repo required}"
GROUP="${2:?group A|B|C|D|E required}"
VIS="${3:?public|private required}"

RULESET_DIR="$(cd "$(dirname "$0")/../rulesets" && pwd)"

echo "==> Bootstrapping ${REPO} (group ${GROUP}, ${VIS})"

# 1) CI-Bot App secrets (every repo)
: "${CI_BOT_APP_ID:?set CI_BOT_APP_ID}"
: "${CI_BOT_APP_PRIVATE_KEY_PATH:?set CI_BOT_APP_PRIVATE_KEY_PATH}"
gh secret set CI_BOT_APP_ID --repo "$REPO" --body "$CI_BOT_APP_ID"
gh secret set CI_BOT_APP_PRIVATE_KEY --repo "$REPO" < "$CI_BOT_APP_PRIVATE_KEY_PATH"
echo "    set CI-Bot App secrets"

# 2) PyPI token (group B only)
if [ "$GROUP" = "B" ]; then
  : "${PYPI_API_TOKEN:?group B needs PYPI_API_TOKEN}"
  gh secret set PYPI_API_TOKEN --repo "$REPO" --body "$PYPI_API_TOKEN"
  echo "    set PYPI_API_TOKEN"
fi

# 3) dev branch (skip for group D / main-only). Default branch is dev for every group
#    EXCEPT C: Home Assistant's add-on-repository feature clones a repo's default branch
#    with no way for a user to pin a ref, so Group C's in-repo HA add-on folder(s) require
#    default = main (see templates/C-docker-ha-addon/README.md, "Why one repo, not two").
#    Setting default = dev on a Group C repo silently ships stale/wrong add-on metadata to
#    every HA instance that adds the repo (found live on ModelDeck — dev's copy of the
#    nightly add-on pointer had gone stale because that pointer is only ever written to
#    main by nightly.yml's roll-nightly-addon job).
if [ "$GROUP" != "D" ]; then
  main_sha=$(gh api "repos/${REPO}/git/refs/heads/main" --jq '.object.sha')
  if ! gh api "repos/${REPO}/git/refs/heads/dev" >/dev/null 2>&1; then
    gh api -X POST "repos/${REPO}/git/refs" -f ref="refs/heads/dev" -f sha="$main_sha" >/dev/null
    echo "    created dev branch"
  fi
  if [ "$GROUP" = "C" ]; then
    gh api -X PATCH "repos/${REPO}" -f default_branch=main >/dev/null
    echo "    default branch = main (Group C: HA add-on store reads the default branch)"
  else
    gh api -X PATCH "repos/${REPO}" -f default_branch=dev >/dev/null
    echo "    default branch = dev"
  fi
fi

# 4) Normalize the native "Allow auto-merge" setting to off (all repos, any visibility).
#    It is unused: every PR is merged by auto-merge.yml's CI-Bot App doing an immediate
#    `gh pr merge` after checks go green, not GitHub's native auto-merge queue. On the
#    org's GitHub Free plan the native flag can only be ENABLED on public repos anyway
#    (private-repo auto-merge needs a paid plan), so it could never be turned on
#    uniformly org-wide — off-and-unmanaged is the normalized state (#35). Disabling it
#    works regardless of visibility/plan.
gh api -X PATCH "repos/${REPO}" -f allow_auto_merge=false >/dev/null
echo "    allow_auto_merge = false (unused; auto-merge.yml/CI-Bot is the real merge path)"

# 5) Protection — public repos get rulesets; private rely on guards + auto-revert
if [ "$VIS" = "public" ]; then
  gh api "repos/${REPO}/rulesets" -X POST --input "${RULESET_DIR}/protect-main.json" >/dev/null
  echo "    applied protect-main ruleset"
  if [ "$GROUP" != "D" ]; then
    gh api "repos/${REPO}/rulesets" -X POST --input "${RULESET_DIR}/protect-dev.json" >/dev/null
    echo "    applied protect-dev ruleset"
  fi
else
  echo "    private repo: skipping rulesets (Free plan) — guards + auto-revert apply."
  echo "    NOTE: ensure ci.yml has 'auto-revert: true' for this repo."
fi

echo "==> Done. The CI-Bot App is installed org-wide ('All repositories'), so no per-repo App install is needed."
echo "    Add source code, replace REPLACE_ME placeholders, then open a PR into dev."
