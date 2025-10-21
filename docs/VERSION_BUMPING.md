# Version Bumping Guide

Complete guide for bumping versions in the docbt project using [bump-my-version](https://github.com/callowayproject/bump-my-version).

## 📋 Quick Reference

```bash
# Show current version
make version

# Bump patch (0.1.0 → 0.1.1)
make bump-patch

# Bump minor (0.1.0 → 0.2.0)
make bump-minor

# Bump major (0.1.0 → 1.0.0)
make bump-major

# Dry run (see what would change)
make bump-dry-run PART=patch

# Show detailed version info
make version-info
```

## 🤖 About bump-my-version

We use [`bump-my-version`](https://github.com/callowayproject/bump-my-version), a modern and configurable version bumping tool that:

- ✅ **Automatically updates** multiple files (`pyproject.toml`, `CHANGELOG.md`)
- ✅ **Creates git commits** with proper messages
- ✅ **Creates git tags** (e.g., `v0.1.0`)
- ✅ **Validates** version format
- ✅ **Supports dry-run** mode to preview changes
- ✅ **Prevents dirty working directory** commits
- ✅ **Configurable** via `pyproject.toml`

## 🔢 Semantic Versioning

We follow [Semantic Versioning 2.0.0](https://semver.org/):

```
MAJOR.MINOR.PATCH
  1  . 5  . 3
```

### When to Bump Each Number

#### **PATCH** (0.1.0 → 0.1.1)
Use for backwards-compatible bug fixes:
- Bug fixes
- Performance improvements
- Documentation updates
- Internal refactoring

**Example:**
```bash
# Fixed a bug in data parsing
make bump-patch
# Result: 0.1.0 → 0.1.1
```

#### **MINOR** (0.1.0 → 0.2.0)
Use for backwards-compatible new features:
- New features
- New APIs (without breaking existing ones)
- Deprecations (not removals)
- Substantial improvements

**Example:**
```bash
# Added BigQuery connector support
make bump-minor
# Result: 0.1.0 → 0.2.0
```

#### **MAJOR** (0.1.0 → 1.0.0)
Use for breaking changes:
- Breaking API changes
- Removed deprecated features
- Major architecture changes
- Incompatible changes

**Example:**
```bash
# Changed CLI interface completely
make bump-major
# Result: 0.1.0 → 1.0.0
```

## 🛠️ Methods

### Method 1: Using Make Commands (Recommended)

The easiest way - uses `bump-my-version` under the hood:

```bash
# Show current version
make version
# Output: 0.1.0

# Show what would change (dry run)
make bump-dry-run PART=patch
# Shows: Current version: 0.1.0, New version: 0.1.1

# Bump patch version
make bump-patch
# Automatically:
# - Updates pyproject.toml
# - Updates CHANGELOG.md
# - Creates git commit
# - Creates git tag v0.1.1

# Or bump minor
make bump-minor

# Or bump major
make bump-major
```

**What it does:**
1. ✅ Updates version in `pyproject.toml` (both `version` and `current_version`)
2. ✅ Updates `CHANGELOG.md` with new version section and date
3. ✅ Creates git commit with message: `chore: bump version from X.Y.Z to A.B.C`
4. ✅ Creates git tag: `vA.B.C`
5. ✅ Ready to push!

### Method 2: Using bump-my-version Directly

For more control or custom workflows:

```bash
# Patch bump
bump-my-version bump patch

# Minor bump
bump-my-version bump minor

# Major bump
bump-my-version bump major

# Dry run (see changes without applying)
bump-my-version bump patch --dry-run --verbose

# Skip commit (update files only)
bump-my-version bump patch --no-commit

# Skip tag
bump-my-version bump patch --no-tag

# Custom message
bump-my-version bump patch --message "Release version {new_version}"

# Allow dirty working directory (not recommended)
bump-my-version bump patch --allow-dirty
```

### Method 3: Manual Edit (Not Recommended)

If you really need to manually edit (bump-my-version handles this better):

```bash
# 1. Edit pyproject.toml
vim pyproject.toml
# Change BOTH:
#   version = "0.1.0"  (in [project])
#   current_version = "0.1.0"  (in [tool.bumpversion])

# 2. Edit CHANGELOG.md
vim CHANGELOG.md
# Add new version section with date

# 3. Commit and tag
git add pyproject.toml CHANGELOG.md
git commit -m "chore: bump version to 0.2.0"
git tag -a v0.2.0 -m "Version 0.2.0"
```

## 📝 Complete Workflow

### Standard Version Bump

```bash
# 1. Ensure you're on main and up to date
git checkout main
git pull origin main

# 2. Create version bump branch
git checkout -b chore/bump-version-0.2.0

# 3. Edit CHANGELOG.md FIRST (important!)
vim CHANGELOG.md
# Add your changes under ## [Unreleased] section:
## [Unreleased]
### Added
- New BigQuery connector
### Fixed
- Data parsing bug

# 4. Commit changelog
git add CHANGELOG.md
git commit -m "docs: update changelog for 0.2.0 release"

# 5. Bump version (this updates files, commits, and tags)
make bump-minor
# Creates commit: "chore: bump version from 0.1.0 to 0.2.0"
# Creates tag: v0.2.0

# 6. Review what happened
git log --oneline -2
git show HEAD
git tag -l

# 7. Push with tags
git push origin chore/bump-version-0.2.0 --follow-tags

# 8. Create PR on GitHub

# 9. After PR approval, merge to main

# 10. Release (manual workflow on GitHub)
# Go to: Actions → Release → Run workflow
# Enter: 0.2.0
```

### Alternative: Bump on Main Directly

If you have direct push access to main:

```bash
# 1. Checkout main
git checkout main
git pull

# 2. Update changelog
vim CHANGELOG.md
git add CHANGELOG.md
git commit -m "docs: update changelog for 0.2.0"

# 3. Bump version
make bump-minor

# 4. Push with tags
git push origin main --follow-tags

# 5. Trigger release workflow
# Go to GitHub Actions → Release → Run workflow
```

### Hotfix Version Bump

For urgent bug fixes:

```bash
# 1. Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug-0.1.1

# 2. Fix the bug
# ... make your changes ...
git add .
git commit -m "fix: critical bug in data parser"

# 3. Update changelog
vim CHANGELOG.md
# Add fix under [Unreleased]
git add CHANGELOG.md
git commit -m "docs: update changelog for hotfix"

# 4. Bump patch version
make bump-patch

# 5. Push with tags
git push origin hotfix/critical-bug-0.1.1 --follow-tags

# 6. Fast-track merge and release
```

## 🎯 Advanced Usage

### Dry Run (Preview Changes)

Always preview changes before bumping:

```bash
# See what would change
make bump-dry-run PART=patch

# Or with bump-my-version directly
bump-my-version bump patch --dry-run --verbose
```

Output shows:
- Current version
- New version
- Files that will be updated
- Exact changes in each file
- Commit message
- Tag name

Example output:
```
Performing bump
Checking if current_version matches the regex. ✓
Current version: 0.1.0
New version: 0.1.1
Changes:
  pyproject.toml:
    line 3: version = "0.1.0" -> version = "0.1.1"
    line 118: current_version = "0.1.0" -> current_version = "0.1.1"
  CHANGELOG.md:
    line 5: ## [Unreleased] -> ## [Unreleased]\n\n## [0.1.1] - 2025-10-19
Would commit with message: chore: bump version from 0.1.0 to 0.1.1
Would tag with: v0.1.1
```

### Skip Commit or Tag

```bash
# Update files only, no commit
bump-my-version bump patch --no-commit

# Commit but don't tag
bump-my-version bump patch --no-tag

# Do both (files only)
bump-my-version bump patch --no-commit --no-tag
```

Use cases:
- `--no-commit`: You want to review changes before committing
- `--no-tag`: You want to create the tag manually later
- Both: You're testing or want full manual control

### Custom Commit Message

```bash
# Custom commit message
bump-my-version bump patch --message "Release {new_version} with critical fixes"

# Multi-line message
bump-my-version bump patch --message "Release {new_version}

- Fixed critical bug in parser
- Updated dependencies
- Improved performance"
```

### Allow Dirty Working Directory

By default, bump-my-version prevents bumping with uncommitted changes:

```bash
# Force bump with uncommitted changes (not recommended)
bump-my-version bump patch --allow-dirty
```

**Warning:** Only use `--allow-dirty` if you know what you're doing!

## 🔍 Verifying Version

After bumping, verify the version:

```bash
# Check current version
make version

# Show detailed info
make version-info

# Check pyproject.toml directly
grep 'version = ' pyproject.toml

# Check git tags
git tag -l

# Check recent commits
git log --oneline -5

# After building and installing
pip install -e .
python -c "from importlib.metadata import version; print(version('docbt'))"
```

## 📦 What Gets Updated

### Automatic (via bump-my-version)
- ✅ `pyproject.toml` - `version` field (line 3)
- ✅ `pyproject.toml` - `current_version` field (in `[tool.bumpversion]`)
- ✅ `CHANGELOG.md` - New version section with current date
- ✅ Git commit with standardized message
- ✅ Git tag with `v` prefix

### Manual (you do this)
- ✅ `CHANGELOG.md` - Fill in actual changes under `[Unreleased]` before bumping
- ✅ Git push with tags (`git push --follow-tags`)
- ✅ Create PR (if using branch workflow)
- ✅ Trigger release workflow after merge

### Automatic (via release workflow)
- ✅ GitHub release with notes
- ✅ PyPI package with new version
- ✅ Docker images with version tags

## ⚙️ Configuration

Our configuration in `pyproject.toml`:

```toml
[tool.bumpversion]
current_version = "0.1.0"
parse = "(?P<major>\\d+)\\.(?P<minor>\\d+)\\.(?P<patch>\\d+)"
serialize = ["{major}.{minor}.{patch}"]
search = "{current_version}"
replace = "{new_version}"
regex = false
ignore_missing_version = false
ignore_missing_files = false
tag = true
sign_tags = false
tag_name = "v{new_version}"
tag_message = "Bump version: {current_version} → {new_version}"
allow_dirty = false
commit = true
message = "chore: bump version from {current_version} to {new_version}"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'

[[tool.bumpversion.files]]
filename = "CHANGELOG.md"
search = "## [Unreleased]"
replace = """## [Unreleased]

## [{new_version}] - {now:%Y-%m-%d}"""
```

### Customization Options

You can modify `pyproject.toml` to change behavior:

#### Change Tag Format
```toml
tag_name = "{new_version}"  # No 'v' prefix
tag_name = "release-{new_version}"  # Custom prefix
```

#### Change Commit Message
```toml
message = "Bump to {new_version}"
message = "Release version {new_version}"
```

#### Sign Tags
```toml
sign_tags = true  # GPG sign tags
```

#### Allow Dirty
```toml
allow_dirty = true  # Allow uncommitted changes (not recommended)
```

#### Add More Files
```toml
[[tool.bumpversion.files]]
filename = "src/docbt/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

## 🔧 Troubleshooting

### "Working directory is not clean"
**Problem:** Uncommitted changes prevent bumping

**Solution:**
```bash
# Commit or stash changes first
git status
git add .
git commit -m "..."

# Or stash temporarily
git stash
make bump-patch
git stash pop
```

### "Current version not found"
**Problem:** `current_version` in `[tool.bumpversion]` doesn't match actual version

**Solution:**
```bash
# Check both version fields match
grep 'version = ' pyproject.toml

# They should both show the same version:
# version = "0.1.0"  (in [project])
# current_version = "0.1.0"  (in [tool.bumpversion])

# If different, manually sync them
vim pyproject.toml
```

### "Tag already exists"
**Problem:** Git tag already created

**Solution:**
```bash
# Delete local tag
git tag -d v0.1.0

# Delete remote tag (careful!)
git push origin :refs/tags/v0.1.0

# Or bump to next version instead
make bump-patch
```

### Git Conflicts After Merge
**Problem:** CHANGELOG.md has conflicts after bump

**Solution:**
```bash
# Edit CHANGELOG.md to resolve conflicts
vim CHANGELOG.md
# Keep both version sections, arrange chronologically

# Mark as resolved
git add CHANGELOG.md
git commit
```

## 📚 Best Practices

1. **Always update CHANGELOG.md BEFORE bumping**
   ```bash
   # Good workflow:
   vim CHANGELOG.md  # Add changes
   git commit -m "docs: update changelog"
   make bump-minor
   ```

2. **Use dry-run to preview**
   ```bash
   make bump-dry-run PART=minor
   # Review output before actual bump
   make bump-minor
   ```

3. **Follow semver strictly** - Helps users understand impact
   - Patch: Bug fixes only
   - Minor: New features, backwards compatible
   - Major: Breaking changes

4. **Keep working directory clean**
   - Commit all changes before bumping
   - Don't use `--allow-dirty`

5. **Push tags immediately**
   ```bash
   git push origin main --follow-tags
   ```

6. **Test before releasing**
   - CI should pass
   - Manual testing complete
   - Documentation updated

7. **Version 0.x.x means "not stable yet"**
   - Breaking changes allowed in minor versions
   - Users expect instability

8. **Version 1.0.0 means stable API**
   - Be careful with breaking changes
   - Document migration paths

## 🚀 Quick Commands Summary

```bash
# Current version
make version

# Dry run
make bump-dry-run PART=patch
make bump-dry-run PART=minor
make bump-dry-run PART=major

# Actual bump
make bump-patch    # Bug fixes (0.1.0 → 0.1.1)
make bump-minor    # New features (0.1.0 → 0.2.0)
make bump-major    # Breaking changes (0.1.0 → 1.0.0)

# After bumping
git push --follow-tags
# Create PR or trigger release
```

## 🎓 Resources

- [bump-my-version Documentation](https://github.com/callowayproject/bump-my-version)
- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [PEP 440](https://peps.python.org/pep-0440/) - Python version identifiers
- [Release Workflow](CICD_QUICKREF.md#creating-a-release)

---

**Pro Tip:** Always run `make bump-dry-run PART=<type>` first to see what will change, then run the actual bump command! 🎯
