# Contributing to Code Bundler

Thank you for considering contributing to Code Bundler! This document provides guidelines and instructions for contributing.

## Development Setup

1. Fork the repository
2. Clone your fork:

   ```bash
   git clone https://github.com/your-username/codebundler.git
   cd codebundler
   ```

3. Set up a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   # or
   pip install -e .
   pip install pytest black flake8 isort pytest-cov
   ```

## Development Workflow

1. Create a new branch for your feature or bugfix:

   ```bash
   git checkout -b feature-name
   ```

2. Make your changes

3. Make sure your code passes all tests:

   ```bash
   pytest
   ```

4. Ensure your code follows the formatting guidelines:

   ```bash
   black .
   isort .
   flake8
   ```

5. Commit your changes:

   ```bash
   git commit -m "Description of your changes"
   ```

6. Push to your fork:

   ```bash
   git push origin feature-name
   ```

7. Open a pull request

## Pull Request Guidelines

- Include tests for new features or bug fixes
- Update documentation as needed
- Follow the code style of the project
- Keep pull requests focused on a single topic
- Reference any related issues in your PR description

## Code Style

This project uses:

- [Black](https://black.readthedocs.io/en/stable/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [Flake8](https://flake8.pycqa.org/en/latest/) for linting

## Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage report
pytest --cov=codebundler

# Run specific test
pytest tests/test_transformers.py
```

## Adding New Features

When adding new features, please follow these steps:

1. Update the appropriate modules in `codebundler/core/`
2. Add tests for your new feature
3. Update documentation if necessary
4. Add a note to CHANGELOG.md under "Unreleased"

## Reporting Bugs

When reporting bugs, please include:

- Your operating system name and version
- Python version
- Package version
- Detailed steps to reproduce the bug
- What you expected to happen
- What actually happened
- Error messages and stack traces, if applicable

## License

By contributing, you agree that your contributions will be licensed under the project's MIT License.
