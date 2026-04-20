# Contributing to FormalCC Hermes Plugin

Thank you for your interest in contributing to the FormalCC Hermes Plugin!

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/your-org/formalcc-hermes-plugin.git
cd formalcc-hermes-plugin
```

2. Install in development mode:
```bash
pip install -e ".[dev]"
```

3. Set up your environment:
```bash
export FORMALCC_API_KEY=fsy_test_your_key_here
```

## Running Tests

Run the full test suite:
```bash
python3 -m pytest tests/ -v
```

Run with coverage:
```bash
python3 -m pytest tests/ --cov=plugins --cov=shared --cov-report=html
```

## Code Quality

Format code with Black:
```bash
black .
```

Lint with Ruff:
```bash
ruff check .
```

## Project Structure

```
formalcc-hermes-plugin/
├── shared/              # Shared utilities and models
├── plugins/
│   ├── memory/          # Memory provider plugin
│   └── context_engine/  # Context engine plugin
└── tests/               # Test suite
```

## Adding New Features

1. Create a feature branch
2. Implement your changes
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation
6. Submit a pull request

## Testing Guidelines

- Write tests for all new functionality
- Maintain or improve code coverage
- Use pytest fixtures for common test data
- Mock external API calls
- Test both success and failure paths

## Documentation

- Update README.md for user-facing changes
- Update DESIGN.md for architectural changes
- Add docstrings to all public functions
- Include examples in docstrings

## Commit Messages

Follow conventional commit format:
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `test:` Test additions or changes
- `refactor:` Code refactoring

## Release Process

1. Update CHANGELOG.md
2. Bump version in pyproject.toml
3. Create a git tag
4. Build and publish to PyPI

## Questions?

Open an issue on GitHub or reach out to the maintainers.
