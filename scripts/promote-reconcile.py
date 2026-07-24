#!/usr/bin/env python3
"""Build the local tree for a dev-to-main promotion reconciliation branch.

This helper is deliberately local-only: the reusable workflow owns authentication,
pushing, PR creation, CI polling, retries, and merging. It expects the caller to
checkout a temporary branch at the requested main ref, then it merges the requested
dev ref and applies the policy-owned changes to that working tree.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


class ReconcileError(RuntimeError):
    """The promotion tree could not be built deterministically."""


def run(*args: str, check: bool = True, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        check=check,
        text=True,
        capture_output=capture_output,
    )


def unresolved_paths() -> list[str]:
    result = run("git", "diff", "--name-only", "--diff-filter=U", capture_output=True)
    return [path for path in result.stdout.splitlines() if path]


def dev_only_patterns() -> list[re.Pattern[str]]:
    manifest = Path(".github/dev-only-paths")
    if not manifest.is_file():
        return []

    patterns = [
        line.strip()
        for line in manifest.read_text().splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    try:
        return [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    except re.error as error:
        raise ReconcileError(f"Invalid .github/dev-only-paths pattern: {error}") from error


def merge_dev(dev_ref: str, strip_dev_only: bool) -> None:
    """Merge dev into the main-based branch, preferring dev except for stripped paths."""
    result = run(
        "git",
        "merge",
        "--no-ff",
        "--no-commit",
        "-X",
        "theirs",
        dev_ref,
        check=False,
    )
    conflicts = unresolved_paths()
    had_conflicts = bool(conflicts)
    patterns = dev_only_patterns() if strip_dev_only else []
    stripped_conflicts = [
        path for path in conflicts if any(pattern.search(path) for pattern in patterns)
    ]
    if stripped_conflicts:
        print(
            "Resolving dev-only merge conflicts by removing: " + ", ".join(stripped_conflicts),
            file=sys.stderr,
        )
        run("git", "rm", "-q", "-f", "--", *stripped_conflicts)
        conflicts = unresolved_paths()

    # Git returns nonzero when it stops for conflicts, even if every permitted
    # dev-only path above was resolved by deletion. Reject failures that did not
    # expose conflicts, and reject any conflicts that remain after that policy.
    if (result.returncode != 0 and not had_conflicts) or conflicts:
        joined = ", ".join(conflicts) if conflicts else "unknown paths"
        run("git", "merge", "--abort", check=False)
        raise ReconcileError(
            "Could not deterministically merge dev onto main; unresolved paths: " + joined
        )


def restore_main_owned_paths(main_ref: str, exclude_paths: str) -> None:
    for path in exclude_paths.splitlines():
        path = path.strip()
        if not path:
            continue
        exists = run(
            "git", "cat-file", "-e", f"{main_ref}:{path}", check=False
        ).returncode == 0
        if exists:
            print(f"Preserving main-owned path: {path}", file=sys.stderr)
            run("git", "checkout", main_ref, "--", path)
        else:
            print(
                f"Main does not contain excluded path {path}; keeping dev's introduced copy.",
                file=sys.stderr,
            )


def strip_dev_only_paths() -> None:
    manifest = Path(".github/dev-only-paths")
    if not manifest.is_file():
        return

    patterns = dev_only_patterns()
    tracked = run("git", "ls-files", capture_output=True).stdout.splitlines()
    paths = [path for path in tracked if any(pattern.search(path) for pattern in patterns)]
    if paths:
        print("Removing dev-only paths: " + ", ".join(paths), file=sys.stderr)
        run("git", "rm", "-q", "-f", "--", *paths)


def version_from_main(main_ref: str, version_file: str = "") -> tuple[int, int, int]:
    tags = run(
        "git", "tag", "--list", "v*.*.*", "--merged", main_ref, capture_output=True
    ).stdout.splitlines()
    versions = [
        tuple(int(group) for group in match.groups())
        for tag in tags
        if (match := re.fullmatch(r"v(\d+)\.(\d+)\.(\d+)", tag.strip()))
    ]
    if versions:
        return max(versions)

    if version_file:
        # Bare X.Y.Z file (no pyproject.toml in this repo). Missing file on main is not
        # an error -- git show returns nonzero, stdout is empty, and we fall through to
        # the 0.0.0 first-release seed below.
        result = run("git", "show", f"{main_ref}:{version_file}", check=False, capture_output=True)
        match = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", result.stdout.strip())
    else:
        result = run("git", "show", f"{main_ref}:pyproject.toml", check=False, capture_output=True)
        match = re.search(
            r'(?m)^version\s*=\s*"(\d+)\.(\d+)\.(\d+)"', result.stdout
        )
    if match:
        return tuple(int(group) for group in match.groups())
    return 0, 0, 0


def _bump_tuple(version: tuple[int, int, int], bump_type: str) -> tuple[int, int, int]:
    """Shared patch/minor/major/wrap-at-99 math for both version sources."""
    x, y, z = version
    if bump_type == "major":
        return x + 1, 1, 1
    if bump_type == "minor":
        return x, y + 1, 1
    if bump_type == "patch":
        z += 1
        if z > 99:
            y += 1
            z = 1
        return x, y, z
    raise ReconcileError(f"Unsupported bump type: {bump_type}")


def bump_version(main_ref: str, bump_type: str) -> str | None:
    pyproject = Path("pyproject.toml")
    if bump_type == "none" or not pyproject.is_file():
        return None

    x, y, z = _bump_tuple(version_from_main(main_ref), bump_type)
    new_version = f"{x}.{y}.{z}"
    content = pyproject.read_text()
    updated, count = re.subn(
        r'(?m)^(version\s*=\s*)"\d+\.\d+\.\d+"',
        lambda match: f'{match.group(1)}"{new_version}"',
        content,
        count=1,
    )
    if count == 0:
        raise ReconcileError('pyproject.toml has no version = "X.Y.Z" line to bump')
    pyproject.write_text(updated)
    return new_version


def bump_version_file(main_ref: str, bump_type: str, version_file: str) -> str | None:
    """Mirror of bump_version() for repos with no pyproject.toml. Creates version_file
    with the computed version if it doesn't already exist -- no manual seeding required.
    """
    if bump_type == "none":
        return None

    x, y, z = _bump_tuple(version_from_main(main_ref, version_file), bump_type)
    new_version = f"{x}.{y}.{z}"
    Path(version_file).write_text(new_version + "\n")
    return new_version


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--main-ref", required=True)
    parser.add_argument("--dev-ref", required=True)
    parser.add_argument("--exclude-paths", default="")
    parser.add_argument("--strip-dev-only-paths", choices=("true", "false"), required=True)
    parser.add_argument("--bump-type", choices=("patch", "minor", "major", "none"), required=True)
    parser.add_argument(
        "--version-file",
        default="",
        help="Bare X.Y.Z file (e.g. VERSION) to bump instead of pyproject.toml, for a repo "
        "with no pyproject.toml. Empty (default) preserves the existing pyproject.toml path.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        strip_dev_only = args.strip_dev_only_paths == "true"
        merge_dev(args.dev_ref, strip_dev_only)
        restore_main_owned_paths(args.main_ref, args.exclude_paths)
        if strip_dev_only:
            strip_dev_only_paths()
        if args.version_file:
            new_version = bump_version_file(args.main_ref, args.bump_type, args.version_file)
        else:
            new_version = bump_version(args.main_ref, args.bump_type)
    except (ReconcileError, subprocess.CalledProcessError) as error:
        run("git", "merge", "--abort", check=False)
        print(f"::error::{error}", file=sys.stderr)
        return 1

    if new_version:
        print(new_version)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
