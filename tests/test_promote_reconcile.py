"""Local Git fixture coverage for scripts/promote-reconcile.py."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HELPER = ROOT / "scripts" / "promote-reconcile.py"


def git(cwd: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), cwd=cwd, check=check, text=True, capture_output=True
    )


class PromoteReconcileTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")
        self.write("pyproject.toml", '[project]\nname = "fixture"\nversion = "0.0.7"\n')
        self.write("shared.txt", "main base\n")
        self.commit("main release")
        git(self.repo, "tag", "v0.0.7")
        git(self.repo, "branch", "dev")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, path: str, content: str) -> None:
        target = self.repo / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)

    def commit(self, message: str) -> None:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", message)

    def dev_change(self, changes: dict[str, str]) -> None:
        git(self.repo, "checkout", "dev")
        for path, content in changes.items():
            self.write(path, content)
        self.commit("dev feature")

    def reconcile(
        self,
        *,
        bump: str = "patch",
        excludes: str = "",
        strip: bool = False,
        expect_success: bool = True,
    ) -> subprocess.CompletedProcess[str]:
        git(self.repo, "checkout", "-B", "promote", "main")
        result = subprocess.run(
            (
                sys.executable,
                str(HELPER),
                "--main-ref",
                "main",
                "--dev-ref",
                "dev",
                "--exclude-paths",
                excludes,
                "--strip-dev-only-paths",
                str(strip).lower(),
                "--bump-type",
                bump,
            ),
            cwd=self.repo,
            text=True,
            capture_output=True,
        )
        if expect_success:
            self.assertEqual(result.returncode, 0, result.stderr)
            git(self.repo, "add", "-A")
            git(self.repo, "commit", "-m", "reconcile")
        return result

    def test_patch_and_minor_use_main_tag_not_stale_dev_version(self) -> None:
        self.dev_change(
            {
                "pyproject.toml": '[project]\nname = "fixture"\nversion = "0.0.5"\n',
                "feature.txt": "dev feature\n",
            }
        )
        git(self.repo, "checkout", "main")
        self.write("released-on-main.txt", "main-only release content\n")
        self.commit("main release after stale dev")
        patch = self.reconcile(bump="patch")
        self.assertEqual(patch.stdout.strip(), "0.0.8")
        self.assertIn('version = "0.0.8"', (self.repo / "pyproject.toml").read_text())
        self.assertEqual((self.repo / "feature.txt").read_text(), "dev feature\n")
        self.assertEqual(git(self.repo, "merge-base", "main", "promote").stdout.strip(), git(self.repo, "rev-parse", "main").stdout.strip())

        git(self.repo, "checkout", "main")
        minor = self.reconcile(bump="minor")
        self.assertEqual(minor.stdout.strip(), "0.1.1")
        self.assertIn('version = "0.1.1"', (self.repo / "pyproject.toml").read_text())

    def test_none_leaves_stale_dev_version_untouched(self) -> None:
        self.dev_change(
            {
                "pyproject.toml": '[project]\nname = "fixture"\nversion = "0.0.5"\n',
                "feature.txt": "dev feature\n",
            }
        )
        result = self.reconcile(bump="none")
        self.assertEqual(result.stdout.strip(), "")
        self.assertIn('version = "0.0.5"', (self.repo / "pyproject.toml").read_text())

    def test_dev_wins_ordinary_conflicts_but_main_wins_exclusions(self) -> None:
        self.dev_change({"shared.txt": "dev content\n", "owned.txt": "dev owned\n"})
        git(self.repo, "checkout", "main")
        self.write("shared.txt", "main content\n")
        self.write("owned.txt", "main owned\n")
        self.commit("main changed shared paths")

        self.reconcile(bump="none", excludes="owned.txt\nnew-owned.txt")
        self.assertEqual((self.repo / "shared.txt").read_text(), "dev content\n")
        self.assertEqual((self.repo / "owned.txt").read_text(), "main owned\n")
        self.assertFalse((self.repo / "new-owned.txt").exists())

    def test_excluded_dev_created_path_is_retained(self) -> None:
        self.dev_change({"new-owned.txt": "dev introduces it\n"})
        self.reconcile(bump="none", excludes="new-owned.txt")
        self.assertEqual((self.repo / "new-owned.txt").read_text(), "dev introduces it\n")

    def test_strip_dev_only_paths_and_resolve_their_conflicts(self) -> None:
        self.dev_change(
            {
                ".github/dev-only-paths": "# Developer tooling\n^CLAUDE\\.md$\n^\\.claude/\n",
                "CLAUDE.md": "development instructions\n",
                ".claude/settings.json": "{}\n",
                "feature.txt": "keep me\n",
            }
        )
        git(self.repo, "checkout", "main")
        self.write("CLAUDE.md", "released instructions\n")
        self.write(".claude/settings.json", '{"main": true}\n')
        self.commit("main changes dev-only paths")
        self.reconcile(bump="none", strip=True)
        self.assertFalse((self.repo / "CLAUDE.md").exists())
        self.assertFalse((self.repo / ".claude/settings.json").exists())
        self.assertEqual((self.repo / "feature.txt").read_text(), "keep me\n")
        self.assertFalse((self.repo / ".git/MERGE_HEAD").exists())


    def test_main_pyproject_fallback_and_patch_rollover(self) -> None:
        git(self.repo, "tag", "-d", "v0.0.7")
        self.write("pyproject.toml", '[project]\nname = "fixture"\nversion = "0.0.99"\n')
        self.commit("main fallback version")
        self.dev_change({"feature.txt": "dev feature\n"})
        result = self.reconcile(bump="patch")
        self.assertEqual(result.stdout.strip(), "0.1.1")

    def test_first_release_fallback_ignores_malformed_tags(self) -> None:
        git(self.repo, "tag", "-d", "v0.0.7")
        git(self.repo, "tag", "v1.2.bad")
        git(self.repo, "rm", "pyproject.toml")
        self.commit("main first release")
        self.dev_change({"feature.txt": "dev feature\n"})
        result = self.reconcile(bump="patch")
        self.assertEqual(result.stdout.strip(), "")
        self.assertFalse((self.repo / "pyproject.toml").exists())

    def test_invalid_version_line_fails_closed(self) -> None:
        self.dev_change({"pyproject.toml": "[project]\nname = \"fixture\"\n"})
        result = self.reconcile(bump="patch", expect_success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("has no version", result.stderr)

    def test_non_dev_only_directory_file_conflict_fails_and_aborts(self) -> None:
        self.dev_change({"conflict/file.txt": "dev content\n"})
        git(self.repo, "checkout", "main")
        self.write("conflict", "main file\n")
        self.commit("main adds conflicting file")
        result = self.reconcile(bump="none", expect_success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("conflict", result.stderr)
        self.assertFalse((self.repo / ".git/MERGE_HEAD").exists())

    def test_broad_dev_only_pattern_applies_to_all_matching_conflicts(self) -> None:
        self.dev_change(
            {
                ".github/dev-only-paths": "^generated/",
                "generated/one.txt": "dev one\n",
                "generated/two.txt": "dev two\n",
            }
        )
        git(self.repo, "checkout", "main")
        self.write("generated/one.txt", "main one\n")
        self.write("generated/two.txt", "main two\n")
        self.commit("main changes generated paths")
        self.reconcile(bump="none", strip=True)
        self.assertFalse((self.repo / "generated/one.txt").exists())
        self.assertFalse((self.repo / "generated/two.txt").exists())

    def test_invalid_manifest_regex_fails_closed(self) -> None:
        self.dev_change({".github/dev-only-paths": "[not-valid\n"})
        result = self.reconcile(bump="none", strip=True, expect_success=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Invalid .github/dev-only-paths pattern", result.stderr)
        self.assertFalse((self.repo / ".git/MERGE_HEAD").exists())


if __name__ == "__main__":
    unittest.main()
