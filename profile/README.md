# AutomationNexus

Org CI/CD is standardized via reusable workflows in `automationnexus/.github`.

See `.github/workflows/` for reusable templates and `.github/rulesets/` for branch protection rules.

## Repositories

| Repo | Type | Branch flow |
|------|------|-------------|
| [`.github`](https://github.com/AutomationNexus/.github) | Meta — reusable workflows, templates, scripts, governance | feature → PR → `master` |
| `CognitiveSystems`, `MediaRefinery`, `ModelDeck`, `Uploadarr` | Application repos (versioned, auto-tagged releases) | feature → PR → `dev` → CI → `main` → release |
| `HomeAssistant` | Home Assistant configuration (no release versioning) | feature → PR → `dev` → CI → `main` |
| `template-python-docker`, `template-python-pypi`, `template-docker-ha-addon`, `template-infra-main-only`, `template-ha-config` | Starter templates for new repos in each group | feature → PR → `main` (no `dev`) |

## Ownership, support, and security

Repository ownership, support routing, and security contact points are tracked by
human GitHub team, not by any individual:

- **Platform** — `.github` meta-repo, reusable workflows, templates, scripts, rulesets.
- **Security** — security-sensitive paths across every repo: workflows, permissions,
  secrets hygiene, permission denylists.
- **Release** — promote/release paths: promote-to-main triggers, release workflows,
  version/tag policy.
- **App maintainers** — application and Home Assistant config source.
- **Admins** — org ownership, billing, and ruleset/security-setting changes.

To report a security issue, open a private security advisory on the relevant repo
(or on `automationnexus/.github` if the issue spans the org's shared workflows) rather
than a public issue.

## Governance

This org uses Claude Code as a development assistant across every repo, orchestrated
through a documented AI agent structure. The agents themselves hold no GitHub
permissions, team membership, or CODEOWNERS entries — only the human teams above do.
The full model — agent roster, human team mapping, repository ownership, and every
documented exception — is public in `automationnexus/.github`:

- [`governance/README.md`](https://github.com/AutomationNexus/.github/blob/master/governance/README.md) — terminology and the human-vs-AI distinction
- [`governance/organogram.md`](https://github.com/AutomationNexus/.github/blob/master/governance/organogram.md) — rendered hierarchy and repo/team/task matrix
- [`governance/registry.yml`](https://github.com/AutomationNexus/.github/blob/master/governance/registry.yml) — the underlying source of truth
