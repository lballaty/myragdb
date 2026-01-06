# Git Automatic Version Bumping System

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/GIT_AUTO_VERSION_BUMPING.md
**Description:** Complete guide to implementing automatic semantic versioning with git hooks
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-06

---

## Overview

This system automatically bumps version numbers based on conventional commit messages and includes the version changes in the same commit. No manual version management needed!

### Features

- ✅ **Semantic versioning** based on commit message conventions
- ✅ **Automatic version bumping** on every commit
- ✅ **Single commit** includes both your changes AND version bump
- ✅ **Date-based build versions** (e.g., `2026.01.06.2.31.0`)
- ✅ **Cache busting** for web assets automatically updated
- ✅ **Zero manual intervention** required

### Commit Message Conventions

```
BREAKING CHANGE: or !:  →  Major bump (2.1.0 → 3.0.0)
feat: or feature:       →  Minor bump (2.1.0 → 2.2.0)
fix: or bugfix:         →  Patch bump (2.1.0 → 2.1.1)
chore: docs: test:      →  No bump
```

---

## Architecture

### Components

1. **Version Storage** - Single source of truth for version numbers
2. **Version Bumper Script** - Python script that reads commit messages and bumps versions
3. **Git Hooks** - Trigger automatic version bumping during commits
4. **Cache Busting** - Update version query strings in HTML files

### How It Works

```
Developer commits
        ↓
prepare-commit-msg hook
        ↓
Read commit message
        ↓
Detect version bump type (major/minor/patch/none)
        ↓
Bump version in source files
        ↓
Stage version files
        ↓
Commit completes (without version files)
        ↓
post-commit hook
        ↓
Check if version files are staged
        ↓
Amend commit to include version files
        ↓
Single commit with code + version!
```

---

## Implementation Steps

### Step 1: Create Version Storage File

Create a central version file that stores all version components.

**Example:** `src/myproject/version.py`

```python
# File: /path/to/project/src/myproject/version.py
# Description: Centralized version information
# Author: Your Name <your.email@example.com>
# Created: YYYY-MM-DD

from datetime import datetime

# Version components
_BUILD_DATE = datetime(2026, 1, 6)
_MAJOR_VERSION = 2
_MINOR_VERSION = 31
_PATCH_VERSION = 0

def get_version() -> str:
    """
    Get full version string.

    Format: YYYY.MM.DD.MAJOR.MINOR.PATCH
    Example: 2026.01.06.2.31.0

    Returns:
        Version string
    """
    return f"{_BUILD_DATE.year}.{_BUILD_DATE.month:02d}.{_BUILD_DATE.day:02d}.{_MAJOR_VERSION}.{_MINOR_VERSION}.{_PATCH_VERSION}"

__version__ = get_version()
```

**Key Points:**
- Use underscored variables (`_BUILD_DATE`) for components
- Provide a `get_version()` function
- Export `__version__` for easy imports

---

### Step 2: Create Version Bumper Script

Create a Python script that reads commit messages and bumps versions.

**Location:** `scripts/bump_version.py`

```python
#!/usr/bin/env python3
# File: /path/to/project/scripts/bump_version.py
# Description: Automatic version bumping based on commit message conventions
# Author: Your Name <your.email@example.com>
# Created: YYYY-MM-DD

import re
import sys
from pathlib import Path
from datetime import datetime

# Path to version.py
REPO_ROOT = Path(__file__).parent.parent
VERSION_FILE = REPO_ROOT / "src" / "myproject" / "version.py"
HTML_FILE = REPO_ROOT / "web" / "index.html"  # Optional


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
    Update cache busting version in HTML file (optional).

    Args:
        version_string: Full version string (e.g., "2026.01.06.2.31.0")
    """
    if not HTML_FILE.exists():
        return

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
```

**Make it executable:**
```bash
chmod +x scripts/bump_version.py
```

---

### Step 3: Create prepare-commit-msg Hook

This hook runs BEFORE the commit is finalized and bumps the version.

**Location:** `.git/hooks/prepare-commit-msg`

```bash
#!/bin/bash
# File: .git/hooks/prepare-commit-msg
# Description: Automatic version bumping before commit
# Author: Your Name <your.email@example.com>
# Created: YYYY-MM-DD

COMMIT_MSG_FILE=$1
COMMIT_SOURCE=$2

# Only run for regular commits (not merge, squash, etc.)
if [ "$COMMIT_SOURCE" != "message" ] && [ "$COMMIT_SOURCE" != "template" ] && [ -n "$COMMIT_SOURCE" ]; then
    exit 0
fi

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Run version bump script
python3 "$REPO_ROOT/scripts/bump_version.py" --detect "$COMMIT_MSG_FILE"

# If version was bumped, stage the changes
if [ $? -eq 0 ]; then
    git add "$REPO_ROOT/src/myproject/version.py" "$REPO_ROOT/web/index.html" 2>/dev/null
fi

exit 0
```

