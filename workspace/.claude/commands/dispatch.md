---
description: Route a task through the org — target repos, ordering, per-repo handoff briefs.
argument-hint: <task description>
---

Dispatch `chief-architect` to route this task: $ARGUMENTS

Expect back: (1) the affected repos and their ordering (shared-workflow changes in
`automationnexus/.github` merge first), (2) a per-repo handoff brief (goal, constraints,
file paths, which repo agents/commands to use, QA gate), (3) risk notes (bump-type
impact, CI/ruleset interactions, rollback).

Relay the briefs to the user with the instruction to open a Claude Code session in each
target repo — repo-tier agents only load there. Only trivial mechanical cross-repo edits
may be done from this root session directly, and then only following each repo's
CLAUDE.md and running its QA gate commands manually.
