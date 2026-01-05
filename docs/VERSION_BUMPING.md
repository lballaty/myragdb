# Version Bumping Guide

**File:** /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/docs/VERSION_BUMPING.md
**Description:** Automatic version bumping rules and conventions
**Author:** Libor Ballaty <libor@arionetworks.com>
**Created:** 2026-01-05

---

## Overview

MyRAGDB uses **automatic version bumping** via git hooks. Versions are bumped based on commit message conventions following CalVer format: `YYYY.MM.DD.MAJOR.MINOR.PATCH`.

## Version Format

```
2026.01.05.1.0.3
│    │  │  │ │ │
│    │  │  │ │ └─ PATCH: Bug fixes only
│    │  │  │ └─── MINOR: New features (backward compatible)
│    │  │  └───── MAJOR: Breaking changes
│    │  └──────── Day: Build day (auto-updated)
│    └─────────── Month: Build month (auto-updated)
└──────────────── Year: Build year (auto-updated)
```

## Commit Message Conventions

The pre-commit hook automatically detects version bump type from your commit message:

### Major Version Bump (Breaking Changes)

**Triggers:**
- Commit message contains `BREAKING CHANGE:` anywhere
- Commit type ends with `!:`

**Examples:**
```bash
git commit -m "feat!: Rename BM25 API fields to keyword"
git commit -m "refactor: Redesign search API

BREAKING CHANGE: All /search/bm25 endpoints renamed to /search/keyword"
```

**Result:** `1.0.3` → `2.0.0`

### Minor Version Bump (New Features)

**Triggers:**
- Commit starts with `feat:` or `feature:`

**Examples:**
```bash
git commit -m "feat: Add semantic search caching"
git commit -m "feature: Implement query history tracking"
```

**Result:** `1.0.3` → `1.1.0`

### Patch Version Bump (Bug Fixes)

**Triggers:**
- Commit starts with `fix:`, `bugfix:`, or `patch:`
- **Default for any other commit type**

**Examples:**
```bash
git commit -m "fix: Keyword search 404 error"
git commit -m "bugfix: Meilisearch IndexStats attribute access"
git commit -m "Update documentation for installation"  # Also bumps patch
```

**Result:** `1.0.3` → `1.0.4`

### No Version Bump

**Triggers:**
- Commit starts with `chore:`, `docs:`, `style:`, `refactor:`, `test:`

**Examples:**
```bash
git commit -m "chore: Update .gitignore"
git commit -m "docs: Add API documentation"
git commit -m "test: Add unit tests for search engine"
git commit -m "style: Fix code formatting"
git commit -m "refactor: Extract search logic to helper"
```

**Result:** No version change

## Manual Version Bumping

If you need to manually bump the version:

```bash
# Bump patch version
python3 scripts/bump_version.py patch

# Bump minor version
python3 scripts/bump_version.py minor

# Bump major version
python3 scripts/bump_version.py major
```

## What Gets Updated Automatically

When version is bumped, the following files are automatically updated:

1. **`src/myragdb/version.py`**
   - `_BUILD_DATE` → Today's date
   - `_MAJOR_VERSION`, `_MINOR_VERSION`, `_PATCH_VERSION` → Bumped values
   - `__version__` → Computed version string

2. **`web-ui/index.html`**
   - CSS cache busting: `styles.css?v=2026.01.05.1.0.4`
   - JS cache busting: `app.js?v=2026.01.05.1.0.4`

These changes are automatically staged and included in your commit.

## Hook Installation

The hook is installed at `.git/hooks/prepare-commit-msg` and runs automatically before each commit.

**To disable the hook temporarily:**
```bash
git commit --no-verify -m "Your commit message"
```

## Examples

### Example 1: Bug Fix

```bash
$ git commit -m "fix: Keyword search returns 404"
Version bumped (patch): 2026.1.5.1.0.3 → 2026.1.5.1.0.4
[main abc1234] fix: Keyword search returns 404
 3 files changed, 10 insertions(+), 5 deletions(-)
```

### Example 2: New Feature

```bash
$ git commit -m "feat: Add query history tracking"
Version bumped (minor): 2026.1.5.1.0.4 → 2026.1.5.1.1.0
[main def5678] feat: Add query history tracking
 5 files changed, 120 insertions(+), 2 deletions(-)
```

### Example 3: Breaking Change

```bash
$ git commit -m "feat!: Rename all BM25 references to keyword

BREAKING CHANGE: API endpoints changed from /search/bm25 to /search/keyword"
Version bumped (major): 2026.1.5.1.1.0 → 2026.1.5.2.0.0
[main ghi9012] feat!: Rename all BM25 references to keyword
 12 files changed, 85 insertions(+), 78 deletions(-)
```

### Example 4: No Bump

```bash
$ git commit -m "docs: Update README with installation instructions"
No version bump needed for this commit type
[main jkl3456] docs: Update README with installation instructions
 1 file changed, 25 insertions(+)
```

## Troubleshooting

### Hook Not Running

Check that the hook is executable:
```bash
chmod +x .git/hooks/prepare-commit-msg
```

### Version Not Updating

1. Verify Python 3 is available: `python3 --version`
2. Check hook output: Look for error messages during commit
3. Test manually: `python3 scripts/bump_version.py patch`

### Wrong Version Bump

If the wrong version was bumped, you can amend the commit:
```bash
# Manually fix version in src/myragdb/version.py and web-ui/index.html
git add src/myragdb/version.py web-ui/index.html
git commit --amend --no-edit
```

## Best Practices

1. **Use conventional commit messages** - Helps automation work correctly
2. **Review version before pushing** - Check that the bump type is correct
3. **Don't skip hooks** - Version bumping is critical for cache busting
4. **Document breaking changes** - Always explain what broke and why in commit body

## Related Files

- `scripts/bump_version.py` - Version bumping script
- `.git/hooks/prepare-commit-msg` - Git hook that runs before commit
- `src/myragdb/version.py` - Version source of truth
- `web-ui/index.html` - Contains cache busting version references
