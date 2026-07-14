---
description: Live status sweep across all org repos (read-only).
argument-hint: [optional repo name(s)]
---

Dispatch `org-inspector` to sweep: $ARGUMENTS (default: all org repos).

Return its compact status table verbatim: repo | local branch/dirty state | open PRs |
last run conclusions | anomalies. Read-only — no fixes, no state changes. If anomalies
were flagged, suggest (but do not run) the next diagnostic step per the workspace
CLAUDE.md "Emergency / doubt checklist".

This command is the org-root operating protocol's "refresh state" step (`CLAUDE.md`) run
standalone — run it before acting on any PR/branch/workflow, not only when something
looks broken.
