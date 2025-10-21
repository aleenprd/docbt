# CI/CD Documentation

This document describes the Continuous Integration and Continuous Deployment (CI/CD) pipelines for the docbt project.

## Overview

The project uses GitHub Actions for CI/CD with two main workflows:

1. **CI Workflow** (`ci.yml`) - Runs on every pull request and push
2. **Release Workflow** (`release.yml`) - Manual workflow for releasing to PyPI and Docker registries

## CI Workflow

The CI workflow runs automatically on pull requests and pushes to `main` and `develop` branches.

### Jobs

#### 1. Lint with Ruff
- **Purpose**: Check code quality and formatting
- **Steps**:
  - Check code formatting with `ruff format --check`
  - Run linter with `ruff check`
- **Python Version**: 3.10

#### 2. Test with pytest
- **Purpose**: Run unit and integration tests
- **Matrix**: Tests run on Python 3.10, 3.11, and 3.12
- **Steps**:
  - Install package with all optional dependencies
  - Run pytest with coverage
  - Upload coverage report to Codecov (Python 3.10 only)
- **Coverage**: Generates XML and terminal coverage reports

#### 3. Build Python Package
- **Purpose**: Ensure the package can be built successfully
- **Steps**:
  - Build source distribution and wheel using `uv build`
  - Validate package with `twine check`
  - Upload artifacts for inspection
- **Artifacts**: Available for 7 days

#### 4. Build Docker Images
- **Purpose**: Ensure Docker images can be built successfully
- **Targets Built**:
  - `base` - Minimal image with core dependencies
  - `production` - Full image with all provider dependencies
  - `development` - Development image with dev tools
- **Features**:
  - Uses BuildKit for efficient caching
  - GitHub Actions cache for faster builds
  - Multi-stage builds

### Status Check

All jobs must pass for the PR to be mergeable. The `all-checks-passed` job provides a single status check.

## Release Workflow

The release workflow is **manually triggered** from the GitHub Actions tab and should only be run from the `main` branch.

### Inputs

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `version` | Version to release (semver format, e.g., `0.1.0`) | Yes | - |
| `release_pypi` | Whether to release to PyPI | Yes | `true` |
| `release_docker` | Whether to release Docker images | Yes | `true` |
| `docker_registry` | Docker registry to use | No | `ghcr.io` |

### Jobs

#### 1. Validate Release
- Ensures release is from `main` branch
- Validates version format (semver)

#### 2. Release to PyPI
- Updates version in `pyproject.toml`
- Builds the package
- Publishes to PyPI using trusted publishing
- **Environment**: `pypi` (requires approval)
- **Requires**: PyPI trusted publisher configured

#### 3. Release Docker Images
- Builds and pushes Docker images to registry
- Creates multi-platform images (amd64, arm64)
- Tags images with:
  - Specific version (e.g., `0.1.0`)
  - Major.minor version (e.g., `0.1`)
  - Major version (e.g., `0`)
  - `latest`
- **Environment**: `docker-registry` (requires approval)
- **Registries Supported**:
  - GitHub Container Registry (`ghcr.io`) - uses `GITHUB_TOKEN`
  - Docker Hub (`docker.io`) - requires `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` secrets

#### 4. Create GitHub Release
- Creates a Git tag
- Creates a GitHub release with release notes
- Links to PyPI and Docker Hub

## Setup Requirements

### PyPI Publishing

For trusted publishing on PyPI:

1. Go to your PyPI project settings
2. Add a new "trusted publisher"
3. Configure:
   - **Owner**: `aleenprd`
   - **Repository**: `docbt`
   - **Workflow**: `release.yml`
   - **Environment**: `pypi`

### Docker Hub Publishing

If using Docker Hub, add these secrets to your repository:

- `DOCKERHUB_USERNAME`: Your Docker Hub username
- `DOCKERHUB_TOKEN`: Docker Hub access token

### GitHub Environments

Create these environments in your repository settings:

1. **pypi**
   - Add protection rules (recommended: require reviewers)
   - No secrets needed (uses trusted publishing)

2. **docker-registry**
   - Add protection rules (recommended: require reviewers)
   - Add `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` if using Docker Hub

## Usage

### Running CI

CI runs automatically. To test locally:

```bash
# Lint
ruff format --check .
ruff check .

# Test
pytest --cov=src/docbt --cov-report=term

# Build package
uv build

# Build Docker images
docker build --target base -t docbt:base .
docker build --target production -t docbt:production .
docker build --target development -t docbt:development .
```

### Creating a Release

1. Ensure all changes are merged to `main`
2. Go to Actions → Release → Run workflow
3. Enter the version number (e.g., `0.1.0`)
4. Choose whether to release to PyPI and/or Docker
5. Select the Docker registry if applicable
6. Click "Run workflow"
7. Approve the release in the environments (if configured)

### Post-Release

After a successful release:

1. Update `CHANGELOG.md` with release notes
2. Create a PR to bump the version in `pyproject.toml` for the next development cycle
3. Announce the release

## Troubleshooting

### CI Failures

- **Ruff failures**: Run `ruff format .` to auto-fix formatting
- **Test failures**: Run `pytest -v` locally to debug
- **Build failures**: Check `pyproject.toml` dependencies

### Release Failures

- **PyPI upload fails**: Check trusted publisher configuration
- **Docker push fails**: Verify registry credentials and permissions
- **Version conflict**: Ensure version doesn't already exist

## Best Practices

1. **Always run tests locally** before pushing
2. **Keep the main branch stable** - only merge tested code
3. **Use semantic versioning** for releases
4. **Document breaking changes** in release notes
5. **Test Docker images locally** before releasing
6. **Review dependency updates** carefully
