# Publishing Evrmore-RPC Documentation

This guide explains how to publish the documentation for the evrmore-rpc library to various platforms.

## Documentation Sources

The evrmore-rpc documentation consists of several components:

1. **README.md**: Main documentation for GitHub and PyPI
2. **Package docstrings**: In-code documentation
3. **Example files**: Practical usage demonstrations
4. **Generated API documentation**: Created with MkDocs and mkdocstrings

## Publishing Platforms Overview

The documentation can be published to multiple platforms:

| Platform | Purpose | Automation | URL Format |
|----------|---------|------------|------------|
| GitHub README | Quick overview | Git push | github.com/username/evrmore-rpc |
| PyPI | Package page | `twine upload` | pypi.org/project/evrmore-rpc |
| Read the Docs | Full documentation | Webhooks | evrmore-rpc.readthedocs.io |
| GitHub Pages | Alternative hosting | GitHub Actions or `mkdocs gh-deploy` | username.github.io/evrmore-rpc |
| Netlify | Custom domain hosting | Git integration | your-domain.com |
| Sphinx | Alternative docs format | Build process | Various hosts |

## 1. GitHub Documentation

The main README.md and all documentation files in the repository are automatically published on GitHub.

To update:
1. Make your changes to the documentation files
2. Commit and push the changes to GitHub:
   ```bash
   git add .
   git commit -m "Update documentation"
   git push origin main
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

## 3. Read the Docs

Read the Docs is a popular documentation hosting platform that can automatically build and publish your documentation.

### Initial Setup

1. Create an account at [readthedocs.org](https://readthedocs.org/)
2. Import your GitHub repository
3. Configure the project settings:
   - Set the documentation type (MkDocs in our case)
   - Configure the required Python version
   - Set up build requirements

### Configuration Files

Ensure these files are in your repository:

1. `.readthedocs.yaml` in the root directory:
   ```yaml
   version: 2

   build:
     os: ubuntu-22.04
     tools:
       python: "3.10"

   python:
     install:
       - method: pip
         path: .
         extra_requirements:
           - docs

   mkdocs:
     configuration: mkdocs.yml
   ```

2. Make sure your `mkdocs.yml` file is properly configured:
   ```yaml
   site_name: Evrmore RPC
   site_description: Python client for the Evrmore blockchain
   site_url: https://evrmore-rpc.readthedocs.io/

   theme:
     name: material
     palette:
       primary: indigo
       accent: indigo

   plugins:
     - search
     - mkdocstrings:
         handlers:
           python:
             selection:
               docstring_style: google
             rendering:
               show_source: true
   ```

### Automatic Builds

Read the Docs can automatically build your documentation when you push to GitHub:

1. Go to your Read the Docs project dashboard
2. Navigate to Admin > Integrations
3. Make sure the GitHub webhook is set up
4. Push changes to your repo to trigger a build

### Manual Build Trigger

To manually trigger a build:
1. Go to your Read the Docs project dashboard
2. Click "Build" in the main navigation
3. Click "Build version"

## 4. GitHub Pages

GitHub Pages provides free hosting for your project documentation. There are two main ways to publish to GitHub Pages:

### Method 1: Using GitHub Actions (Recommended)

GitHub now supports building and deploying your documentation using GitHub Actions:

1. Go to your repository on GitHub
2. Navigate to Settings > Pages
3. Under "Build and deployment", select "GitHub Actions" as the source
4. Create a GitHub Actions workflow file in your repository at `.github/workflows/docs.yml`:

```yaml
name: Build and Deploy Documentation

on:
  push:
    branches:
      - main  # or your default branch
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: "pages"
  cancel-in-progress: false

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install .[docs]
      
      - name: Build documentation
        run: mkdocs build
      
      - name: Upload artifact
        uses: actions/upload-pages-artifact@v2
        with:
          path: ./site
  
  deploy:
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    needs: build
    runs-on: ubuntu-latest
    steps:
      - name: Deploy to GitHub Pages
        id: deployment
        uses: actions/deploy-pages@v2
```

5. Push this file to your repository and GitHub Actions will automatically build and deploy your documentation

### Method 2: Using MkDocs directly

You can also use MkDocs to build and push to GitHub Pages manually:

```bash
# Build and deploy to GitHub Pages
mkdocs gh-deploy --force
```

This method uses the `gh-deploy` command to build your site and push it to the `gh-pages` branch.

Your documentation will be available at `https://username.github.io/evrmore-rpc/`.

### Current Setup for evrmore-rpc

The evrmore-rpc documentation is currently published at [manticoretechnologies.github.io/evrmore-rpc](https://manticoretechnologies.github.io/evrmore-rpc/) using MkDocs with the Material theme.

## 5. Netlify

Netlify is a popular platform for hosting static sites with custom domains and continuous deployment.

### Setup

1. Create a Netlify account at [netlify.com](https://www.netlify.com/)
2. Connect your GitHub repository
3. Configure build settings:
   - Build command: `mkdocs build`
   - Publish directory: `site`

### Custom Domain

To set up a custom domain:
1. Go to your Netlify site settings
2. Click "Domain settings"
3. Add your custom domain
4. Update your DNS records

## 6. Sphinx (Alternative Documentation Generator)

If you prefer Sphinx documentation format over MkDocs:

1. Install Sphinx and extensions:
   ```bash
   pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints
   ```

2. Create a Sphinx documentation project:
   ```bash
   mkdir docs
   cd docs
   sphinx-quickstart
   ```

3. Configure `conf.py` for autodoc and other features

4. Build Sphinx documentation:
   ```bash
   sphinx-build -b html docs/source docs/build
   ```

## Comprehensive Publishing Script

The repository includes a `scripts/publish_docs.py` script that automates publishing to multiple platforms:

```bash
# Publish to all platforms
./scripts/publish_docs.py --version 3.2.2

# Dry run to see what would happen
./scripts/publish_docs.py --version 3.2.2 --dry-run

# Skip PyPI publication
./scripts/publish_docs.py --version 3.2.2 --no-pypi

# Force publish even without changes
./scripts/publish_docs.py --version 3.2.2 --force
```

## Checklist Before Publishing

- [ ] All docstrings are up to date
- [ ] README.md is comprehensive and accurate
- [ ] Examples are working and documented
- [ ] Changelog is updated
- [ ] Version numbers are consistent across all files
- [ ] Documentation builds without errors locally
- [ ] Read the Docs configuration is valid
- [ ] GitHub Pages rendering is checked
- [ ] PyPI README rendering is verified
- [ ] GitHub Actions workflow for docs is working (if using Method 1 for GitHub Pages)

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
6. Confirm documentation renders correctly on all publishing platforms

## Contact

For questions about documentation, contact the Evrmore RPC development team. 