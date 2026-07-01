#!/usr/bin/env python3
"""Compute stable HA add-on pin updates for a release version."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import yaml

# REPLACE_ME: set these to your add-on folder name and Docker image before use.
ADDON_CONFIG_REL = Path("REPLACE_ME_ADDON_DIR/config.yaml")
ADDON_DOCKERFILE_REL = Path("REPLACE_ME_ADDON_DIR/Dockerfile")
BUILD_FROM_LINE = re.compile(r"^(ARG BUILD_FROM=)(.+)$", re.MULTILINE)
IMAGE_PREFIX = "ghcr.io/automationnexus/REPLACE_ME_IMAGE_NAME:v"


def parse_version(tag: str) -> str:
    """Strip optional v prefix and validate semver X.Y.Z."""
    tag = tag.strip()
    if tag.startswith("v"):
        tag = tag[1:]
    if not re.fullmatch(r"\d+\.\d+\.\d+", tag):
        raise ValueError(f"tag must be semver vX.Y.Z, got {tag!r}")
    if tag == "0.0.0":
        raise ValueError(
            "tag resolved to v0.0.0 — this is the workflow fallback sentinel, not a real "
            "release. Ensure GH_TOKEN is set and the release tag exists before syncing."
        )
    return tag


def read_haos_state(haos_root: Path) -> tuple[str, str]:
    """Return (config version, BUILD_FROM image) from the add-on tree."""
    config_path = haos_root / ADDON_CONFIG_REL
    docker_path = haos_root / ADDON_DOCKERFILE_REL
    addon = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    version = str(addon["version"])
    docker_text = docker_path.read_text(encoding="utf-8")
    match = BUILD_FROM_LINE.search(docker_text)
    if not match:
        raise ValueError(f"BUILD_FROM not found in {docker_path}")
    return version, match.group(2).strip()


def apply_stable_pin(haos_root: Path, version: str) -> bool:
    """Update the stable pin files. Returns True if files changed.

    Stable add-on version is always exactly the parent release version (bare
    X.Y.Z, no packaging-revision suffix) — an add-on-only packaging change is
    never released standalone; it ships bundled at the next real release, so
    there's nothing to track separately here.
    """
    config_path = haos_root / ADDON_CONFIG_REL
    docker_path = haos_root / ADDON_DOCKERFILE_REL
    expected_image = f"{IMAGE_PREFIX}{version}"

    current_version, current_build = read_haos_state(haos_root)
    if current_version == version and current_build == expected_image:
        return False

    addon = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    addon["version"] = version
    text = yaml.safe_dump(addon, sort_keys=False)
    text = re.sub(
        r"^version: .*$",
        f'version: "{version}"',
        text,
        count=1,
        flags=re.MULTILINE,
    )
    config_path.write_text(text, encoding="utf-8")

    docker_text = docker_path.read_text(encoding="utf-8")
    new_docker = BUILD_FROM_LINE.sub(
        rf"\1{expected_image}",
        docker_text,
        count=1,
    )
    docker_path.write_text(new_docker, encoding="utf-8")
    return True


def main() -> int:
    """CLI entry: sync or check the stable add-on pin against a release tag."""
    parser = argparse.ArgumentParser(description="Sync stable add-on pin")
    parser.add_argument(
        "haos_root",
        type=Path,
        help="Path to repo root containing the add-on folder (use '.' in-repo)",
    )
    parser.add_argument("tag", help="Release tag (e.g. v0.0.2)")
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Exit 0 if already synced, 2 if update needed",
    )
    args = parser.parse_args()
    version = parse_version(args.tag)
    haos_root = args.haos_root.resolve()

    if args.check_only:
        current_version, current_build = read_haos_state(haos_root)
        expected = f"{IMAGE_PREFIX}{version}"
        if current_version == version and current_build == expected:
            print("already synced")
            return 0
        print(f"needs sync: version={current_version} build_from={current_build}")
        return 2

    changed = apply_stable_pin(haos_root, version)
    if changed:
        print(f"updated pin to v{version}")
    else:
        print("no changes needed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