**Make it executable:**
```bash
chmod +x .git/hooks/prepare-commit-msg
```

**Important:** Update these paths:
- `src/myproject/version.py` → Your version file path
- `web/index.html` → Your HTML file path (if using cache busting)

---

### Step 4: Create post-commit Hook

This hook runs AFTER the commit completes and amends it to include version files.

**Location:** `.git/hooks/post-commit`

```bash
#!/bin/bash
# File: .git/hooks/post-commit
# Description: Amend commit with version bump if files were modified
# Author: Your Name <your.email@example.com>
# Created: YYYY-MM-DD

# Get repository root
REPO_ROOT=$(git rev-parse --show-toplevel)

# Check if version files were modified by prepare-commit-msg hook
VERSION_FILE="$REPO_ROOT/src/myproject/version.py"
HTML_FILE="$REPO_ROOT/web/index.html"

# Check if these files are staged (prepare-commit-msg staged them)
if git diff --cached --quiet "$VERSION_FILE" "$HTML_FILE" 2>/dev/null; then
    # No staged changes in version files, exit
    exit 0
fi

# Version files are staged, amend the commit to include them
# Use --no-verify to avoid infinite loop
GIT_EDITOR=true git commit --amend --no-edit --no-verify

exit 0
```

**Make it executable:**
```bash
chmod +x .git/hooks/post-commit
```

**Important:** Update these paths:
- `src/myproject/version.py` → Your version file path
- `web/index.html` → Your HTML file path (if using cache busting)

---

## Testing

### Test 1: No Bump (chore commit)

```bash
echo "test" >> README.md
git add README.md
git commit -m "chore: update readme"
```

**Expected:**
```
[main abc1234] chore: update readme
 1 file changed, 1 insertion(+)
No version bump needed for this commit type
```

**Verification:** Only README.md in commit

---

### Test 2: Patch Bump (fix commit)

```bash
echo "fix" >> file.py
git add file.py
git commit -m "fix: resolve bug"
```

**Expected:**
```
[main def5678] fix: resolve bug
 1 file changed, 1 insertion(+)
Version bumped (patch): 2026.01.06.2.31.0 → 2026.01.06.2.31.1
[main ghi9012] fix: resolve bug
 3 files changed, 5 insertions(+), 4 deletions(-)
```

**Verification:**
```bash
git log -1 --stat
```

Should show:
- `file.py` (your change)
- `src/myproject/version.py` (auto-bumped)
- `web/index.html` (cache busting updated)

---

### Test 3: Minor Bump (feat commit)

```bash
echo "feature" >> feature.py
git add feature.py
git commit -m "feat: add new feature"
```

**Expected:**
```
Version bumped (minor): 2026.01.06.2.31.1 → 2026.01.06.2.32.0
```

---

### Test 4: Major Bump (breaking change)

```bash
echo "breaking" >> api.py
git add api.py
git commit -m "feat!: redesign API

BREAKING CHANGE: API endpoints completely redesigned"
```

**Expected:**
```
Version bumped (major): 2026.01.06.2.32.0 → 2026.01.06.3.0.0
```

---

## Customization

### Different Version Format

If you want `MAJOR.MINOR.PATCH` instead of date-based:

**version.py:**
```python
_MAJOR_VERSION = 1
_MINOR_VERSION = 2
_PATCH_VERSION = 3

def get_version() -> str:
    return f"{_MAJOR_VERSION}.{_MINOR_VERSION}.{_PATCH_VERSION}"
```

**bump_version.py:** Remove build date logic

---

### Additional Files to Update

If you have multiple files that need version updates:

**prepare-commit-msg:**
```bash
git add \
    "$REPO_ROOT/src/myproject/version.py" \
    "$REPO_ROOT/web/index.html" \
    "$REPO_ROOT/package.json" \
    "$REPO_ROOT/setup.py" \
    2>/dev/null
```

**post-commit:** Update the file list

---

### Custom Commit Conventions

Modify `detect_bump_type_from_commit_msg()` in `bump_version.py`:

```python
# Example: Add "hotfix:" prefix
if first_line.startswith('hotfix:'):
    return "patch"

# Example: "release:" triggers major bump
if first_line.startswith('release:'):
    return "major"
```

