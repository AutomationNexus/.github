#!/usr/bin/env python3
"""Validate governance/registry.yml: structure, cross-references, and .claude discovery.

Hand-rolled checks below are authoritative. governance/schema.json is validated too when
the optional `jsonschema` package happens to be installed, but this repo has no dependency
management of its own and cannot assume it is present -- do not make it a hard requirement.

Usage:
    python scripts/validate-governance.py [--live] [--workspace-root PATH]

Exit code is nonzero if any ERROR-level finding was reported. WARN-level findings (mostly
needs-verification/permission-limited/missing-sibling-clone cases) are reported but do not
fail the run.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover - environment guard, not a logic path
    print("PyYAML is required: pip install pyyaml", file=sys.stderr)
    raise SystemExit(1) from exc

try:
    import jsonschema  # type: ignore
except ImportError:
    jsonschema = None  # type: ignore[assignment]

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent
GOVERNANCE_DIR = REPO_ROOT / "governance"
REGISTRY_PATH = GOVERNANCE_DIR / "registry.yml"
SCHEMA_PATH = GOVERNANCE_DIR / "schema.json"
ORGANOGRAM_PATH = GOVERNANCE_DIR / "organogram.md"

VERIFICATION_STATES = {"active", "desired", "exception", "needs-verification", "permission-limited"}
AUTHORITY_CLASSES = {"read-only", "repo-write", "cross-repo-write", "admin-state", "human-confirmation-required"}
MUTATING_TOOLS = {"Edit", "Write", "NotebookEdit"}

FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?\n)---\s*\n?", re.DOTALL)


class Report:
    def __init__(self) -> None:
        self.findings: list[tuple[str, str, str]] = []  # (level, area, message)

    def error(self, area: str, message: str) -> None:
        self.findings.append(("ERROR", area, message))

    def warn(self, area: str, message: str) -> None:
        self.findings.append(("WARN", area, message))

    @property
    def has_errors(self) -> bool:
        return any(level == "ERROR" for level, _, _ in self.findings)

    def render(self) -> str:
        if not self.findings:
            return "No findings. Registry and discovered .claude files are consistent."
        lines = []
        for level, area, message in self.findings:
            lines.append(f"[{level}] {area}: {message}")
        errors = sum(1 for level, _, _ in self.findings if level == "ERROR")
        warns = sum(1 for level, _, _ in self.findings if level == "WARN")
        lines.append(f"\n{errors} error(s), {warns} warning(s).")
        return "\n".join(lines)


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_frontmatter(path: Path) -> dict[str, Any] | None:
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        return None
    try:
        data = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return None
    return data if isinstance(data, dict) else None


def parse_tools(frontmatter: dict[str, Any]) -> set[str]:
    raw = frontmatter.get("tools", "")
    if isinstance(raw, list):
        return {str(t).strip() for t in raw}
    return {t.strip() for t in str(raw).split(",") if t.strip()}


# ---------------------------------------------------------------------------
# Schema validation (best-effort)
# ---------------------------------------------------------------------------

def validate_schema(registry: Any, report: Report) -> None:
    if jsonschema is None:
        report.warn("schema", "jsonschema package not installed -- skipped; hand-rolled checks below are authoritative")
        return
    schema = load_json(SCHEMA_PATH)
    validator = jsonschema.Draft202012Validator(schema)
    for error in sorted(validator.iter_errors(registry), key=lambda e: list(e.path)):
        path = "/".join(str(p) for p in error.path) or "<root>"
        report.error("schema", f"{path}: {error.message}")


# ---------------------------------------------------------------------------
# Structural / cross-reference checks (authoritative regardless of jsonschema)
# ---------------------------------------------------------------------------

def require_keys(obj: dict[str, Any], keys: list[str], area: str, label: str, report: Report) -> None:
    for key in keys:
        if key not in obj:
            report.error(area, f"{label} missing required key '{key}'")


def check_top_level(registry: Any, report: Report) -> None:
    if not isinstance(registry, dict):
        report.error("registry", "root of registry.yml must be a mapping")
        raise SystemExit(2)
    required = [
        "schema_version", "human_teams", "org_agents", "org_commands",
        "repo_core_team", "repo_core_commands", "repositories",
        "authority_classes", "exceptions",
    ]
    require_keys(registry, required, "registry", "registry.yml", report)
    if registry.get("schema_version") != 1:
        report.error("registry", f"schema_version must be 1, got {registry.get('schema_version')!r}")


def check_human_teams(registry: Any, report: Report) -> set[str]:
    slugs: set[str] = set()
    for team in registry.get("human_teams", []):
        require_keys(team, ["slug", "purpose", "default_repo_permission", "state"], "human_teams", str(team.get("slug", "<unnamed>")), report)
        slug = team.get("slug")
        if slug in slugs:
            report.error("human_teams", f"duplicate slug '{slug}'")
        elif slug:
            slugs.add(slug)
        if team.get("state") not in VERIFICATION_STATES:
            report.error("human_teams", f"{slug}: invalid state '{team.get('state')}'")
    return slugs


def check_org_agents(registry: Any, report: Report) -> dict[str, dict[str, Any]]:
    agents: dict[str, dict[str, Any]] = {}
    for agent in registry.get("org_agents", []):
        name = agent.get("name")
        require_keys(
            agent,
            ["name", "model", "rank", "role", "decision_rights", "mutation_class", "escalation_target", "parent"],
            "org_agents", str(name or "<unnamed>"), report,
        )
        if name in agents:
            report.error("org_agents", f"duplicate name '{name}'")
        elif name:
            agents[name] = agent
        if agent.get("mutation_class") not in AUTHORITY_CLASSES:
            report.error("org_agents", f"{name}: invalid mutation_class '{agent.get('mutation_class')}'")
        if agent.get("rank") not in {"org-lead", "org-operational"}:
            report.error("org_agents", f"{name}: invalid rank '{agent.get('rank')}'")

    # Escalation chains must terminate at "human" with no cycles.
    for name, agent in agents.items():
        seen = {name}
        current = agent.get("escalation_target")
        depth = 0
        while current != "human":
            depth += 1
            if depth > 10:
                report.error("org_agents", f"{name}: escalation chain did not terminate within 10 hops")
                break
            if current in seen:
                report.error("org_agents", f"{name}: escalation chain cycles back to '{current}'")
                break
            if current not in agents:
                report.error("org_agents", f"{name}: escalation_target '{current}' is not 'human' and not a known org agent")
                break
            seen.add(current)
            current = agents[current].get("escalation_target")

    # parent, when set, must name a known org agent.
    for name, agent in agents.items():
        parent = agent.get("parent")
        if parent is not None and parent not in agents:
            report.error("org_agents", f"{name}: parent '{parent}' is not a known org agent")

    return agents


def check_org_commands(registry: Any, org_agents: dict[str, Any], report: Report) -> set[str]:
    names: set[str] = set()
    for command in registry.get("org_commands", []):
        name = command.get("name")
        require_keys(command, ["name", "owner", "confirmation_class", "entry_conditions", "outputs"], "org_commands", str(name or "<unnamed>"), report)
        if name in names:
            report.error("org_commands", f"duplicate name '{name}'")
        elif name:
            names.add(name)
        if command.get("owner") not in org_agents:
            report.error("org_commands", f"{name}: owner '{command.get('owner')}' is not a known org agent")
        if command.get("confirmation_class") not in AUTHORITY_CLASSES:
            report.error("org_commands", f"{name}: invalid confirmation_class '{command.get('confirmation_class')}'")
    return names


def check_repo_core_team(registry: Any, report: Report) -> dict[str, dict[str, Any]]:
    team: dict[str, dict[str, Any]] = {}
    expected = {"architect", "qa-gatekeeper", "reviewer", "security-auditor"}
    for role in registry.get("repo_core_team", []):
        name = role.get("name")
        require_keys(role, ["name", "model", "decision_rights", "mutation_class"], "repo_core_team", str(name or "<unnamed>"), report)
        if name:
            team[name] = role
        if role.get("mutation_class") not in AUTHORITY_CLASSES:
            report.error("repo_core_team", f"{name}: invalid mutation_class '{role.get('mutation_class')}'")
    missing = expected - team.keys()
    if missing:
        report.error("repo_core_team", f"missing expected core role(s): {sorted(missing)}")
    return team


def check_repo_core_commands(registry: Any, report: Report) -> set[str]:
    names: set[str] = set()
    for command in registry.get("repo_core_commands", []):
        name = command.get("name")
        require_keys(command, ["name", "confirmation_class"], "repo_core_commands", str(name or "<unnamed>"), report)
        if name:
            names.add(name)
        if command.get("confirmation_class") not in AUTHORITY_CLASSES:
            report.error("repo_core_commands", f"{name}: invalid confirmation_class '{command.get('confirmation_class')}'")
    return names


def check_authority_classes(registry: Any, report: Report) -> None:
    declared = registry.get("authority_classes", [])
    if set(declared) != AUTHORITY_CLASSES:
        report.error("authority_classes", f"expected exactly {sorted(AUTHORITY_CLASSES)}, got {sorted(declared)}")


def check_repositories(registry: Any, human_teams: set[str], report: Report) -> dict[str, dict[str, Any]]:
    repos: dict[str, dict[str, Any]] = {}
    for repo in registry.get("repositories", []):
        name = repo.get("repo")
        require_keys(
            repo,
            ["repo", "class", "default_branch", "branch_flow", "team_policy", "dev_only_files", "sync_role", "owning_team", "state"],
            "repositories", str(name or "<unnamed>"), report,
        )
        if name in repos:
            report.error("repositories", f"duplicate repo '{name}'")
        elif name:
            repos[name] = repo
        if repo.get("state") not in VERIFICATION_STATES:
            report.error("repositories", f"{name}: invalid state '{repo.get('state')}'")
        if repo.get("class") not in {"meta", "full", "config-only", "minimal", "template"}:
            report.error("repositories", f"{name}: invalid class '{repo.get('class')}'")
        if repo.get("team_policy") not in {"meta-core", "full-core", "minimal", "stub"}:
            report.error("repositories", f"{name}: invalid team_policy '{repo.get('team_policy')}'")
        if repo.get("sync_role") not in {"canonical-source", "consumer", "template-target", "excluded"}:
            report.error("repositories", f"{name}: invalid sync_role '{repo.get('sync_role')}'")
        if repo.get("owning_team") not in human_teams:
            report.error("repositories", f"{name}: owning_team '{repo.get('owning_team')}' is not a known human team")
        if repo.get("state") == "exception" and not repo.get("exception"):
            report.error("repositories", f"{name}: state is 'exception' but no 'exception' block is present")
        exception = repo.get("exception")
        if exception:
            require_keys(exception, ["rationale", "owner", "review_trigger"], "repositories", f"{name}.exception", report)
    return repos


def check_exceptions(registry: Any, human_teams: set[str], report: Report) -> None:
    ids: set[str] = set()
    for exc in registry.get("exceptions", []):
        exc_id = exc.get("id")
        require_keys(exc, ["id", "description", "owner", "review_trigger"], "exceptions", str(exc_id or "<unnamed>"), report)
        if exc_id in ids:
            report.error("exceptions", f"duplicate id '{exc_id}'")
        elif exc_id:
            ids.add(exc_id)
        if exc.get("owner") not in human_teams:
            report.error("exceptions", f"{exc_id}: owner '{exc.get('owner')}' is not a known human team")


# ---------------------------------------------------------------------------
# .claude discovery: registered-vs-on-disk drift
# ---------------------------------------------------------------------------

def discover_agents(directory: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not directory.is_dir():
        return found
    for path in sorted(directory.glob("*.md")):
        found[path.stem] = path
    return found


def discover_commands(directory: Path) -> dict[str, Path]:
    found: dict[str, Path] = {}
    if not directory.is_dir():
        return found
    for path in sorted(directory.glob("*.md")):
        found[f"/{path.stem}"] = path
    return found


def check_agent_files(agent_names: set[str], directory: Path, area: str, report: Report, expect_repo_specific_marker: bool = False) -> None:
    on_disk = discover_agents(directory)
    missing = agent_names - on_disk.keys()
    unregistered = on_disk.keys() - agent_names
    for name in sorted(missing):
        report.error(area, f"registered agent '{name}' has no file in {directory.relative_to(REPO_ROOT)}")
    for name in sorted(unregistered):
        report.warn(area, f"file {on_disk[name].relative_to(REPO_ROOT)} is not registered under any known agent name")
    for name, path in on_disk.items():
        frontmatter = parse_frontmatter(path)
        if frontmatter is None:
            report.error(area, f"{path.relative_to(REPO_ROOT)}: missing or unparseable frontmatter")
            continue
        require_keys(frontmatter, ["name", "description", "tools", "model"], area, str(path.relative_to(REPO_ROOT)), report)
        if frontmatter.get("name") != path.stem:
            report.error(area, f"{path.relative_to(REPO_ROOT)}: frontmatter name '{frontmatter.get('name')}' does not match filename '{path.stem}'")
        if expect_repo_specific_marker and "<!-- repo-specific -->" not in path.read_text(encoding="utf-8"):
            report.warn(area, f"{path.relative_to(REPO_ROOT)}: shared-core file has no '<!-- repo-specific -->' marker for sync-shared-claude.sh")


def check_command_files(command_names: set[str], directory: Path, area: str, report: Report) -> None:
    on_disk = discover_commands(directory)
    missing = command_names - on_disk.keys()
    unregistered = on_disk.keys() - command_names
    for name in sorted(missing):
        report.error(area, f"registered command '{name}' has no file in {directory.relative_to(REPO_ROOT)}")
    for name in sorted(unregistered):
        report.warn(area, f"file {on_disk[name].relative_to(REPO_ROOT)} is not registered under any known command name")
    for name, path in on_disk.items():
        frontmatter = parse_frontmatter(path)
        if frontmatter is None or "description" not in frontmatter:
            report.error(area, f"{path.relative_to(REPO_ROOT)}: missing frontmatter 'description'")


def check_mutation_class_vs_tools(name: str, mutation_class: str, directory: Path, area: str, report: Report) -> None:
    path = directory / f"{name}.md"
    if not path.is_file():
        return
    frontmatter = parse_frontmatter(path)
    if not frontmatter:
        return
    tools = parse_tools(frontmatter)
    if mutation_class == "read-only" and tools & MUTATING_TOOLS:
        report.error(area, f"{name}: registered mutation_class is 'read-only' but frontmatter tools include {sorted(tools & MUTATING_TOOLS)}")


def check_organogram_coverage(org_agents: dict[str, Any], repo_core_team: dict[str, Any], report: Report) -> None:
    if not ORGANOGRAM_PATH.is_file():
        report.error("organogram", f"{ORGANOGRAM_PATH.relative_to(REPO_ROOT)} does not exist")
        return
    text = ORGANOGRAM_PATH.read_text(encoding="utf-8")
    for name in list(org_agents) + list(repo_core_team):
        if name not in text:
            report.warn("organogram", f"'{name}' is registered but not mentioned in organogram.md")


# ---------------------------------------------------------------------------
# Cross-repo checks (best-effort: sibling clones may not exist, e.g. in CI)
# ---------------------------------------------------------------------------

def check_sibling_repo_teams(repos: dict[str, dict[str, Any]], repo_core_team: dict[str, Any], workspace_root: Path, report: Report) -> None:
    for name, repo in repos.items():
        if repo.get("team_policy") not in {"full-core", "meta-core"}:
            continue
        if name == ".github":
            agents_dir = REPO_ROOT / ".claude" / "agents"
        else:
            sibling = workspace_root / name
            if not sibling.is_dir():
                report.warn("repositories", f"{name}: sibling clone not found under {workspace_root} -- skipped local team check")
                continue
            agents_dir = sibling / ".claude" / "agents"
        on_disk = discover_agents(agents_dir)
        missing = repo_core_team.keys() - on_disk.keys()
        if missing:
            report.error("repositories", f"{name}: missing core role file(s) {sorted(missing)} under {agents_dir}")


# ---------------------------------------------------------------------------
# Optional live GitHub checks
# ---------------------------------------------------------------------------

def gh_default_branch(repo: str) -> str | None:
    try:
        result = subprocess.run(
            ["gh", "api", f"repos/AutomationNexus/{repo}", "--jq", ".default_branch"],
            check=True, text=True, capture_output=True, timeout=30,
        )
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return None
    return result.stdout.strip() or None


def check_live(repos: dict[str, dict[str, Any]], report: Report) -> None:
    for name, repo in repos.items():
        live_branch = gh_default_branch(name)
        if live_branch is None:
            report.warn("live", f"{name}: could not query live default branch (permission-limited or gh unavailable)")
            continue
        expected = repo.get("default_branch")
        if live_branch != expected:
            report.error("live", f"{name}: registry says default_branch='{expected}', GitHub reports '{live_branch}'")


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--live", action="store_true", help="also query live GitHub state via gh (best-effort)")
    parser.add_argument("--workspace-root", type=Path, default=REPO_ROOT.parent, help="directory containing sibling repo clones (default: parent of this repo)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = Report()

    if not REGISTRY_PATH.is_file():
        print(f"ERROR: {REGISTRY_PATH} not found", file=sys.stderr)
        return 2
    registry = load_yaml(REGISTRY_PATH)

    check_top_level(registry, report)
    validate_schema(registry, report)

    human_teams = check_human_teams(registry, report)
    org_agents = check_org_agents(registry, report)
    org_command_names = check_org_commands(registry, org_agents, report)
    repo_core_team = check_repo_core_team(registry, report)
    repo_core_command_names = check_repo_core_commands(registry, report)
    check_authority_classes(registry, report)
    repos = check_repositories(registry, human_teams, report)
    check_exceptions(registry, human_teams, report)

    check_agent_files(set(org_agents), REPO_ROOT / "workspace" / ".claude" / "agents", "workspace-agents", report)
    check_command_files(org_command_names, REPO_ROOT / "workspace" / ".claude" / "commands", "workspace-commands", report)
    check_agent_files(set(repo_core_team), REPO_ROOT / "templates" / "_shared" / ".claude" / "agents", "shared-core-agents", report, expect_repo_specific_marker=True)
    check_command_files(repo_core_command_names, REPO_ROOT / "templates" / "_shared" / ".claude" / "commands", "shared-core-commands", report)
    check_agent_files(set(repo_core_team) | {"workflow-engineer"}, REPO_ROOT / ".claude" / "agents", "meta-repo-agents", report)

    for agent_name, agent in org_agents.items():
        check_mutation_class_vs_tools(agent_name, agent.get("mutation_class", ""), REPO_ROOT / "workspace" / ".claude" / "agents", "workspace-agents", report)
    for role_name, role in repo_core_team.items():
        check_mutation_class_vs_tools(role_name, role.get("mutation_class", ""), REPO_ROOT / "templates" / "_shared" / ".claude" / "agents", "shared-core-agents", report)
        check_mutation_class_vs_tools(role_name, role.get("mutation_class", ""), REPO_ROOT / ".claude" / "agents", "meta-repo-agents", report)

    check_organogram_coverage(org_agents, repo_core_team, report)
    check_sibling_repo_teams(repos, repo_core_team, args.workspace_root, report)

    if args.live:
        check_live(repos, report)

    print(report.render())
    return 1 if report.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
