# Make Commands Guide

This guide explains how to use the `Makefile` included in the docbt project for common development tasks.

## Table of Contents

- [What is Make?](#what-is-make)
- [Prerequisites](#prerequisites)
- [Quick Reference](#quick-reference)
- [Command Categories](#command-categories)
  - [Help & Setup](#help--setup)
  - [Development Commands](#development-commands)
  - [Testing](#testing)
  - [Code Quality](#code-quality)
  - [Docker Commands](#docker-commands)
  - [Package Building](#package-building)
  - [Version Management](#version-management)
- [Common Workflows](#common-workflows)
- [Troubleshooting](#troubleshooting)

---

## What is Make?

[Make](https://www.gnu.org/software/make/) is a build automation tool that automatically executes commands defined in a `Makefile`. It's commonly used in software development to:

- Automate repetitive tasks
- Ensure consistent build processes
- Simplify complex command sequences
- Provide a standard interface across different projects

The docbt project includes a `Makefile` with predefined targets (commands) that make development easier.

---

## Prerequisites

Make is typically pre-installed on Linux and macOS. For Windows users:

### Linux/macOS
```bash
# Check if make is installed
make --version

# Install on Ubuntu/Debian (if needed)
sudo apt-get install build-essential

# Install on macOS (if needed)
xcode-select --install
```

### Windows
```bash
# Using Chocolatey
choco install make

# Using WSL (Windows Subsystem for Linux) - recommended
wsl --install
# Then follow Linux instructions inside WSL
```

---

## Quick Reference

To see all available commands with descriptions:

```bash
make help
```

This displays a formatted list of all targets with their descriptions:

```
Usage: make [target]

Available targets:
  build           Build base Docker image
  check           Run all checks (format + lint)
  clean           Remove containers and images
  env             Create .env file from .env.example (keeping section headers)
  format          Format code with ruff
  help            Show this help message
  install         Install dependencies with uv
  lint            Run ruff linter
  test            Run tests with pytest
  ...
```

---

## Command Categories

### Help & Setup

#### `make help`
Display all available commands with descriptions.

```bash
make help
```

#### `make env`
Create a `.env` file from `.env.example` with section headers preserved and comments removed.

```bash
make env
```

**Features:**
- Keeps section headers (`###`)
- Removes inline and full-line comments
- Prompts before overwriting existing `.env` file
- Creates clean, production-ready configuration

**Example:**
```bash
# First time setup
make env

# If .env already exists, you'll be prompted:
# ⚠️  .env file already exists!
# Do you want to overwrite it? [y/N]
```

#### `make install`
Install all project dependencies with development tools using [uv](https://docs.astral.sh/uv/).

```bash
make install
```

**What it does:**
- Installs base package in editable mode
- Includes all data providers (Snowflake, BigQuery)
- Includes development tools (testing, linting)

**Equivalent to:**
```bash
uv pip install -e ".[all-providers,dev]"
```

---

### Development Commands

#### `make pre-commit`
Install pre-commit hooks for automatic code quality checks.

```bash
make pre-commit
```

**What it does:**
- Sets up git hooks that run before each commit
- Automatically formats and checks code
- Prevents committing code with linting errors

#### `make pre-commit-run`
Manually run pre-commit hooks on all files.

```bash
make pre-commit-run
```

---

### Testing

#### `make test`
Run the full test suite using pytest.

```bash
make test
```

**Output:**
```
pytest
================== test session starts ==================
collected 302 items

tests/ai/test_llm.py ...................... [ 10%]
tests/cli/test_cli.py ..................... [ 20%]
...
================== 302 passed in 1.66s ==================
```

#### `make test-cov`
Run tests with coverage report.

```bash
make test-cov
```

**Output:**
- Terminal coverage summary
- HTML coverage report in `htmlcov/`

**To view HTML report:**
```bash
# After running make test-cov
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

#### `make test-docker`
Run tests inside a Docker container.

```bash
make test-docker
```

---

### Code Quality

#### `make lint`
Run [ruff](https://github.com/astral-sh/ruff) linter to check code quality.

```bash
make lint
```

**What it checks:**
- Code style violations
- Potential bugs
- Unused imports
- Type hints
- And more...

#### `make format`
Automatically format code using ruff.

```bash
make format
```

**What it does:**
- Fixes code style issues
- Sorts imports
- Removes trailing whitespace
- Ensures consistent formatting

#### `make format-check`
Check if code is properly formatted without making changes.

```bash
make format-check
```

**Use case:** CI/CD pipelines to verify formatting

#### `make check`
Run both formatting check and linting.

```bash
make check
```

**Equivalent to:**
```bash
make format-check
make lint
```

#### `make ci`
Run all CI checks locally (format, lint, and tests with coverage).

```bash
make ci
```

**Use this before pushing to ensure CI will pass:**
```bash
make ci
# ✓ All checks passed - safe to push!
```

---

### Docker Commands

Docker commands help you build, run, and manage containerized versions of docbt.

#### Building Images

**`make build`** - Build base Docker image
```bash
make build
```

**`make build-dev`** - Build development image
```bash
make build-dev
```

**`make build-prod`** - Build production image
```bash
make build-prod
```

#### Running Containers

**`make run`** - Run docbt with docker-compose
```bash
make run
```
Access at: http://localhost:8501

**`make run-bg`** - Run in background (detached mode)
```bash
make run-bg
```

**`make dev`** - Run development version
```bash
make dev
```

**`make prod`** - Run production version
```bash
make prod
```

**`make prod-bg`** - Run production in background
```bash
make prod-bg
```

#### Container Management

**`make stop`** - Stop all running containers
```bash
make stop
```

**`make restart`** - Restart containers
```bash
make restart
```

**`make logs`** - View container logs (follow mode)
```bash
make logs
```

**`make shell`** - Open interactive shell in container
```bash
make shell
```

#### Cleanup

**`make clean`** - Remove containers and images
```bash
make clean
```

**`make clean-all`** - Remove everything including volumes
```bash
make clean-all
```

⚠️ **Warning:** This deletes all data in Docker volumes!

#### Docker Utilities

**`make inspect`** - Inspect base Docker image
```bash
make inspect
```

**`make size`** - Show Docker image sizes
```bash
make size
```

**`make health`** - Check container health status
```bash
make health
```

---

### Package Building

Build and distribute docbt as a Python package.

#### `make build-package`
Build Python package (wheel and source distribution).

```bash
make build-package
```

**Output:** Creates files in `dist/` directory:
- `docbt-X.Y.Z-py3-none-any.whl` (wheel)
- `docbt-X.Y.Z.tar.gz` (source)

#### `make check-package`
Verify package integrity using twine.

```bash
make check-package
```

**Use before publishing to PyPI**

#### `make clean-package`
Remove build artifacts and distributions.

```bash
make clean-package
```

---

### Version Management

docbt uses [bump-my-version](https://github.com/callowayproject/bump-my-version) for semantic versioning.

#### `make version`
Show current version.

```bash
make version
# Output: 0.1.2
```

#### `make version-info`
Show detailed version information and next version numbers.

```bash
make version-info
```

#### Bump Version

**`make bump-patch`** - Increment patch version (0.1.0 → 0.1.1)
```bash
make bump-patch
```

**Use for:** Bug fixes, small changes

---

**`make bump-minor`** - Increment minor version (0.1.0 → 0.2.0)
```bash
make bump-minor
```

**Use for:** New features, backwards-compatible changes

---

**`make bump-major`** - Increment major version (0.1.0 → 1.0.0)
```bash
make bump-major
```

**Use for:** Breaking changes, major releases

---

#### `make bump-dry-run`
Test version bump without making changes.

```bash
make bump-dry-run PART=patch
make bump-dry-run PART=minor
make bump-dry-run PART=major
```

**Output:**
```
Would bump version from 0.1.2 to 0.1.3
Files to be modified:
  - src/docbt/__init__.py
  - pyproject.toml
```

---

## Common Workflows

### 🚀 First Time Setup

```bash
# 1. Clone the repository
git clone https://github.com/aleenprd/docbt.git
cd docbt

# 2. Create virtual environment
uv venv
source .venv/bin/activate

# 3. Install dependencies
make install

# 4. Create environment file
make env

# 5. Edit .env with your credentials
nano .env  # or your preferred editor

# 6. Install pre-commit hooks (optional but recommended)
make pre-commit

# 7. Run tests to verify everything works
make test
```

### 🔧 Daily Development Workflow

```bash
# 1. Start your work day
cd docbt
source .venv/bin/activate

# 2. Make your code changes
# ... edit files ...

# 3. Format and check code
make format
make lint

# 4. Run tests
make test

# 5. Commit your changes
git add .
git commit -m "feat: add new feature"
# Pre-commit hooks run automatically

# 6. Push changes
git push
```

### 🧪 Before Submitting a Pull Request

```bash
# Run the full CI suite locally
make ci

# If everything passes:
git push origin feature-branch
```

### 🐳 Docker Development

```bash
# Build development image
make build-dev

# Run in development mode
make dev

# View logs
make logs

# Stop when done
make stop
```

### 📦 Preparing a Release

```bash
# 1. Ensure all tests pass
make ci

# 2. Update version (choose appropriate bump)
make bump-minor  # or bump-patch, bump-major

# 3. Build package
make build-package

# 4. Verify package
make check-package

# 5. Tag and push
git push
git push --tags
```

### 🧹 Cleanup

```bash
# Clean Python cache and test artifacts
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type d -name "*.egg-info" -exec rm -rf {} +

# Clean package builds
make clean-package

# Clean Docker resources
make clean-all
```

---

## Troubleshooting

### Command Not Found: make

**Linux/macOS:**
```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# macOS
xcode-select --install

# Verify installation
make --version
```

**Windows:**
```bash
# Install via Chocolatey
choco install make

# Or use WSL (recommended)
wsl --install
```

### Permission Errors

```bash
# Don't use sudo with make commands in virtual environments
# Instead, ensure your virtual environment is activated:
source .venv/bin/activate

# Then run make commands normally:
make install
```

### Docker Commands Fail

```bash
# Ensure Docker is running
docker ps

# Check Docker daemon status
# macOS/Linux:
systemctl status docker

# If not running, start it:
systemctl start docker
```

### Make Target Not Working

```bash
# 1. Check the Makefile exists
ls -la Makefile

# 2. Verify target exists
make help | grep <target-name>

# 3. Run with verbose output
make -d <target-name>
```

### Environment Setup Issues

```bash
# Start fresh
rm -rf .venv
uv venv
source .venv/bin/activate
make install

# Recreate .env
rm .env
make env
```

### Tests Failing

```bash
# Run tests with verbose output
pytest -v

# Run specific test file
pytest tests/server/test_server.py -v

# Run with print statements visible
pytest -s
```

---

## Additional Resources

- **Official Make Documentation:** https://www.gnu.org/software/make/manual/
- **Make Tutorial:** https://makefiletutorial.com/
- **Project Makefile:** See `Makefile` in repository root
- **Contributing Guide:** See [CONTRIBUTING.md](../CONTRIBUTING.md)
- **CI/CD Documentation:** See [CICD.md](CICD.md)

---

## Need Help?

If you encounter issues not covered in this guide:

1. Check the [GitHub Issues](https://github.com/aleenprd/docbt/issues)
2. Open a new issue with:
   - Make command you ran
   - Error message received
   - Your operating system
   - Output of `make --version`

---

**Happy developing!** 🚀
