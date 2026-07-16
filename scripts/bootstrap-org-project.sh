#!/usr/bin/env bash
# Bootstrap (or reconcile) the org-wide "AutomationNexus — Delivery" GitHub
# Project -- the single org-level Project v2 that tracks Issues (as cards)
# from every AutomationNexus repo in one board / table / roadmap. The board
# is ISSUE-CENTRIC and LEAN: a PR's relationship to its issue surfaces via
# the built-in Linked pull requests field, not a separate PR card or a
# separate planning-layer field -- see docs/org-project.md.
#
# This is the reproducible source of truth for the Project's SHAPE (its custom
# fields and the Status pipeline stages). It does NOT own the Project's items or
# its saved views:
#   - Items flow in via add-to-project.yml (issues only, event-driven) and,
#     going forward, org-project-sync.yml (Status reconciliation on a
#     schedule, derived from each issue's linked PRs).
#   - View layouts (board grouping, roadmap timeline, filters) and the native
#     Iteration field are UI-only -- the GitHub API cannot create them. See
#     docs/org-project.md for the click-by-click view recipe.
#   - The Project's own native "Auto-add to project" workflow (Project UI ->
#     Workflows) is a separate, UI-only setting from add-to-project.yml above.
#     If it is currently configured to auto-add Pull requests too, switch it
#     to Issues-only there -- this script cannot see or change it via the API.
#
# The script is idempotent for custom fields: it finds the Project by title
# (creating it only if absent), then creates any custom field that is
# missing. The Status field's pipeline options are handled separately below
# and are CREATE-ONLY, not idempotent-by-replace -- see the comment there.
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
# Lean by design: Area/Type is the only custom field the board keeps. The
# unused planning layer (Bump type, Priority, Track, Release target, Start
# date, Target date) was dropped in the issue-centric redesign -- Status is
# now fully derived from each issue's linked PR(s) by org-project-sync.yml,
# so those fields had no automation reading or writing them. Deliberately
# NOT deleting them here if a board still has them from before this redesign
# -- ensure_select/ensure_plain only ever create, ceasing to declare a field
# does not retroactively remove it; drop it via the Project UI by hand if a
# clean board is wanted.
ensure_select "Area/Type"      "feature,bug,chore,release,platform,security,docs"

# --- Status pipeline stages (reshape the built-in Status field) -------------
# The built-in Status single-select ships as Todo/In Progress/Done. On a
# genuinely FRESH Project (still holding only those GitHub defaults) we
# replace them wholesale with the AutomationNexus Backlog -> ... ->
# Released/Done pipeline so the built-in "item added / closed" automations
# still drive one field.
#
# *** THIS MUTATION IS CREATE-ONLY. NEVER RE-RUN IT AGAINST A POPULATED
# *** BOARD. *** updateProjectV2Field's singleSelectOptions input takes an
# OPTIONAL `id` per option; every option below omits `id`, so a full replace
# makes GitHub mint a BRAND-NEW option id for every single one of them --
# including options whose name text is completely unchanged. Every project
# item's existing Status value is stored as a reference to the OLD option
# id: the instant that id stops existing, the item's Status silently goes
# blank ("unassigned"), for every item on the board, not just ones that
# actually needed a stage renamed/added. That is not idempotent and not
# safe to repeat.
#
# If the pipeline stages ever need to change on a board that already has
# real items triaged (add one more terminal stage, rename one, etc.), that
# MUST go through the Project UI (which preserves option ids for unchanged
# names), or a hand-written mutation that passes back every existing
# option's real `id` alongside any new one -- never this replace-all.
#
# So: look up the Status field's *current* options first, and only run the
# full-replace mutation if none of our pipeline names are present yet (i.e.
# this still looks like a fresh/default board). Otherwise skip entirely --
# a board that already has "Backlog" et al. is left exactly as-is, even if
# it's missing one of the newer stages (e.g. "Done"); adding just that one
# stage safely is a UI/ID-preserving-mutation job, not this script's.
STATUS_FIELD_ID="$(gh project field-list "$NUMBER" --owner "$OWNER" --format json \
  | python3 -c "import sys,json;print(next(f['id'] for f in json.load(sys.stdin)['fields'] if f['name']=='Status'))")"
STATUS_OPTION_NAMES="$(gh project field-list "$NUMBER" --owner "$OWNER" --format json \
  | python3 -c "import sys,json;f=next(f for f in json.load(sys.stdin)['fields'] if f['name']=='Status');print('\n'.join(o['name'] for o in f.get('options', [])))")"

has_status_option() { grep -qxF "$1" <<<"$STATUS_OPTION_NAMES"; }

if has_status_option "Backlog"; then
  echo "  = Status already has the AutomationNexus pipeline options (\"Backlog\" present) -- leaving as-is."
  echo "    To add or rename a stage on this now-populated board: use the Project UI, or a"
  echo "    hand-written mutation that passes back every existing option's real id. Never"
  echo "    re-run a full singleSelectOptions replace here (see comment above)."
else
  echo "  + Status -> Backlog / In Progress / In Review / On Dev / Promote Pending / Released / Done / Blocked"
  echo "    (fresh/default board detected -- one-time full replace of Todo/In Progress/Done is safe here)"
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
      {name:"Done",            color:GRAY,   description:"Closed, no versioned release"},
      {name:"Blocked",         color:RED,    description:"Blocked"}
    ]
  }){ projectV2Field { ... on ProjectV2SingleSelectField { name } } }
}' -f fid="$STATUS_FIELD_ID" >/dev/null || true
fi

echo "Done. Project id: $PROJECT_ID"
echo "Remaining UI-only steps (see docs/org-project.md): native Iteration field, saved views, auto-add + auto-archive workflow toggles."
