# Quick Start: Automated Version Bumping

## 🚀 The Easy Way (Recommended)

**Versions are automatically bumped after each successful release!**

### How It Works

1. You trigger a release with version `0.1.0`
2. Release workflow runs (PyPI, Docker, GitHub Release)
3. **Automatically bumps to `0.1.1`** and commits to `main`
4. Ready for next development cycle!

### Quick Release Process

```bash
# 1. Update CHANGELOG.md
vim CHANGELOG.md
# Add your changes

# 2. Commit and push to main
git add CHANGELOG.md
git commit -m "docs: update changelog for v0.1.0"
git push origin main

# 3. Trigger release on GitHub
# Go to: Actions → Release → Run workflow
# Enter version: 0.1.0
# Click: Run workflow

# 4. ✅ Done! Version auto-bumps to 0.1.1
```

That's it! No manual version management needed.

---

## 📖 Full Auto-Bump Details

See [VERSIONING.md](VERSIONING.md) for complete documentation on:
- How auto-bumping works
- Version numbering strategy
- Troubleshooting
- Customization options

---

## 🔧 Manual Version Bumping (Optional)

If you need to bump versions manually for local development:

## Installation

```bash
# Install in your virtual environment
source .venv/bin/activate
pip install bump-my-version

# Or using uv
uv add bump-my-version

# Or using uv pip
uv pip install bump-my-version

```

Already included in dev dependencies! Just run:
```bash
make install
```

## Basic Usage

### 1. Check Current Version
```bash
make version
# Output: 0.1.0
```

### 2. Preview Changes (Dry Run)
```bash
# See what would happen without making changes
make bump-dry-run PART=patch

# Or for minor/major
make bump-dry-run PART=minor
make bump-dry-run PART=major
```

### 3. Bump Version

**Important:** Commit all changes first!

```bash
# Ensure clean working directory
git status

# Bump patch version (0.1.0 → 0.1.1)
make bump-patch

# Bump minor version (0.1.0 → 0.2.0)
make bump-minor

# Bump major version (0.1.0 → 1.0.0)
make bump-major
```

### 4. Push Changes
```bash
# Push with tags
git push --follow-tags
```

## Complete Example

```bash
# 1. Update changelog
vim CHANGELOG.md
# Add your changes under [Unreleased]

# 2. Commit changelog
git add CHANGELOG.md
git commit -m "docs: update changelog for 0.2.0"

# 3. Preview bump
make bump-dry-run PART=minor
# Review the output

# 4. Bump version
make bump-minor
# ✅ Updates pyproject.toml
# ✅ Updates CHANGELOG.md with date
# ✅ Creates commit
# ✅ Creates tag v0.2.0

# 5. Push
git push --follow-tags
```

## What It Does

When you run `make bump-patch` (or minor/major):

1. **Updates `pyproject.toml`**:
   ```toml
   version = "0.1.0"  →  version = "0.1.1"
   current_version = "0.1.0"  →  current_version = "0.1.1"
   ```

2. **Updates `CHANGELOG.md`**:
   ```markdown
   ## [Unreleased]

   →

   ## [Unreleased]

   ## [0.1.1] - 2025-10-19
   ```

3. **Creates Git Commit**:
   ```
   chore: bump version from 0.1.0 to 0.1.1
   ```

4. **Creates Git Tag**:
   ```
   v0.1.1
   ```

## Common Commands

```bash
# Show current version
make version

# Show detailed info
make version-info

# Dry run (preview)
make bump-dry-run PART=patch

# Bump versions
make bump-patch    # 0.1.0 → 0.1.1 (bug fixes)
make bump-minor    # 0.1.0 → 0.2.0 (new features)
make bump-major    # 0.1.0 → 1.0.0 (breaking changes)

# Direct bump-my-version usage
bump-my-version bump patch --dry-run --verbose
bump-my-version bump minor --no-tag
bump-my-version bump major --allow-dirty  # Not recommended!
```

## Troubleshooting

### "Working directory is not clean"
```bash
# Commit your changes first
git add .
git commit -m "your message"

# Then bump
make bump-patch
```

### Need to test without committing?
```bash
# Dry run shows what would happen
make bump-dry-run PART=patch

# Or update files only (no commit)
bump-my-version bump patch --no-commit --allow-dirty
```

### Made a mistake?
```bash
# If not pushed yet, undo last commit
git reset --soft HEAD~1

# Delete local tag
git tag -d v0.1.1

# Make fixes and bump again
```

## Best Practices

1. ✅ **Always dry-run first**: `make bump-dry-run PART=patch`
2. ✅ **Commit all changes before bumping**
3. ✅ **Update CHANGELOG.md before bumping**
4. ✅ **Push with tags**: `git push --follow-tags`
5. ✅ **Follow semantic versioning**:
   - Patch: Bug fixes
   - Minor: New features
   - Major: Breaking changes

## Resources

- Full guide: [docs/VERSION_BUMPING.md](VERSION_BUMPING.md)
- bump-my-version: https://github.com/callowayproject/bump-my-version
- Semantic Versioning: https://semver.org/

---

**Quick Reference Card**

| Action | Command |
|--------|---------|
| Check version | `make version` |
| Dry run | `make bump-dry-run PART=patch` |
| Bug fix release | `make bump-patch` |
| Feature release | `make bump-minor` |
| Breaking change | `make bump-major` |
| Push with tags | `git push --follow-tags` |
