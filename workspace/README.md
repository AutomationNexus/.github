# workspace/ — canonical org-tier Claude Code layer

This directory is the versioned source of truth for the AutomationNexus **workspace
root**'s Claude Code layer:

- `CLAUDE.md` → copied to `<workspace-root>/CLAUDE.md`
- `.claude/` (org agents, org commands, settings) → copied to `<workspace-root>/.claude/`

The workspace root (the local directory containing all the org repo clones) is **not a
git repository**, so it cannot version these files itself — they are versioned here and
copied into place by `scripts/sync-workspace.sh`.

## Rules

- **Never hand-edit the root copies.** Edit here, land the change via feature branch →
  PR → `master`, then run `scripts/sync-workspace.sh` (or `/sync-workspace` from a
  workspace-root Claude Code session).
- The sync script refuses to overwrite drifted root copies without `--force`, and always
  snapshots the previous root copies to `workspace/.backups/<UTC-stamp>/` (gitignored)
  before overwriting — nothing is ever lost.
- The script is copy-only: it does not delete a root file that was removed from this
  directory. Handle deletions manually (rare).

## What lives here

- `.claude/agents/` — the 6 org-tier agents (chief-architect, platform-engineer,
  release-manager, security-officer, org-inspector, template-steward). These load ONLY
  in sessions opened at the workspace root — `.claude/` does not cascade from parent
  directories the way `CLAUDE.md` does.
- `.claude/commands/` — the org commands (`/org-status`, `/dispatch`, `/promote`,
  `/org-audit`, `/sync-templates`, `/sync-workspace`, `/new-repo`).
- `.claude/settings.json` — deny-only permission list for root sessions (superset of the
  `templates/_shared` baseline, since a root session can see every clone's secrets).

The full org model (org tier ↔ repo tier, handoff protocol) is documented in this
directory's `CLAUDE.md` under "Agent organization".
