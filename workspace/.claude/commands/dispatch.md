---
description: Route a task through the org — target repos, ordering, per-repo handoff briefs.
argument-hint: <task description>
---

Follow the org-root operating protocol in `CLAUDE.md` (classify → refresh live state →
build dependency graph → delegate → handoff → handback → close out) to dispatch
`chief-architect` and route this task: $ARGUMENTS

Expect back, per affected repo, the full handoff packet defined in `CLAUDE.md`'s
"Handoff packet (org → repo)": repository + execution order (shared-workflow changes in
`automationnexus/.github` merge first), goal/non-goals/branch, paths + `CLAUDE.md`
constraints, required repo agents/commands + risk track, shared-workflow/template
dependencies, file ownership boundaries, permission/secret constraints, review/security/
QA/rollback requirements, expected PR target + release impact, and escalation triggers.

Relay the briefs to the user with the instruction to open a Claude Code session in each
target repo — repo-tier agents only load there. Only trivial mechanical cross-repo edits
may be done from this root session directly, and then only following each repo's
CLAUDE.md and running its QA gate commands manually.

When a repo session reports back, expect the handback packet from `CLAUDE.md`'s
"Handback packet (repo → org)" — repo/branch/PR/commits/files, QA/runtime evidence,
review/security disposition, deviations, and any outstanding promote/release/admin
action — before treating that repo's slice of the task as done.
