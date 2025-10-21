# CI/CD Quick Reference

Quick commands and checklists for working with the CI/CD pipeline.

## Local Development Commands

### Quick Checks (Before Committing)
```bash
# Run all checks locally
make ci

# Or individually:
make format        # Format code
make lint         # Check linting
make test         # Run tests
make test-cov     # Run tests with coverage
```

### Using Pre-commit Hooks
```bash
# Install hooks (one time)
make pre-commit

# Run manually on all files
make pre-commit-run

# Hooks will run automatically on git commit
git commit -m "your message"
```

## CI Workflow

### What Runs on Pull Requests

Every PR automatically runs:

1. **Ruff Checks** (Python 3.10)
   - `ruff format --check .` - Code formatting
   - `ruff check .` - Linting

2. **Tests** (Python 3.10, 3.11, 3.12)
   - `pytest --cov` - Unit tests with coverage
   - Coverage uploaded to Codecov

3. **Package Build**
   - `uv build` - Build wheel and sdist
   - `twine check` - Validate package

4. **Docker Build**
   - Build base, production, dev images
   - Cached for faster builds

### PR Requirements

✅ **Must Pass:**
- All lint checks
- All tests on all Python versions
- Package build successful
- Docker images build successful

### Fixing CI Failures

**Ruff formatting errors:**
```bash
ruff format .
git add .
git commit --amend --no-edit
git push --force
```

**Ruff linting errors:**
```bash
ruff check --fix .
# Review changes
git add .
git commit -m "fix: address linting issues"
git push
```

**Test failures:**
```bash
pytest -v  # Run locally to debug
# Fix the failing test
git add .
git commit -m "fix: resolve test failures"
git push
```

**Docker build failures:**
```bash
docker build --target production -t docbt:test .
# Fix Dockerfile or dependencies
git add .
git commit -m "fix: resolve docker build issue"
git push
```

## Release Workflow

### Creating a Release

1. **Ensure main branch is ready**
   ```bash
   git checkout main
   git pull origin main
   ```

2. **Update CHANGELOG.md**
   - Document all changes since last release
   - Move items from [Unreleased] to new version section
   - Commit changes

3. **Trigger Release Workflow**
   - Go to: Actions → Release → Run workflow
   - Fill in:
     - Version: `0.1.0` (semver format)
     - Release to PyPI: ✅
     - Release Docker images: ✅
     - Docker registry: `ghcr.io` (or `docker.io`)
   - Click "Run workflow"

4. **Approve in Environments**
   - Review the release
   - Approve in `pypi` environment
   - Approve in `docker-registry` environment

5. **Verify Release**
   ```bash
   # Check PyPI
   pip install docbt==0.1.0

   # Check Docker
   docker pull ghcr.io/aleenprd/docbt:0.1.0

   # Check GitHub Release
   # Visit: https://github.com/aleenprd/docbt/releases
   ```

### Release Checklist

- [ ] All tests passing on main
- [ ] CHANGELOG.md updated
- [ ] Version number follows semver
- [ ] PyPI trusted publisher configured (first time only)
- [ ] Docker registry credentials set (first time only)
- [ ] GitHub environments configured (first time only)

### Post-Release

1. **Bump version for next development cycle**
   ```bash
   # Edit pyproject.toml
   # Change version to next dev version (e.g., 0.2.0)
   git checkout -b chore/bump-version
   # ... make changes ...
   git commit -m "chore: bump version to 0.2.0-dev"
   git push origin chore/bump-version
   # Create PR
   ```

2. **Announce release**
   - GitHub Discussions
   - README badges
   - Social media (if applicable)

## First-Time Setup

### 1. PyPI Trusted Publishing

Visit: https://pypi.org/manage/account/publishing/

Add trusted publisher:
- Owner: `aleenprd`
- Repository: `docbt`
- Workflow: `release.yml`
- Environment: `pypi`

### 2. Docker Registry

**For GitHub Container Registry (ghcr.io):**
- No setup needed! Uses `GITHUB_TOKEN` automatically

**For Docker Hub:**
1. Create access token: https://hub.docker.com/settings/security
2. Add secrets to GitHub:
   - Settings → Secrets → Actions
   - Add `DOCKERHUB_USERNAME`
   - Add `DOCKERHUB_TOKEN`

### 3. GitHub Environments

Settings → Environments → New environment

**Create `pypi` environment:**
- Required reviewers: (your username)
- Wait timer: 0 minutes (optional)

**Create `docker-registry` environment:**
- Required reviewers: (your username)
- Add secrets (if using Docker Hub):
  - `DOCKERHUB_USERNAME`
  - `DOCKERHUB_TOKEN`

### 4. Branch Protection

Settings → Branches → Add rule

**For `main` branch:**
- ✅ Require pull request reviews (1 reviewer)
- ✅ Require status checks to pass
  - Select: `All Checks Passed`
- ✅ Require branches to be up to date
- ✅ Do not allow bypassing

## Troubleshooting

### "Trusted publisher not configured"
1. Go to PyPI project settings
2. Add trusted publisher as described above
3. Retry the release

### "Docker push permission denied"
1. Check registry credentials are correct
2. Verify `GITHUB_TOKEN` has packages:write permission
3. For Docker Hub, verify token is valid

### "Environment protection rules not satisfied"
1. Approve the deployment in the environment
2. Or adjust environment protection rules

### "Version already exists"
1. Check PyPI/Docker for existing version
2. Use a different version number
3. Or delete the existing release (not recommended)

## Common Workflows

### Hotfix Release

```bash
# Create hotfix branch from main
git checkout main
git pull
git checkout -b hotfix/critical-bug

# Make fix
# ... fix code ...
git add .
git commit -m "fix: critical bug in X"

# Push and create PR
git push origin hotfix/critical-bug
# Create PR to main

# After merge, release immediately
# Go to Actions → Release → Run workflow
# Use patch version bump (e.g., 0.1.0 → 0.1.1)
```

### Feature Release

```bash
# Feature is merged to main
# Update CHANGELOG.md
# Use minor version bump (e.g., 0.1.0 → 0.2.0)
# Follow release workflow
```

### Major Release

```bash
# Breaking changes are merged
# Update CHANGELOG.md with migration guide
# Use major version bump (e.g., 0.9.0 → 1.0.0)
# Follow release workflow
# Post-release: Update documentation
```

## Resources

- [CI/CD Documentation](CICD.md) - Full documentation
- [Contributing Guide](../CONTRIBUTING.md) - Development guidelines
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [PyPI Publishing](https://packaging.python.org/en/latest/guides/publishing-package-distribution-releases-using-github-actions-ci-cd-workflows/)
