---
description: Refresh the workspace-root CLAUDE.md/.claude from the canonical .github/workspace/.
---

1. Run `scripts/sync-workspace.sh --check` (from the `.github` clone, Git Bash) and
   show the drift report.
2. If drift is reported: the root copies were hand-edited or the canonical source
   changed. Show which files, remind that the canonical source is `.github/workspace/`
   (edits go there via PR to `master`), and get user confirmation before re-running
   with `--force` — a timestamped backup of the current root copies is taken
   automatically before any overwrite.
3. If clean (or only missing files): run `scripts/sync-workspace.sh` and report what
   was copied.