---

## Troubleshooting

### Version files not included in commit

**Symptom:** Version files are staged but not in the commit

**Solution:** Check that `post-commit` hook is executable:
```bash
chmod +x .git/hooks/post-commit
```

---

### Hook not running

**Symptom:** No version bump output

**Causes:**
1. Hooks not executable: `chmod +x .git/hooks/*`
2. Python3 not in PATH: Use full path in hooks
3. Wrong commit source: Hook skips merge/squash commits

---

### Infinite loop

**Symptom:** Git hangs during commit

**Cause:** `post-commit` hook triggering itself

**Solution:** Ensure `--no-verify` flag is used:
```bash
git commit --amend --no-edit --no-verify
```

---

### Version script errors

**Symptom:** `Failed to parse version.py`

**Cause:** Version file format doesn't match regex

**Solution:** Ensure exact format:
```python
_BUILD_DATE = datetime(2026, 1, 6)  # No spaces around parentheses
_MAJOR_VERSION = 2                   # No spaces around equals
```

---

## Sharing Hooks with Team

Git hooks are NOT tracked in the repository. To share with your team:

### Option 1: Scripts Directory

1. Create `scripts/git_hooks/` directory
2. Store hooks there
3. Add setup script:

**scripts/setup_hooks.sh:**
```bash
#!/bin/bash
# Copy hooks to .git/hooks/
cp scripts/git_hooks/* .git/hooks/
chmod +x .git/hooks/*
echo "Git hooks installed!"
```

4. Document in README:
```markdown
## Setup
After cloning:
```bash
./scripts/setup_hooks.sh
```
```

---

### Option 2: Git Config (Git 2.9+)

**.gitconfig:**
```
[core]
    hooksPath = .githooks
```

1. Create `.githooks/` directory in repo
2. Add hooks there
3. Tracked in git automatically

---

## Benefits

### For Developers
- ✅ Never forget to bump version
- ✅ No manual version file editing
- ✅ Consistent versioning across team
- ✅ Single commit per change

### For CI/CD
- ✅ Version always up-to-date
- ✅ Build numbers reflect commit history
- ✅ Cache busting automatic

### For Users
- ✅ Clear version history
- ✅ Semantic versioning enforced
- ✅ Easy to track changes

---

## Best Practices

1. **Always use conventional commits** - Makes version bumping predictable
2. **Test hooks after setup** - Ensure they work before relying on them
3. **Document custom conventions** - If you modify bump logic
4. **Share hooks with team** - Use setup script or hooksPath
5. **Review version changes** - Check version file in diffs

---

## Advanced Usage

### Skip version bump for specific commit

Use `--no-verify` flag:
```bash
git commit --no-verify -m "chore: temp change"
```

This skips ALL hooks, including version bumping.

---

### Manual version bump

Run the script directly:
```bash
./scripts/bump_version.py major   # Bump major version
./scripts/bump_version.py minor   # Bump minor version
./scripts/bump_version.py patch   # Bump patch version
```

---

### Check current version

**From Python:**
```python
from myproject.version import __version__
print(__version__)  # 2026.01.06.2.31.0
```

**From CLI:**
```bash
python3 -c "from myproject.version import __version__; print(__version__)"
```

---

## Migration to Other Projects

### Quick Checklist

- [ ] Copy `scripts/bump_version.py`
- [ ] Update paths in script (VERSION_FILE, HTML_FILE)
- [ ] Create version.py in your project
- [ ] Copy `.git/hooks/prepare-commit-msg`
- [ ] Copy `.git/hooks/post-commit`
- [ ] Update paths in both hooks
- [ ] Make hooks executable
- [ ] Test with dummy commit
- [ ] Document in project README

---

## Example Projects Using This System

- **MyRAGDB** - Hybrid search system with web UI
  - Version: `src/myragdb/version.py`
  - Cache busting: `web-ui/index.html`
  - Full implementation reference

---

## Questions or Issues?

Contact: libor@arionetworks.com

---

## Appendix: Complete File Listing

### Project Structure
```
myproject/
├── .git/
│   └── hooks/
│       ├── prepare-commit-msg    (executable)
│       └── post-commit           (executable)
├── scripts/
│   ├── bump_version.py           (executable)
│   └── git_hooks/                (optional - for sharing)
│       ├── prepare-commit-msg
│       └── post-commit
├── src/
│   └── myproject/
│       └── version.py
└── web/
    └── index.html                (optional - for cache busting)
```

---

**End of Document**
