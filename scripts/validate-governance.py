#!/usr/bin/env python3
"""Validate governance/registry.yml: structure, cross-references, and .claude discovery.

Hand-rolled checks below are authoritative. governance/schema.json is validated too when
the optional `jsonschema` package happens to be installed, but this repo has no dependency
management of its own and cannot assume it is present -- do not make it a hard requirement.

Usage:
    python scripts/validate-governance.py [--live] [--workspace-root PATH]

Always runs (no live GitHub calls): registry schema/cross-reference checks, agent/command
file discovery vs registration, mutation-class-vs-tool-grant checks, sibling repo-core team
presence, and each full-core/meta-core repo's .claude/settings.json deny list against the
templates/_shared/.claude/settings.json.template baseline.

--live additionally queries GitHub for: default branch, repo security settings (secret
scanning/push protection/Dependabot) and rulesets (public repos only -- GitHub Free has no
ruleset support on private repos), human team existence, CODEOWNERS team-slug references,
label-API reachability, and org Projects v2. Findings about state described in the plan as
not-yet-rolled-out (Sections 5/6) are WARN, never ERROR -- this mode is reporting-only until
that rollout happens; auth/scope failures are also WARN ("permission-limited"), never treated
as a failed check.

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
RISK_TRACKS = {"A", "B", "C", "D"}

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


def check_repo_core_commands(registry: Any, repo_core_team: dict[str, Any], report: Report) -> set[str]:
    names: set[str] = set()
    # "main-session" is a documented sentinel (workspace/CLAUDE.md, templates/_shared/CLAUDE.md.template,
    # execute.md/release.md): /execute and /release are orchestrated by the main repo session across
    # multiple core roles depending on risk track, not owned by any single repo_core_team member.
    valid_owners = set(repo_core_team) | {"main-session"}
    for command in registry.get("repo_core_commands", []):
        name = command.get("name")
        require_keys(command, ["name", "owner", "confirmation_class", "entry_conditions", "outputs"], "repo_core_commands", str(name or "<unnamed>"), report)
        if name:
            names.add(name)
        if command.get("owner") not in valid_owners:
            report.error("repo_core_commands", f"{name}: owner '{command.get('owner')}' is not a known repo-core role or 'main-session'")
        if command.get("confirmation_class") not in AUTHORITY_CLASSES:
            report.error("repo_core_commands", f"{name}: invalid confirmation_class '{command.get('confirmation_class')}'")
        if "risk_tracks" in command:
            tracks = command.get("risk_tracks")
            if not isinstance(tracks, list) or not tracks:
                report.error("repo_core_commands", f"{name}: risk_tracks must be a non-empty list when present")
                continue
            invalid = [t for t in tracks if t not in RISK_TRACKS]
            if invalid:
                report.error("repo_core_commands", f"{name}: risk_tracks contains invalid entry(s) {invalid}, expected a subset of {sorted(RISK_TRACKS)}")
            if len(set(tracks)) != len(tracks):
                report.error("repo_core_commands", f"{name}: risk_tracks has duplicate entries {tracks}")
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
        if repo.get("class") == "full" and not repo.get("domain_agents") and repo.get("state") != "exception":
            report.error("repositories", f"{name}: class 'full' requires at least one domain agent; domain_agents is empty and no exception is registered")
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

def load_settings_deny(path: Path) -> set[str] | None:
    if not path.is_file():
        return None
    try:
        data = load_json(path)
    except (json.JSONDecodeError, OSError):
        return None
    if not isinstance(data, dict):
        return None
    deny = ((data.get("permissions") or {}).get("deny")) or []
    return {str(d) for d in deny}


def check_settings_denylist(repos: dict[str, dict[str, Any]], workspace_root: Path, report: Report) -> None:
    """Compare each full-core/meta-core repo's actual .claude/settings.json deny list against
    the mandatory baseline in templates/_shared/.claude/settings.json.template. Repos may add
    domain-specific secret-path denies on top -- only a MISSING baseline entry is a finding
    (this is how ModelDeck's now-fixed missing push-deny would have been caught automatically)."""
    baseline = load_settings_deny(REPO_ROOT / "templates" / "_shared" / ".claude" / "settings.json.template")
    if baseline is None:
        report.warn("settings-denylist", "could not load templates/_shared/.claude/settings.json.template -- skipped")
        return
    for name, repo in repos.items():
        if repo.get("team_policy") not in {"full-core", "meta-core"}:
            continue
        if name == ".github":
            settings_path = REPO_ROOT / ".claude" / "settings.json"
        else:
            sibling = workspace_root / name
            if not sibling.is_dir():
                report.warn("settings-denylist", f"{name}: sibling clone not found under {workspace_root} -- skipped local denylist check")
                continue
            settings_path = sibling / ".claude" / "settings.json"
        actual = load_settings_deny(settings_path)
        if actual is None:
            report.error("settings-denylist", f"{name}: {settings_path} missing or unparseable")
            continue
        missing = baseline - actual
        if missing:
            report.error("settings-denylist", f"{name}: .claude/settings.json is missing mandatory baseline deny(s) {sorted(missing)}")


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


def check_sibling_repo_domain_agents(repos: dict[str, dict[str, Any]], repo_core_team: dict[str, Any], workspace_root: Path, report: Report) -> None:
    """Compare each full-core/meta-core repo's registered domain_agents + extra_qa_gates
    against the domain-specific agent files actually on disk (agent files beyond the 4 shared
    core roles). This is what would have caught MediaRefinery/Uploadarr shipping real domain
    engineers with an empty registered domain_agents: [], and HomeAssistant's yaml-engineer
    file going unregistered.

    extra_orchestration is deliberately excluded from this comparison: it can name a process
    or command rather than an agent file -- e.g. HomeAssistant's dry-run-deploy refers to the
    /deploy-dry-run command (which dispatches release-operator), not a .claude/agents/*.md
    file -- so it is not comparable to disk the same way domain_agents/extra_qa_gates are."""
    for name, repo in repos.items():
        if repo.get("team_policy") not in {"full-core", "meta-core"}:
            continue
        if name == ".github":
            agents_dir = REPO_ROOT / ".claude" / "agents"
        else:
            sibling = workspace_root / name
            if not sibling.is_dir():
                report.warn("repositories", f"{name}: sibling clone not found under {workspace_root} -- skipped domain-agent check")
                continue
            agents_dir = sibling / ".claude" / "agents"
        on_disk = discover_agents(agents_dir)
        domain_on_disk = on_disk.keys() - repo_core_team.keys()
        registered = set(repo.get("domain_agents") or []) | set(repo.get("extra_qa_gates") or [])
        missing = registered - domain_on_disk
        unregistered = domain_on_disk - registered
        for n in sorted(missing):
            report.error("repositories", f"{name}: registered domain agent '{n}' has no file under {agents_dir}")
        for n in sorted(unregistered):
            report.warn("repositories", f"{name}: file {agents_dir / (n + '.md')} is not registered in domain_agents/extra_qa_gates")


def check_command_content_invariants(report: Report) -> None:
    """Machine-verify orchestration properties that are only ever asserted in hand-authored
    prose: the shared /execute command must actually contain the mandatory security-auditor
    trigger and the rerun-after-fix rule, and /dispatch must actually name both the handoff
    and handback packets and state that repo-tier agents are not directly available at the
    org root. This catches a future edit that silently drops one of these properties from the
    command file even though the registry still claims the behavior exists."""
    checks = [
        (
            REPO_ROOT / "templates" / "_shared" / ".claude" / "commands" / "execute.md",
            [
                "security-auditor",
                "rerun the QA gate",
                "Stop and report on the first failed gate",
            ],
        ),
        (
            REPO_ROOT / "templates" / "_shared" / "CLAUDE.md.template",
            [
                "never a local fork",
            ],
        ),
        (
            REPO_ROOT / "workspace" / ".claude" / "commands" / "dispatch.md",
            [
                "Handoff packet (org → repo)",
                "Handback packet (repo → org)",
                "repo-tier agents only load there",
            ],
        ),
    ]
    for path, phrases in checks:
        if not path.is_file():
            report.error("command-content", f"{path.relative_to(REPO_ROOT)} does not exist")
            continue
        text = path.read_text(encoding="utf-8")
        for phrase in phrases:
            if phrase not in text:
                report.error("command-content", f"{path.relative_to(REPO_ROOT)}: missing required phrase {phrase!r}")


def check_workspace_sync_drift(workspace_root: Path, report: Report) -> None:
    """Compare the canonical workspace/ layer here against its generated copy at the org
    workspace root -- the same comparison scripts/sync-workspace.sh --check performs (reused
    logic and the same "managed files" definition, not a second sync mechanism; this only
    reads, it never writes -- the actual copy remains that script's job, run separately with
    human confirmation). Only meaningful from a full org workspace checkout; an isolated
    .github-only clone (most CI runs) has no root copy to compare against, which is WARN, not
    a failure of this check. Drift itself is also WARN, not ERROR: refreshing the root copy is
    a separate, human-confirmed sync-workspace.sh run, so this reports pending-rollout state
    like the other not-yet-synced findings in this script."""
    src = REPO_ROOT / "workspace"
    sentinel_repos = ["CognitiveSystems", "MediaRefinery", "ModelDeck", "Uploadarr"]
    if not all((workspace_root / r).is_dir() for r in sentinel_repos):
        report.warn("workspace-sync", "no full org workspace checkout found (sibling repo clones absent) -- skipped, expected in an isolated .github-only clone")
        return
    managed = [
        p for p in src.rglob("*")
        if p.is_file() and p.name != "README.md" and ".backups" not in p.relative_to(src).parts
    ]
    drifted: list[str] = []
    missing: list[str] = []
    for path in managed:
        rel = path.relative_to(src)
        dest = workspace_root / rel
        if not dest.is_file():
            missing.append(str(rel))
        elif path.read_bytes() != dest.read_bytes():
            drifted.append(str(rel))
    if drifted or missing:
        detail = []
        if drifted:
            detail.append(f"drifted: {sorted(drifted)}")
        if missing:
            detail.append(f"missing at root: {sorted(missing)}")
        report.warn("workspace-sync", f"generated workspace root is out of sync with canonical workspace/ ({'; '.join(detail)}) -- run scripts/sync-workspace.sh to refresh (human-confirmed)")


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


def gh_api(path: str) -> tuple[Any | None, int | None, str | None]:
    """Best-effort GET against the GitHub API via gh. Returns (data, http_status, error_text).

    data is None on any failure. http_status is parsed from gh's error text when available
    (e.g. 404 = does not exist yet, 403 = permission-limited) so callers can tell "not rolled
    out yet" apart from "couldn't check" without guessing from message text.
    """
    try:
        result = subprocess.run(
            ["gh", "api", path], check=True, text=True, capture_output=True, timeout=30,
        )
    except FileNotFoundError:
        return None, None, "gh CLI not found"
    except subprocess.TimeoutExpired:
        return None, None, "timed out"
    except subprocess.CalledProcessError as exc:
        stderr = (exc.stderr or "").strip()
        match = re.search(r"HTTP (\d\d\d)", stderr)
        status = int(match.group(1)) if match else None
        return None, status, stderr or f"gh api {path} failed"
    text = result.stdout.strip()
    if not text:
        return None, 200, None
    try:
        return json.loads(text), 200, None
    except json.JSONDecodeError:
        return text, 200, None


def check_live(repos: dict[str, dict[str, Any]], report: Report) -> None:
    for name, repo in repos.items():
        live_branch = gh_default_branch(name)
        if live_branch is None:
            report.warn("live", f"{name}: could not query live default branch (permission-limited or gh unavailable)")
            continue
        expected = repo.get("default_branch")
        if live_branch != expected:
            report.error("live", f"{name}: registry says default_branch='{expected}', GitHub reports '{live_branch}'")


def check_live_security_and_rulesets(repos: dict[str, dict[str, Any]], report: Report) -> None:
    """Plan Section 6 (secret scanning/push protection/rulesets) is a separately-confirmed
    privileged rollout, not yet performed -- findings here are reporting-only (WARN), never
    ERROR, until that rollout happens. Rulesets are checked only for public repos: GitHub Free
    has no branch-protection/ruleset support on private repos (see rulesets/README.md) -- those
    rely on CI guards + auto-revert instead, so absence there is not a finding at all."""
    for name in repos:
        data, status, err = gh_api(f"repos/AutomationNexus/{name}")
        if data is None or not isinstance(data, dict):
            report.warn("live-security", f"{name}: could not query repo metadata ({err or status or 'unknown error'}) -- permission-limited")
            continue
        visibility = data.get("visibility")
        sec = data.get("security_and_analysis") or {}
        if visibility == "public":
            wanted = ("secret_scanning", "secret_scanning_push_protection", "dependabot_security_updates")
            disabled = [k for k in wanted if ((sec.get(k) or {}).get("status")) != "enabled"]
            if disabled:
                report.warn("live-security", f"{name}: public repo, security feature(s) not yet enabled: {sorted(disabled)} (plan Section 6 rollout not yet performed)")

            rulesets, rstatus, rerr = gh_api(f"repos/AutomationNexus/{name}/rulesets")
            if rulesets is None:
                report.warn("live-rulesets", f"{name}: could not query rulesets ({rerr or rstatus or 'unknown error'}) -- permission-limited")
            elif isinstance(rulesets, list) and not rulesets:
                report.warn("live-rulesets", f"{name}: public repo has no rulesets applied yet (plan Section 6/7 rollout not yet performed)")


def check_live_teams(human_team_slugs: set[str], report: Report) -> None:
    for slug in sorted(human_team_slugs):
        data, status, err = gh_api(f"orgs/AutomationNexus/teams/{slug}")
        if data is not None:
            report.warn("live-teams", f"{slug}: exists live -- once membership/permissions are verified, update its registry.yml state from 'desired' to 'active'")
        elif status == 404:
            report.warn("live-teams", f"{slug}: does not exist live yet (registry state is 'desired' -- expected pending plan Section 5 rollout)")
        else:
            report.warn("live-teams", f"{slug}: could not query ({err or 'unknown error'}) -- permission-limited")


def check_live_codeowners(repos: dict[str, dict[str, Any]], human_team_slugs: set[str], report: Report) -> None:
    import base64

    for name, repo in repos.items():
        branch = repo.get("default_branch", "main")
        data, status, err = gh_api(f"repos/AutomationNexus/{name}/contents/.github/CODEOWNERS?ref={branch}")
        if data is None:
            if status == 404:
                report.warn("live-codeowners", f"{name}: no CODEOWNERS file yet on '{branch}' (plan Section 5 rollout not yet performed)")
            else:
                report.warn("live-codeowners", f"{name}: could not query CODEOWNERS ({err or 'unknown error'}) -- permission-limited")
            continue
        if not isinstance(data, dict) or "content" not in data:
            report.warn("live-codeowners", f"{name}: CODEOWNERS content response was not in the expected shape -- skipped")
            continue
        try:
            text = base64.b64decode(data["content"]).decode("utf-8", errors="replace")
        except (ValueError, TypeError):
            report.warn("live-codeowners", f"{name}: CODEOWNERS present but could not decode content")
            continue
        referenced = set(re.findall(r"@AutomationNexus/([\w-]+)", text))
        unknown = referenced - human_team_slugs
        if unknown:
            report.error("live-codeowners", f"{name}: CODEOWNERS references unknown team slug(s) {sorted(unknown)}")


def check_live_labels(repos: dict[str, dict[str, Any]], report: Report) -> None:
    """No canonical label taxonomy is registered in registry.yml yet (plan Section 5 describes
    one as future work) -- this only confirms the labels API is reachable per repo so a future
    taxonomy check has something to validate against. Reachability failures are permission-
    limited; there is nothing to assert about label content until a taxonomy is registered."""
    for name in repos:
        data, status, err = gh_api(f"repos/AutomationNexus/{name}/labels")
        if data is None:
            report.warn("live-labels", f"{name}: could not query labels ({err or status or 'unknown error'}) -- permission-limited")


def check_live_projects(report: Report) -> None:
    query = 'query=query { organization(login: "AutomationNexus") { projectsV2(first: 20) { nodes { title } } } }'
    try:
        result = subprocess.run(
            ["gh", "api", "graphql", "-f", query], text=True, capture_output=True, timeout=30,
        )
    except (subprocess.TimeoutExpired, FileNotFoundError) as exc:
        report.warn("live-projects", f"could not query org Projects v2 ({exc}) -- permission-limited")
        return
    raw = result.stdout.strip() or result.stderr.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        report.warn("live-projects", "could not query org Projects v2 (unparseable response) -- permission-limited")
        return
    if isinstance(data, dict) and data.get("errors"):
        messages = "; ".join(str(e.get("message", e)) for e in data["errors"])
        report.warn("live-projects", f"org Projects v2 not queryable: {messages} -- permission-limited")
        return
    nodes = (((data.get("data") or {}).get("organization") or {}).get("projectsV2") or {}).get("nodes", [])
    if not nodes:
        report.warn("live-projects", "no org Projects v2 boards found yet (plan Section 5 desired boards not yet created)")


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
    repo_core_command_names = check_repo_core_commands(registry, repo_core_team, report)
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
    check_sibling_repo_domain_agents(repos, repo_core_team, args.workspace_root, report)
    check_settings_denylist(repos, args.workspace_root, report)
    check_command_content_invariants(report)
    check_workspace_sync_drift(args.workspace_root, report)

    if args.live:
        check_live(repos, report)
        check_live_security_and_rulesets(repos, report)
        check_live_teams(human_teams, report)
        check_live_codeowners(repos, human_teams, report)
        check_live_labels(repos, report)
        check_live_projects(report)

    print(report.render())
    return 1 if report.has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
