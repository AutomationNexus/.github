"""Regression coverage for the reusable main dev-only-file guard."""

from __future__ import annotations

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github" / "workflows" / "ci.yml"


def git(
    cwd: Path, *args: str, check: bool = True
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ("git", *args), cwd=cwd, check=check, text=True, capture_output=True
    )


def write(repo: Path, path: str, content: str) -> None:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def dev_only_matches(repo: Path, paths: list[str], manifest_ref: str = "HEAD") -> list[str]:
    manifest = git(
        repo, "show", f"{manifest_ref}:.github/dev-only-paths"
    ).stdout.splitlines()
    patterns = [
        re.compile(line, re.IGNORECASE)
        for line in manifest
        if line and not line.startswith("#")
    ]
    return [path for path in paths if any(pattern.search(path) for pattern in patterns)]


class MainFileGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.repo = Path(self.tmp.name)
        git(self.repo, "init", "--initial-branch=main")
        git(self.repo, "config", "user.name", "Test User")
        git(self.repo, "config", "user.email", "test@example.com")
        write(self.repo, ".github/dev-only-paths", "^CLAUDE\\.md$\n^\\.claude/\n")
        write(self.repo, "CLAUDE.md", "legacy developer instructions\n")
        write(self.repo, ".claude/settings.json", "{}\n")
        write(self.repo, "app.txt", "main baseline\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "main baseline")

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def changed_paths(self, diff_filter: str) -> list[str]:
        return git(
            self.repo,
            "diff",
            "--name-only",
            f"--diff-filter={diff_filter}",
            "main...HEAD",
        ).stdout.splitlines()

    def test_workflow_checks_only_added_or_modified_paths(self) -> None:
        content = WORKFLOW.read_text(encoding="utf-8")
        command = "git diff --name-only --diff-filter=AM origin/main...HEAD"
        self.assertEqual(content.count(command), 2)
        self.assertEqual(
            content.count("git cat-file -e origin/main:.github/dev-only-paths 2>/dev/null"), 1
        )
        self.assertIn(
            'git show origin/main:.github/dev-only-paths > "$base_manifest"', content
        )
        self.assertIn(
            'git show "origin/${{ github.base_ref }}:.github/dev-only-paths" > "$base_manifest"',
            content,
        )

    def test_promotion_cleanup_allows_deletions_and_leaves_clean_tree(self) -> None:
        git(self.repo, "checkout", "-b", "promote")
        (self.repo / "CLAUDE.md").unlink()
        (self.repo / ".claude/settings.json").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "remove dev-only files")

        self.assertEqual(dev_only_matches(self.repo, self.changed_paths("AM")), [])
        self.assertEqual(
            dev_only_matches(self.repo, git(self.repo, "ls-files").stdout.splitlines()), []
        )

    def test_guard_rejects_removing_the_existing_manifest(self) -> None:
        git(self.repo, "checkout", "-b", "feature")
        (self.repo / ".github/dev-only-paths").unlink()
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "remove manifest")

        self.assertEqual(
            git(
                self.repo,
                "cat-file",
                "-e",
                "main:.github/dev-only-paths",
                check=False,
            ).returncode,
            0,
        )
        self.assertFalse((self.repo / ".github/dev-only-paths").is_file())

    def test_guard_uses_base_manifest_when_pull_request_weakens_patterns(self) -> None:
        git(self.repo, "checkout", "-b", "feature")
        write(self.repo, ".github/dev-only-paths", "^\\.claude/\n")
        write(self.repo, "CLAUDE.md", "modified developer instructions\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "weaken manifest")

        changed = self.changed_paths("AM")
        self.assertEqual(dev_only_matches(self.repo, changed), [])
        self.assertEqual(
            dev_only_matches(self.repo, changed, manifest_ref="main"), ["CLAUDE.md"]
        )
        self.assertEqual(
            dev_only_matches(
                self.repo,
                git(self.repo, "ls-files").stdout.splitlines(),
                manifest_ref="main",
            ),
            [".claude/settings.json", "CLAUDE.md"],
        )

    def test_guard_rejects_added_or_modified_dev_only_paths(self) -> None:
        git(self.repo, "checkout", "-b", "feature")
        write(self.repo, "CLAUDE.md", "modified developer instructions\n")
        write(self.repo, ".claude/new-settings.json", "{}\n")
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-m", "modify dev-only files")

        self.assertEqual(
            dev_only_matches(self.repo, self.changed_paths("AM")),
            [".claude/new-settings.json", "CLAUDE.md"],
        )


if __name__ == "__main__":
    unittest.main()
