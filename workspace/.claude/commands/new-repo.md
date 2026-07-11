---
description: Guided new-repo creation from a template group (bootstrap wiring included).
argument-hint: <repo-name> [group A-E]
---

Walk the user through creating a new org repo: $ARGUMENTS

1. Read `.github/docs/new-repo-guide.md` and confirm the group (A python-docker /
   B python-pypi / C docker-ha-addon / D infra-main-only / E ha-config), the repo name,
   and public vs private.
2. Recap what will happen: "Use this template" repo creation from the matching
   `template-*` repo, placeholder replacement, then `scripts/bootstrap-repo.sh`
   (creates `dev`, sets CI-Bot App secrets — group B also needs `PYPI_API_TOKEN` in the
   operator's env — and applies rulesets for public repos).
3. STOP for explicit human confirmation before any `gh repo create`, secret write, or
   push.
4. After bootstrap, run the guide's verification commands and report the results.
