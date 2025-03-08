# Publishing Evrmore-RPC Documentation

This guide explains how to publish the documentation for the evrmore-rpc library to various platforms.

## Documentation Sources

The evrmore-rpc documentation consists of several components:

1. **README.md**: Main documentation for GitHub and PyPI
2. **Package docstrings**: In-code documentation
3. **Example files**: Practical usage demonstrations
4. **Generated API documentation**: Created with MkDocs and mkdocstrings

## 1. GitHub Documentation

The main README.md and all documentation files in the repository are automatically published on GitHub.

To update:
1. Make your changes to the documentation files
2. Commit and push the changes to GitHub:
   ```bash
   git add .
   git commit -m "Update documentation"
   git push origin master
   ```

## 2. PyPI Documentation

PyPI displays the README.md content on the package page.

To update:
1. Ensure the README.md is up-to-date
2. Update the version number in `pyproject.toml` or `setup.py`
3. Build and publish the package:
   ```bash
   # Clean old builds
   python3 setup.py clean --all
   # Create distribution packages
   python3 -m build
   # Upload to PyPI
   python3 -m twine upload dist/*
   ```

## 3. Read the Docs / MkDocs Documentation

The repository is configured to use MkDocs for generating comprehensive API documentation.

### Local Development

To build and view documentation locally:

```bash
# Install dependencies
pip3 install -e ".[docs]"

# Generate documentation
mkdocs build

# Serve documentation locally
mkdocs serve
```

Then visit http://localhost:8000 in your browser.

### Publishing to Read the Docs

The documentation is automatically built and published on Read the Docs when you push to GitHub.

Read the Docs configuration is in `.readthedocs.yml` and MkDocs configuration is in `mkdocs.yml`.

To manually trigger a rebuild:
1. Go to the Read the Docs project page
2. Navigate to "Builds"
3. Click "Build version"

### Custom Domain (Optional)

If using a custom domain:
1. Go to the Read the Docs project settings
2. Navigate to "Domains"
3. Add your custom domain
4. Update your DNS settings to point to Read the Docs

## 4. Python Package Index (PyPI)

The PyPI page for the package displays the README.md content. To ensure the best appearance:

1. Verify README.md renders correctly using a Markdown previewer
2. Check relative links are properly formatted
3. Ensure all images use absolute URLs

## 5. Documentation Versioning

For versioned documentation:

```bash
# Create a documentation version for the current release
mkdocs mike deploy <version>

# Set version as default
mkdocs mike set-default <version>

# Push changes to GitHub
git push origin gh-pages
```

## Checklist Before Publishing

- [ ] All docstrings are up to date
- [ ] README.md is comprehensive and accurate
- [ ] Examples are working and documented
- [ ] Changelog is updated
- [ ] Version numbers are consistent across all files
- [ ] Documentation builds without errors locally

## Documentation Standards

Follow these standards for consistency:

1. Use Python docstring format for all code
2. Include parameter types and return types in docstrings
3. Provide examples for complex functions
4. Keep the README.md up to date with the latest features
5. Ensure all ZMQ documentation emphasizes the need to force async mode

## Documentation Review Process

Before releasing new documentation:

1. Review all changes for accuracy
2. Test all example code
3. Have at least one other team member review the documentation
4. Check for any outdated references or code examples
5. Verify all links are working

## Contact

For questions about documentation, contact the Evrmore RPC development team. 