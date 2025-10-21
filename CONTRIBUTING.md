# Contributing to docbt

Thank you for your interest in contributing to docbt! This document provides guidelines and instructions for contributing.

## Development Setup

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- Git
- Docker (optional, for testing containers)

### Local Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/aleenprd/docbt.git
   cd docbt
   ```

2. **Create a virtual environment**
   ```bash
   # Using uv (recommended)
   uv venv
   source .venv/bin/acivate

   # Using pip
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   # using uv sync (recommended)
   uv sync

   # Using uv pip
   uv pip install -e ".[all-providers,dev]"

   # Or using pip
   pip install -e ".[all-providers,dev]"
   ```

4. **Install pre-commit hooks** (optional but recommended)
   ```bash
   pre-commit install
   ```


## Development Workflow

### 1. Create a Branch

Create a feature branch from `main`:

```bash
git checkout main
git pull origin main
git checkout -b feature/your-feature-name
```

Branch naming conventions:
- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `refactor/` - Code refactoring
- `test/` - Test improvements

### 2. Make Changes

Write your code following our coding standards (see below).

### 3. Run Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/docbt --cov-report=term

# Run specific test file
pytest tests/ai/test_llm.py

# Run specific test
pytest tests/ai/test_llm.py::test_specific_function
```

### 4. Lint Your Code

```bash
# Format code
ruff format .

# Check linting
ruff check .

# Auto-fix linting issues
ruff check --fix .
```

### 5. Commit Your Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add support for X"
```

Commit message format:
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks
- `ci:` - CI/CD changes

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a pull request on GitHub.

## Pull Request Guidelines

### PR Checklist

Before submitting your PR, ensure:

- [ ] Code follows the project's style guidelines
- [ ] All tests pass locally
- [ ] New tests added for new features
- [ ] Documentation updated (if applicable)
- [ ] No unnecessary dependencies added
- [ ] Commit messages are clear and descriptive
- [ ] PR description explains what and why

### PR Description Template

```markdown
## Description
Brief description of the changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
How has this been tested?

## Checklist
- [ ] Tests pass locally
- [ ] Code is formatted with ruff
- [ ] Documentation updated
- [ ] No new warnings

## Related Issues
Closes #123
```

### Review Process

1. Automated checks will run (CI pipeline)
2. A maintainer will review your code
3. Address any feedback
4. Once approved, your PR will be merged

## Coding Standards

### Python Style

We use **Ruff** for linting and formatting:

- Line length: 100 characters
- Target Python version: 3.10+
- Follow PEP 8 conventions

### Code Quality

- Write clear, self-documenting code
- Add docstrings to all public functions/classes
- Keep functions small and focused
- Avoid complex nested logic
- Use type hints where beneficial

### Docstring Format

Use Google-style docstrings:

```python
def function_name(param1: str, param2: int) -> bool:
    """Brief description of the function.

    More detailed description if needed.

    Args:
        param1: Description of param1
        param2: Description of param2

    Returns:
        Description of return value

    Raises:
        ValueError: When something goes wrong
    """
    pass
```

### Testing

- Write tests for all new features
- Aim for high test coverage
- Use descriptive test names
- Keep tests simple and focused
- Use fixtures for common setup

```python
def test_feature_does_something_correctly():
    """Test that feature X behaves correctly when Y."""
    # Arrange
    input_data = setup_test_data()

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result == expected_output
```

## Project Structure

```
docbt/
├── src/docbt/          # Main package
│   ├── ai/             # AI/LLM integration
│   ├── cli/            # Command-line interface
│   ├── config/         # Configuration management
│   ├── providers/      # Database connectors
│   └── server/         # Streamlit server
├── tests/              # Test suite
├── docs/               # Documentation
└── pyproject.toml      # Project configuration
```

## Running the Application

### CLI Mode

```bash
# Run the server
docbt run

# With custom host/port
docbt run --host 0.0.0.0 --port 8080
```

### Docker Mode

```bash
# Build
docker build -t docbt:latest .

# Run
docker run -p 8501:8501 docbt:latest
```

## Adding New Features

### Adding a New Provider

1. Create a new file in `src/docbt/providers/`
2. Implement the provider interface
3. Add tests in `tests/providers/`
4. Update documentation
5. Add to optional dependencies if needed

### Adding CLI Commands

1. Add command in `src/docbt/cli/docbt_cli.py`
2. Add tests in `tests/cli/`
3. Update CLI documentation

## Documentation

- Update relevant documentation files in `docs/`
- Add docstrings to new code
- Update README.md if adding major features
- Include usage examples

## Getting Help

- **Questions**: Open a GitHub Discussion
- **Bugs**: Open a GitHub Issue
- **Security Issues**: Email predaalin2694@gmail.com

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

## Recognition

Contributors will be recognized in:
- GitHub contributors page
- Release notes (for significant contributions)
- README acknowledgments

Thank you for contributing to docbt! 🎉
