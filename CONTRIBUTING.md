# Contributing to Toolable

Thank you for your interest in contributing to Toolable! This document provides guidelines for contributing to the project.

## Getting Started

### Prerequisites

- Python 3.10 or higher
- Git
- pip

### Development Setup

1. Fork and clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/toolable.git
cd toolable
```

2. Create a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install in development mode with dev dependencies:
```bash
pip install -e ".[dev]"
```

4. Verify tests pass:
```bash
pytest tests/
```

## Development Workflow

### Branch Strategy

- `main` - Stable releases only
- `dev` - Active development branch
- `feature/*` - New features
- `fix/*` - Bug fixes
- `infra/*` - Infrastructure and tooling

### Making Changes

1. Create a feature branch from `dev`:
```bash
git checkout dev
git pull origin dev
git checkout -b feature/your-feature-name
```

2. Make your changes following our coding standards (see below)

3. Add tests for your changes - we maintain 90%+ coverage

4. Run the test suite:
```bash
pytest tests/ --cov=toolable --cov-report=term-missing
```

5. Run linting:
```bash
ruff check src/toolable tests/
mypy src/toolable
```

6. Commit with clear messages:
```bash
git commit -m "feat: add new feature description"
```

Follow [Conventional Commits](https://www.conventionalcommits.org/):
- `feat:` - New features
- `fix:` - Bug fixes
- `test:` - Test additions/changes
- `docs:` - Documentation changes
- `refactor:` - Code refactoring
- `perf:` - Performance improvements

7. Push and create a pull request:
```bash
git push origin feature/your-feature-name
gh pr create --base dev
```

## Coding Standards

### Style Guide

- Follow PEP 8
- Use type hints for all functions
- Maximum line length: 100 characters
- Use Ruff for linting
- Use MyPy for type checking

### Testing Requirements

- All new code must have tests
- Maintain 90%+ test coverage
- Tests must pass on Python 3.10, 3.11, 3.12, and 3.13
- Tests must pass on Ubuntu, macOS, and Windows

### Documentation Requirements

- Add docstrings to all public functions/classes
- Update README.md if adding user-facing features
- Update CLAUDE.md for architectural changes
- Include examples for new decorators or features

## Pull Request Process

### Before Submitting

- [ ] Tests pass locally (`pytest tests/`)
- [ ] Coverage is 90%+ for new code
- [ ] Linting passes (`ruff check src/ tests/`)
- [ ] Type checking passes (`mypy src/toolable`)
- [ ] Documentation updated
- [ ] CHANGELOG.md updated (if applicable)

### PR Guidelines

1. **Target the `dev` branch** unless it's a hotfix
2. **Fill out the PR template** completely
3. **Keep PRs focused** - one feature/fix per PR
4. **Write clear descriptions** - explain what and why
5. **Respond to reviews** promptly
6. **Keep commits clean** - squash if needed

### Review Process

- All PRs require at least one approval
- CI must pass (tests on all platforms/versions)
- Coverage must not decrease
- Maintainers may request changes

## Testing Guidelines

### Writing Good Tests

```python
def test_specific_behavior():
    """Test that X does Y when Z."""
    # Arrange
    input_data = {"key": "value"}

    # Act
    result = function_under_test(input_data)

    # Assert
    assert result["status"] == "success"
```

### Test Organization

- Unit tests: Test individual functions in isolation
- Integration tests: Test full CLI execution paths
- Fixtures: Reusable test data in `tests/fixtures/`

### Running Specific Tests

```bash
# Single test
pytest tests/test_cli.py::test_specific_function -v

# Single file
pytest tests/test_cli.py -v

# With coverage
pytest tests/test_cli.py --cov=toolable.cli --cov-report=term-missing
```

## Reporting Issues

### Bug Reports

Use the bug report template and include:
- Python version
- Operating system
- Minimal reproduction steps
- Expected vs actual behavior
- Error messages (if any)

### Feature Requests

Use the feature request template and include:
- Use case description
- Proposed API (if applicable)
- Alternatives considered
- Willingness to implement

## Code of Conduct

### Our Standards

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Assume good intentions

### Unacceptable Behavior

- Harassment or discrimination
- Trolling or inflammatory comments
- Publishing others' private information
- Other conduct inappropriate in a professional setting

### Enforcement

Violations may result in temporary or permanent ban from the project. Report issues to the maintainers.

## Questions?

- Open a discussion on GitHub
- Check existing issues and PRs
- Read the documentation in `docs/`

## License

By contributing to Toolable, you agree that your contributions will be licensed under the MIT License.
