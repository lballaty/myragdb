#!/usr/bin/env python3
# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/scripts/bump_version.py
# Description: Automatic version bumping based on commit message conventions
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-05

import re
import sys
from pathlib import Path
from datetime import datetime

# Path to version.py
REPO_ROOT = Path(__file__).parent.parent
VERSION_FILE = REPO_ROOT / "src" / "myragdb" / "version.py"
HTML_FILE = REPO_ROOT / "web-ui" / "index.html"


def read_current_version():
    """
    Read current version from version.py.

    Returns:
        tuple: (year, month, day, major, minor, patch)
    """
    with open(VERSION_FILE, 'r') as f:
        content = f.read()

    # Extract version components
    build_date_match = re.search(r'_BUILD_DATE = datetime\((\d+), (\d+), (\d+)\)', content)
    major_match = re.search(r'_MAJOR_VERSION = (\d+)', content)
    minor_match = re.search(r'_MINOR_VERSION = (\d+)', content)
    patch_match = re.search(r'_PATCH_VERSION = (\d+)', content)

    if not all([build_date_match, major_match, minor_match, patch_match]):
        raise ValueError("Failed to parse version.py")

    return (
        int(build_date_match.group(1)),  # year
        int(build_date_match.group(2)),  # month
        int(build_date_match.group(3)),  # day
        int(major_match.group(1)),       # major
        int(minor_match.group(1)),       # minor
        int(patch_match.group(1))        # patch
    )


def write_new_version(year, month, day, major, minor, patch):
    """
    Write new version to version.py.

    Args:
        year, month, day: Build date components
        major, minor, patch: Version components
    """
    with open(VERSION_FILE, 'r') as f:
        content = f.read()

    # Update version components
    content = re.sub(
        r'_BUILD_DATE = datetime\(\d+, \d+, \d+\)',
        f'_BUILD_DATE = datetime({year}, {month}, {day})',
        content
    )
    content = re.sub(
        r'_MAJOR_VERSION = \d+',
        f'_MAJOR_VERSION = {major}',
        content
    )
    content = re.sub(
        r'_MINOR_VERSION = \d+',
        f'_MINOR_VERSION = {minor}',
        content
    )
    content = re.sub(
        r'_PATCH_VERSION = \d+',
        f'_PATCH_VERSION = {patch}',
        content
    )

    with open(VERSION_FILE, 'w') as f:
        f.write(content)

    return f"{year}.{month:02d}.{day:02d}.{major}.{minor}.{patch}"


def update_cache_busting(version_string):
    """
    Update cache busting version in HTML file.

    Args:
        version_string: Full version string (e.g., "2026.01.05.1.0.3")
    """
    with open(HTML_FILE, 'r') as f:
        content = f.read()

    # Update CSS cache busting
    content = re.sub(
        r'static/css/styles\.css\?v=[0-9.]+',
        f'static/css/styles.css?v={version_string}',
        content
    )

    # Update JS cache busting
    content = re.sub(
        r'static/js/app\.js\?v=[0-9.]+',
        f'static/js/app.js?v={version_string}',
        content
    )

    with open(HTML_FILE, 'w') as f:
        f.write(content)


def bump_version(bump_type="patch"):
    """
    Bump version based on type.

    Args:
        bump_type: One of "major", "minor", "patch" (default: "patch")

    Returns:
        str: New version string
    """
    year, month, day, major, minor, patch = read_current_version()
    today = datetime.now()

    # Update build date to today
    new_year = today.year
    new_month = today.month
    new_day = today.day

    # Bump version based on type
    if bump_type == "major":
        major += 1
        minor = 0
        patch = 0
    elif bump_type == "minor":
        minor += 1
        patch = 0
    elif bump_type == "patch":
        patch += 1
    else:
        raise ValueError(f"Invalid bump type: {bump_type}")

    # Write new version
    new_version = write_new_version(new_year, new_month, new_day, major, minor, patch)

    # Update cache busting
    update_cache_busting(new_version)

    return new_version


def detect_bump_type_from_commit_msg(commit_msg):
    """
    Detect version bump type from commit message.

    Conventions:
    - BREAKING CHANGE: or !: → major
    - feat: or feature: → minor
    - fix: or bugfix: or patch: → patch (default)
    - chore:, docs:, style:, refactor:, test: → no bump

    Args:
        commit_msg: Commit message text

    Returns:
        str: One of "major", "minor", "patch", or None (no bump)
    """
    first_line = commit_msg.split('\n')[0].lower()

    # Check for breaking change (major bump)
    if 'breaking change:' in commit_msg.lower() or first_line.endswith('!:'):
        return "major"

    # Check for feature (minor bump)
    if first_line.startswith(('feat:', 'feature:')):
        return "minor"

    # Check for fix/patch (patch bump)
    if first_line.startswith(('fix:', 'bugfix:', 'patch:')):
        return "patch"

    # No bump for chore, docs, style, refactor, test
    if first_line.startswith(('chore:', 'docs:', 'style:', 'refactor:', 'test:')):
        return None

    # Default: patch bump for any other commit
    return "patch"


def main():
    """
    Main entry point for version bumping.

    Usage:
        bump_version.py [major|minor|patch]
        bump_version.py --detect <commit-msg-file>
    """
    if len(sys.argv) < 2:
        print("Usage: bump_version.py [major|minor|patch] OR --detect <commit-msg-file>")
        sys.exit(1)

    if sys.argv[1] == "--detect":
        # Read commit message from file
        if len(sys.argv) < 3:
            print("Error: --detect requires commit message file path")
            sys.exit(1)

        commit_msg_file = Path(sys.argv[2])
        with open(commit_msg_file, 'r') as f:
            commit_msg = f.read()

        bump_type = detect_bump_type_from_commit_msg(commit_msg)

        if bump_type is None:
            print("No version bump needed for this commit type")
            sys.exit(0)

        old_version = ".".join(map(str, read_current_version()))
        new_version = bump_version(bump_type)
        print(f"Version bumped ({bump_type}): {old_version} → {new_version}")
    else:
        bump_type = sys.argv[1]
        if bump_type not in ["major", "minor", "patch"]:
            print(f"Error: Invalid bump type '{bump_type}'. Must be major, minor, or patch.")
            sys.exit(1)

        old_version = ".".join(map(str, read_current_version()))
        new_version = bump_version(bump_type)
        print(f"Version bumped ({bump_type}): {old_version} → {new_version}")


if __name__ == "__main__":
    main()
