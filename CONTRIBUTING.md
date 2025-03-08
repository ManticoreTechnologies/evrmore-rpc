# Contributing to Evrmore RPC

Thank you for considering contributing to the Evrmore RPC library! This document outlines the process for contributing to the project.

## Development Process

1. **Fork the Repository**: Start by forking the repository to your GitHub account.

2. **Create a Branch**: Create a branch for your feature or bug fix.
   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up the Development Environment**:
   ```bash
   # Install dependencies
   pip install -r requirements.txt
   
   # Install development dependencies
   pip install pytest pytest-asyncio black isort mypy
   
   # Install the package in development mode
   pip install -e .
   ```

4. **Make Your Changes**: Implement your changes, following the code style guidelines.

5. **Run Tests**: Ensure your changes pass all tests.
   ```bash
   pytest
   ```

6. **Code Formatting**: Format your code with Black and isort.
   ```bash
   black evrmore_rpc tests examples
   isort --profile black evrmore_rpc tests examples
   ```

7. **Type Checking**: Check your code with mypy.
   ```bash
   mypy evrmore_rpc
   ```

8. **Submit a Pull Request**: Push your changes to your fork and submit a pull request to the main repository.

## Code Style Guidelines

- Follow PEP 8 coding standards
- Use type hints for all function arguments and return values
- Write docstrings for all classes and methods using Google style
- Keep lines under 100 characters
- Use descriptive variable and function names

## Testing Guidelines

- Write tests for all new features and bug fixes
- Maintain or improve code coverage
- Use pytest fixtures for test setup
- Include both unit tests and integration tests when appropriate

## Documentation Guidelines

- Update documentation for all new features
- Include examples for new functionality
- Follow the Google style docstring format
- Update the CHANGELOG.md file for significant changes

## Commit Message Guidelines

Follow the conventional commits specification:
- `feat:` for new features
- `fix:` for bug fixes
- `docs:` for documentation changes
- `style:` for code style changes
- `refactor:` for code refactoring
- `test:` for adding or modifying tests
- `chore:` for maintenance tasks

## Pull Request Process

1. Update the README.md or documentation with details of changes to the interface, if applicable
2. Update the CHANGELOG.md with details of the changes
3. The PR may be merged once it receives approval from maintainers

## Code of Conduct

Please note that this project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## Questions?

If you have any questions about contributing, please open an issue or contact the maintainers. 