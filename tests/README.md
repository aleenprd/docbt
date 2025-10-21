# Tests for docbt

This directory contains the test suite for the docbt project.

## Structure

```
test/
├── __init__.py
├── conftest.py          # Pytest configuration and shared fixtures
├── README.md            # This file
└── server/              # Tests for server components
    ├── __init__.py
    └── test_llm.py      # Tests for LLM provider module
```

## Running Tests

### Install Development Dependencies

First, install pytest and other development dependencies:

```bash
pip install -e ".[dev]"
```

Or if using uv:

```bash
uv pip install -e ".[dev]"
```

### Run All Tests

```bash
pytest
```

### Run Tests with Coverage

```bash
pytest --cov=docbt --cov-report=html
```

### Run Specific Test File

```bash
pytest test/server/test_llm.py
```

### Run Specific Test Class

```bash
pytest test/server/test_llm.py::TestParseChainOfThought
```

### Run Specific Test Method

```bash
pytest test/server/test_llm.py::TestParseChainOfThought::test_lmstudio_with_think_tags
```

### Run Tests in Verbose Mode

```bash
pytest -v
```

### Run Tests and Show Print Statements

```bash
pytest -s
```

## Test Organization

Tests are organized by module, mirroring the structure of the `src/docbt/` directory:

- `test/server/` - Tests for components in `src/docbt/server/`
- More test directories can be added as needed (e.g., `test/cli/`, `test/config/`, etc.)

## Writing Tests

When writing tests:

1. Use descriptive test names that explain what is being tested
2. Follow the Arrange-Act-Assert pattern
3. Use pytest fixtures for common setup
4. Add docstrings to test classes and methods
5. Group related tests in test classes
6. Use markers to categorize tests (e.g., `@pytest.mark.unit`, `@pytest.mark.integration`)

## Test Coverage

Aim for high test coverage, especially for critical business logic. You can generate a coverage report using:

```bash
pytest --cov=docbt --cov-report=term-missing
```
