#!/usr/bin/env bash
# Bootstrap (or reconcile) the org-wide "AutomationNexus — Delivery" GitHub
# Project -- the single org-level Project v2 that aggregates Issues and PRs from
# every AutomationNexus repo into one board / table / roadmap.
#
# This is the reproducible source of truth for the Project's SHAPE (its custom
# fields and the Status pipeline stages). It does NOT own the Project's items or
# its saved views:
#   - Items flow in via each repo's built-in auto-add workflow (configured in the
#     Project UI) and, going forward, org-project-sync.yml.
#   - View layouts (board grouping, roadmap timeline, filters) and the native
#     Iteration field are UI-only -- the GitHub API cannot create them. See
#     docs/org-project.md for the click-by-click view recipe.
#
# The script is idempotent: it finds the Project by title (creating it only if
# absent), then creates any custom field that is missing and (re)applies the
# Status single-select options. Re-running it is safe.
#
# Requirements:
#   - gh CLI authenticated with the `project` scope (gh auth refresh -s project).
#   - python3 on PATH (used for JSON parsing, matching the other scripts here).
#
# Usage:
#   scripts/bootstrap-org-project.sh            # create/reconcile
#   scripts/bootstrap-org-project.sh --dry-run  # print what it would do; no writes
set -euo pipefail

OWNER="AutomationNexus"
TITLE="AutomationNexus — Delivery"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

run() {
  if $DRY_RUN; then
    echo "DRY: $*"
  else
    "$@"
  fi
}

# --- locate or create the project ------------------------------------------
NUMBER="$(gh project list --owner "$OWNER" --format json \
  | python3 -c "import sys,json;print(next((str(p['number']) for p in json.load(sys.stdin)['projects'] if p['title']=='$TITLE'),''))")"

if [[ -z "$NUMBER" ]]; then
  echo "Project '$TITLE' not found -- creating."
  if $DRY_RUN; then
    echo "DRY: gh project create --owner $OWNER --title '$TITLE'"; exit 0
  fi
  NUMBER="$(gh project create --owner "$OWNER" --title "$TITLE" --format json \
    | python3 -c "import sys,json;print(json.load(sys.stdin)['number'])")"
fi
echo "Project #$NUMBER (${OWNER})"

PROJECT_ID="$(gh project view "$NUMBER" --owner "$OWNER" --format json \
  | python3 -c "import sys,json;print(json.load(sys.stdin)['id'])")"

# Existing field names, so we only create what's missing.
EXISTING="$(gh project field-list "$NUMBER" --owner "$OWNER" --format json \
  | python3 -c "import sys,json;print('\n'.join(f['name'] for f in json.load(sys.stdin)['fields']))")"

has_field() { grep -qxF "$1" <<<"$EXISTING"; }

ensure_select() {
  local name="$1" opts="$2"
  if has_field "$name"; then echo "  = field '$name' exists"; return; fi
  echo "  + field '$name' (single-select)"
  run gh project field-create "$NUMBER" --owner "$OWNER" --name "$name" \
    --data-type SINGLE_SELECT --single-select-options "$opts"
}
ensure_plain() {
  local name="$1" type="$2"
  if has_field "$name"; then echo "  = field '$name' exists"; return; fi
  echo "  + field '$name' ($type)"
  run gh project field-create "$NUMBER" --owner "$OWNER" --name "$name" --data-type "$type"
}

# --- custom fields ----------------------------------------------------------
ensure_select "Area/Type"      "feature,bug,chore,release,platform,security,docs"
ensure_select "Bump type"      "patch,minor,major,none,n-a"
ensure_select "Priority"       "P0,P1,P2,P3"
ensure_select "Track"          "On track,At risk,Off track"
ensure_plain  "Release target" TEXT
ensure_plain  "Start date"     DATE
ensure_plain  "Target date"    DATE

# --- Status pipeline stages (reshape the built-in Status field) -------------
# The built-in Status single-select ships as Todo/In Progress/Done. We replace
# its options with the AutomationNexus dev -> promote -> main -> release pipeline
# so the built-in "item added / closed" automations still drive one field.
STATUS_FIELD_ID="$(gh project field-list "$NUMBER" --owner "$OWNER" --format json \
  | python3 -c "import sys,json;print(next(f['id'] for f in json.load(sys.stdin)['fields'] if f['name']=='Status'))")"

echo "  ~ Status -> Backlog / In Progress / In Review / On Dev / Promote Pending / Released / Blocked"
run gh api graphql -f query='
mutation($fid:ID!){
  updateProjectV2Field(input:{
    fieldId:$fid,
    singleSelectOptions:[
      {name:"Backlog",         color:GRAY,   description:"Not started"},
      {name:"In Progress",     color:BLUE,   description:"Feature branch active"},
      {name:"In Review",       color:YELLOW, description:"PR open into dev"},
      {name:"On Dev",          color:PURPLE, description:"Merged to dev, awaiting promote"},
      {name:"Promote Pending", color:ORANGE, description:"Promote PR open into main"},
      {name:"Released",        color:GREEN,  description:"Tagged on main"},
      {name:"Blocked",         color:RED,    description:"Blocked"}
    ]
  }){ projectV2Field { ... on ProjectV2SingleSelectField { name } } }
}' -f fid="$STATUS_FIELD_ID" >/dev/null || true

echo "Done. Project id: $PROJECT_ID"
echo "Remaining UI-only steps (see docs/org-project.md): native Iteration field, saved views, auto-add + auto-archive workflow toggles."
