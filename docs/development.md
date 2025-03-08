# Development Guide

This guide provides information for developers who want to contribute to the Evrmore RPC library.

## Setting Up Development Environment

```bash
# Clone the repository
git clone https://github.com/ManticoreTechnology/evrmore-rpc.git
cd evrmore-rpc

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## Project Structure

The project follows a standard Python package structure:

```
evrmore-rpc/
├── docs/               # Documentation files
├── examples/           # Example scripts
├── scripts/            # Utility scripts
├── src/                # Source code
│   └── evrmore_rpc/    # Main package
│       ├── models/     # Data models
│       ├── zmq/        # ZMQ client
│       ├── __init__.py # Package entry point
│       ├── client.py   # Main client implementation
│       ├── client.pyi  # Type stub file for IDE support
│       ├── config.py   # Configuration handling
│       └── utils.py    # Utility functions
├── tests/              # Test files
├── .gitignore          # Git ignore file
├── LICENSE             # License file
├── MANIFEST.in         # Package manifest
├── mkdocs.yml          # Documentation configuration
├── pyproject.toml      # Project configuration
├── README.md           # Project readme
├── requirements.txt    # Dependencies
└── setup.py            # Setup script
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_client.py

# Run tests with coverage
pytest --cov=evrmore_rpc
```

## Building Documentation

```bash
# Build documentation
python scripts/build_docs.py

# Build and deploy documentation
python scripts/build_docs.py --deploy
```

## Running Examples

```bash
# List available examples
python scripts/run_examples.py --list

# Run a basic example
python scripts/run_examples.py super_simple

# Run an advanced example
python scripts/run_examples.py asset_monitor
```

## Code Style

The project uses the following tools for code style:

- [Black](https://black.readthedocs.io/) for code formatting
- [isort](https://pycqa.github.io/isort/) for import sorting
- [mypy](https://mypy.readthedocs.io/) for type checking

```bash
# Format code
black src tests examples

# Sort imports
isort src tests examples

# Check types
mypy src
```

## Publishing

```bash
# Check readiness for publication
python scripts/check_publication.py

# Build package
python -m build

# Upload to PyPI
python -m twine upload dist/*
```

## Contribution Guidelines

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests to ensure they pass
5. Update documentation if needed
6. Submit a pull request

Please follow these guidelines when contributing:

- Follow the existing code style
- Add tests for new features
- Update documentation for new features
- Keep commits focused and add descriptive commit messages
- Rebase your branch before submitting a pull request 