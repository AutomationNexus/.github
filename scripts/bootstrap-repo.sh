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

# 3) dev branch + default = dev  (skip for group D / main-only)
if [ "$GROUP" != "D" ]; then
  main_sha=$(gh api "repos/${REPO}/git/refs/heads/main" --jq '.object.sha')
  if ! gh api "repos/${REPO}/git/refs/heads/dev" >/dev/null 2>&1; then
    gh api -X POST "repos/${REPO}/git/refs" -f ref="refs/heads/dev" -f sha="$main_sha" >/dev/null
    echo "    created dev branch"
  fi
  gh api -X PATCH "repos/${REPO}" -f default_branch=dev >/dev/null
  echo "    default branch = dev"
fi

# 4) Protection — public repos get rulesets; private rely on guards + auto-revert
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
