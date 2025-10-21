# Version Management - Technical Details

## Where Version is Defined

The project has version defined in **three places**, all automatically synchronized:

### 1. `pyproject.toml` (Build-time)
```toml
[project]
version = "0.1.0"
```
**Purpose:** Source of truth for package building and distribution

### 2. `src/docbt/__init__.py` (Runtime)
```python
__version__ = "0.1.0"
```
**Purpose:**
- Programmatic access: `import docbt; print(docbt.__version__)`
- Used by CLI as fallback

### 3. `CHANGELOG.md` (Documentation)
```markdown
## [0.1.0] - 2025-10-19
```
**Purpose:** Human-readable version history

## Version Access Methods

### From Package Metadata (Preferred)
```python
from importlib.metadata import version
v = version("docbt")  # "0.1.0"
```
**When:** Package is installed

### From Module (Fallback)
```python
from docbt import __version__
print(__version__)  # "0.1.0"
```
**When:** Running from source (development)

### From CLI
```bash
docbt --version
# Output: docbt, version 0.1.0
```

## Auto-Sync Configuration

All three locations are updated automatically by `bump-my-version`:

```toml
[tool.bumpversion]
current_version = "0.1.0"

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'

[[tool.bumpversion.files]]
filename = "src/docbt/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'

[[tool.bumpversion.files]]
filename = "CHANGELOG.md"
search = "## [Unreleased]"
replace = """## [Unreleased]

## [{new_version}] - {now:%Y-%m-%d}"""
```

## CLI Version Resolution

The CLI uses a **fallback strategy**:

```python
# 1. Try package metadata (when installed)
try:
    __version__ = version("docbt")
except PackageNotFoundError:
    # 2. Try __init__.py (when running from source)
    try:
        from docbt import __version__
    except ImportError:
        # 3. Fallback to "unknown"
        __version__ = "unknown"
```

**Benefits:**
- ✅ Works when installed: `pip install docbt`
- ✅ Works in development: `python -m docbt.cli.docbt_cli`
- ✅ Always shows some version

## Why Keep `__version__` in `__init__.py`?

### Pros
✅ **Runtime access** - Users can check version programmatically  
✅ **Development fallback** - Works when not installed  
✅ **Standard practice** - Common Python convention  
✅ **Debugging** - Easy to identify version in logs  
✅ **CLI support** - Fallback for `docbt --version`  

### Cons
❌ **Duplication** - Needs to stay in sync  
❌ **Extra update location** - But automated!  


## Version Bumping Workflow

When you bump versions, all three locations update:

```bash
# Manual bump
make bump-patch

# Files updated:
# ✅ pyproject.toml:        version = "0.1.0" → "0.1.1"
# ✅ src/docbt/__init__.py: __version__ = "0.1.0" → "0.1.1"
# ✅ CHANGELOG.md:          Adds [0.1.1] section

# Automatic bump (after release)
# Same updates happen automatically!
```

## Summary

| Location | Purpose | Updated By | Used By |
|----------|---------|------------|---------|
| `pyproject.toml` | Build source of truth | bump-my-version | pip, uv, build tools |
| `__init__.py` | Runtime access | bump-my-version | Python code, CLI |
| `CHANGELOG.md` | Documentation | bump-my-version | Users, developers |

**All stay in sync automatically!** 🎉

## See Also

- [VERSIONING.md](VERSIONING.md) - Automated version bumping guide
- [VERSION_BUMPING_QUICKSTART.md](VERSION_BUMPING_QUICKSTART.md) - Quick reference
- [Python Packaging User Guide](https://packaging.python.org/en/latest/guides/single-sourcing-package-version/)
