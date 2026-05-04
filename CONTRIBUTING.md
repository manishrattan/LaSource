# Contributing to LaSource

Thank you for your interest in contributing to LaSource! This document provides guidelines and instructions for contributing to the project.

## Code of Conduct

We are committed to providing a welcoming and inclusive environment for all contributors. Please be respectful and constructive in all interactions.

## Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ (for frontend development)
- Git
- Azure CLI (for Azure resource testing)

### Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/manishrattan/LaSource.git
   cd LaSource
   ```

2. **Set up Python environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development/testing
   ```

4. **Install Node dependencies (for frontend):**
   ```bash
   npm install
   ```

5. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

6. **Run tests:**
   ```bash
   pytest tests/ -v
   ```

## Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
# or for bug fixes:
git checkout -b fix/your-bug-name
```

### 2. Make Changes

- Follow PEP 8 style guidelines for Python code
- Add type hints to functions
- Include docstrings for all public methods
- Write tests for new functionality
- Update documentation as needed

### 3. Write Tests

All new features and bug fixes should include tests:

```python
# Example test structure
def test_new_feature():
    """Test description."""
    # Arrange
    expected = "expected_value"
    
    # Act
    result = function_under_test()
    
    # Assert
    assert result == expected
```

Run tests locally:
```bash
pytest tests/ -v --cov=lasource
```

### 4. Exception Handling

LaSource uses custom exceptions for consistent error handling. When adding new functionality:

```python
from lasource.domain.exceptions import LaSourceException, LaSourceValidationError

def my_function(value: str) -> str:
    """
    Function description.
    
    Args:
        value: Input parameter.
        
    Returns:
        str: Result value.
        
    Raises:
        LaSourceValidationError: If validation fails.
    """
    if not value:
        raise LaSourceValidationError("Value cannot be empty")
    
    try:
        # Your logic here
        pass
    except SomeSpecificError as e:
        raise LaSourceException(f"Operation failed: {str(e)}") from e
```

### 5. Commit Changes

Write clear, descriptive commit messages:

```bash
git add .
git commit -m "feat: add new security validation layer"
```

**Commit message format:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation update
- `test:` Test addition or modification
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance tasks

### 6. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Then create a Pull Request on GitHub with:
- Clear title and description
- Reference to related issues (if any)
- Summary of changes
- Screenshots (if UI changes)

## Code Style

### Python

- Use PEP 8 formatting
- Run `black` for automatic formatting
- Use `flake8` for linting
- Use `mypy` for type checking

```bash
black lasource/ src/
flake8 lasource/ src/
mypy lasource/ src/
```

### TypeScript/React

- Use ESLint configuration from `.eslintrc.json`
- Use Prettier for formatting
- Write functional components with hooks

### Documentation

- Use clear, concise language
- Include code examples where appropriate
- Keep docstrings up-to-date
- Update README.md for new features

## Testing Requirements

- Write unit tests for all domain logic
- Add integration tests for provider implementations
- Aim for >80% code coverage
- Test error cases and exception handling

```bash
# Run tests with coverage
pytest tests/ --cov=lasource --cov-report=html
```

## Documentation Requirements

For new features, update:

1. **Code docstrings** - Clear parameter and return descriptions
2. **README.md** - Add usage examples
3. **SPEC.md** - Update architecture/feature documentation
4. **Type hints** - Use Python type annotations

## Provider Implementation Guidelines

When implementing a new AI provider:

1. Create a new file in `lasource/providers/` (e.g., `gemini_provider.py`)
2. Inherit from `AbstractProvider`
3. Implement required methods:
   - `generate_response(prompt: str) -> str`
   - `health_check() -> bool`
4. Use custom exceptions from `lasource.domain.exceptions`
5. Add comprehensive error handling
6. Include docstrings and type hints
7. Add tests in `tests/test_providers/`

Example:

```python
from lasource.domain.provider import AbstractProvider
from lasource.domain.exceptions import LaSourceProviderError, LaSourceHealthCheckError

class MyProvider(AbstractProvider):
    """Implementation of MyProvider."""
    
    def __init__(self):
        """Initialize the provider."""
        # Implementation
        pass
    
    def generate_response(self, prompt: str) -> str:
        """Generate response."""
        try:
            # Implementation
            pass
        except Exception as e:
            raise LaSourceProviderError(f"Error: {str(e)}", provider_name="my-provider")
    
    def health_check(self) -> bool:
        """Check provider health."""
        try:
            # Implementation
            pass
        except Exception as e:
            raise LaSourceHealthCheckError(f"Error: {str(e)}", provider_name="my-provider")
```

## Reporting Bugs

### Before Reporting

- Check existing issues to avoid duplicates
- Check documentation and FAQs
- Try the latest development version

### How to Report

1. Use clear, descriptive title
2. Describe exact steps to reproduce
3. Include expected vs actual behavior
4. Add relevant code samples
5. Include environment details:
   - OS and version
   - Python version
   - LaSource version
   - Relevant environment variables (sanitized)

## Security Issues

**Do not** open public issues for security vulnerabilities. Instead:

1. Email security concerns to the maintainers
2. Include steps to reproduce and impact assessment
3. Allow time for patching before disclosure

## Pull Request Process

1. Update documentation and tests
2. Ensure CI/CD pipeline passes
3. Request review from maintainers
4. Address review feedback
5. Squash commits before merge (if requested)
6. Delete branch after merge

## Code Review

When reviewing PRs:

- Check code quality and style
- Verify tests are included and passing
- Review exception handling
- Ensure documentation is updated
- Provide constructive feedback

## Release Process

Releases follow semantic versioning (MAJOR.MINOR.PATCH):

1. Update version in `setup.py` and `package.json`
2. Update CHANGELOG
3. Create git tag: `git tag vX.Y.Z`
4. Push tag: `git push origin vX.Y.Z`
5. Publish release on GitHub

## Resources

- [LaSource Documentation](./README.md)
- [Architecture Specification](./SPEC.md)
- [Clean Architecture Principles](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [OpenTelemetry Standards](https://opentelemetry.io/)
- [Azure Best Practices](https://learn.microsoft.com/en-us/azure/architecture/guide/)

## Questions?

- Open a GitHub Discussion
- Check existing issues
- Email: [maintainers contact info]

Thank you for contributing to LaSource! 🚀
