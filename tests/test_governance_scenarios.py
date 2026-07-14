"""Scenario fixtures for the AI/human governance orchestration model (plan Sec 13).

Each test asserts routing, required agents, sequencing, confirmation points, and
expected artifacts for one realistic task shape against the real, committed
governance/registry.yml and canonical docs -- structurally, read-only. No agent is
dispatched, no branch is touched, no GitHub call is made.
"""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = REPO_ROOT / "scripts" / "validate-governance.py"
EXECUTE_MD = REPO_ROOT / "templates" / "_shared" / ".claude" / "commands" / "execute.md"
SHARED_CLAUDE_TEMPLATE = REPO_ROOT / "templates" / "_shared" / "CLAUDE.md.template"
WORKSPACE_CLAUDE = REPO_ROOT / "workspace" / "CLAUDE.md"


def _load_validator_module() -> Any:
    # scripts/validate-governance.py has a hyphen in its filename, so it can't be
    # imported normally -- load it by path instead of duplicating its parsing logic.
    spec = importlib.util.spec_from_file_location("validate_governance", VALIDATOR_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


VALIDATOR = _load_validator_module()


class GovernanceScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.registry: dict[str, Any] = VALIDATOR.load_yaml(VALIDATOR.REGISTRY_PATH)
        cls.repos_by_name = {r["repo"]: r for r in cls.registry["repositories"]}
        cls.org_commands_by_name = {c["name"]: c for c in cls.registry["org_commands"]}
        cls.repo_core_team_names = {a["name"] for a in cls.registry["repo_core_team"]}
        cls.repo_core_commands_by_name = {c["name"]: c for c in cls.registry["repo_core_commands"]}
        cls.exceptions_by_id = {e["id"]: e for e in cls.registry["exceptions"]}

    def repo_roster(self, repo_name: str) -> set[str]:
        repo = self.repos_by_name[repo_name]
        return (
            self.repo_core_team_names
            | set(repo.get("domain_agents") or [])
            | set(repo.get("extra_qa_gates") or [])
        )

    # 1. Trivial repo fix -----------------------------------------------------
    def test_trivial_repo_fix_routes_track_a(self) -> None:
        cmd = self.repo_core_commands_by_name["/execute"]
        self.assertIn("A", cmd["risk_tracks"])
        self.assertEqual(cmd["owner"], "main-session")
        self.assertEqual(cmd["confirmation_class"], "repo-write")
        self.assertIn("pr", cmd["outputs"])
        # Track A's only mandatory role is the shared QA gate -- no domain dispatch.
        self.assertIn("qa-gatekeeper", self.repo_roster("CognitiveSystems"))
        execute_doc = EXECUTE_MD.read_text(encoding="utf-8")
        self.assertIn("Track A", execute_doc)
        self.assertIn("Skip steps 2 and 4", execute_doc)
        template_doc = SHARED_CLAUDE_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn("No subagent dispatch beyond QA", template_doc)

    # 2. Multi-domain repo feature ---------------------------------------------
    def test_multi_domain_feature_routes_track_c_full_roster(self) -> None:
        cmd = self.repo_core_commands_by_name["/execute"]
        self.assertIn("C", cmd["risk_tracks"])
        roster = self.repo_roster("ModelDeck")
        for required in ("architect", "mqtt-engineer", "addon-engineer", "reviewer", "qa-gatekeeper", "security-auditor"):
            self.assertIn(required, roster, f"{required} not registered for ModelDeck")
        self.assertIn("addon-qa-gatekeeper", self.repos_by_name["ModelDeck"].get("extra_qa_gates", []))
        execute_doc = EXECUTE_MD.read_text(encoding="utf-8")
        self.assertIn("Track C", execute_doc)
        self.assertIn("dispatch `architect` first", execute_doc)

    # 3. Shared-workflow + two-consumer rollout --------------------------------
    def test_shared_workflow_rollout_routes_through_dispatch_to_consumers(self) -> None:
        dispatch = self.org_commands_by_name["/dispatch"]
        self.assertEqual(dispatch["owner"], "chief-architect")
        self.assertEqual(dispatch.get("handoff_handback"), "required")
        self.assertIn("handoff-brief", dispatch["outputs"])
        self.assertEqual(self.repos_by_name[".github"]["sync_role"], "canonical-source")
        for consumer in ("MediaRefinery", "Uploadarr"):
            repo = self.repos_by_name[consumer]
            self.assertEqual(repo["sync_role"], "consumer")
            self.assertEqual(repo["team_policy"], "full-core")

    # 4. Security-sensitive workflow change ------------------------------------
    def test_security_sensitive_workflow_change_requires_security_auditor(self) -> None:
        self.assertIn("security-auditor", self.repo_core_team_names)
        meta = self.repos_by_name[".github"]
        self.assertEqual(meta["team_policy"], "meta-core")
        self.assertIn("workflow-engineer", meta["domain_agents"])
        execute_doc = EXECUTE_MD.read_text(encoding="utf-8")
        self.assertIn("also dispatch `security-auditor`", execute_doc)
        self.assertIn("workflows", execute_doc)

    # 5. Promote operation ------------------------------------------------------
    def test_promote_operation_requires_human_confirmation(self) -> None:
        release = self.repo_core_commands_by_name["/release"]
        self.assertEqual(release["risk_tracks"], ["D"])
        self.assertEqual(release["confirmation_class"], "human-confirmation-required")
        self.assertEqual(release["owner"], "main-session")
        self.assertIn("gate-by-gate-status", release["outputs"])
        promote = self.org_commands_by_name["/promote"]
        self.assertEqual(promote["owner"], "release-manager")
        self.assertEqual(promote["confirmation_class"], "human-confirmation-required")
        self.assertIn("gate-by-gate-status", promote["outputs"])

    # 6. Template sync ------------------------------------------------------------
    def test_template_sync_is_human_confirmed_direct_push_exception(self) -> None:
        sync = self.org_commands_by_name["/sync-templates"]
        self.assertEqual(sync["owner"], "template-steward")
        self.assertEqual(sync["confirmation_class"], "human-confirmation-required")
        self.assertIn("sync-templates-direct-push", self.exceptions_by_id)
        template_repos = [r for r in self.registry["repositories"] if r["class"] == "template"]
        self.assertEqual(len(template_repos), 5)
        for repo in template_repos:
            self.assertEqual(repo["sync_role"], "template-target")

    # 7. Collision with dirty work -------------------------------------------------
    def test_collision_protocol_is_documented_and_inherited(self) -> None:
        workspace_doc = WORKSPACE_CLAUDE.read_text(encoding="utf-8").lower()
        self.assertIn("mandatory collision protocol", workspace_doc)
        template_doc = SHARED_CLAUDE_TEMPLATE.read_text(encoding="utf-8").lower()
        self.assertIn("mandatory collision protocol", template_doc)
        self.assertIn("worktree", template_doc)

    # 8. Permission-limited GitHub query ---------------------------------------------
    def test_permission_limited_is_a_first_class_verification_state(self) -> None:
        self.assertIn("permission-limited", VALIDATOR.VERIFICATION_STATES)
        validator_src = VALIDATOR_PATH.read_text(encoding="utf-8")
        # Auth/scope failures in every live-check function must WARN, never ERROR.
        self.assertIn('report.warn("live-security"', validator_src)
        self.assertIn('report.warn("live-teams"', validator_src)
        self.assertNotIn('report.error("live-security"', validator_src)
        self.assertNotIn('report.error("live-teams"', validator_src)

    # 9. ARCRunner minimal-team task ---------------------------------------------------
    def test_arcrunner_minimal_team_is_a_registered_exception(self) -> None:
        arcrunner = self.repos_by_name["ARCRunner"]
        self.assertEqual(arcrunner["team_policy"], "minimal")
        self.assertEqual(arcrunner.get("domain_agents"), [])
        self.assertEqual(arcrunner["state"], "exception")
        exception = arcrunner["exception"]
        for key in ("rationale", "owner", "review_trigger"):
            self.assertTrue(exception.get(key), f"ARCRunner exception missing {key}")


if __name__ == "__main__":
    unittest.main()
