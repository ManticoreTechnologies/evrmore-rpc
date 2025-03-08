#!/usr/bin/env python3
"""
Documentation Publishing Script for evrmore-rpc

This script automates the process of publishing documentation for the evrmore-rpc library
to various platforms, including GitHub, PyPI, and Read the Docs.

Usage:
    python3 scripts/publish_docs.py [--version VERSION] [--no-pypi] [--no-rtd] [--dry-run]
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path
import re

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

def run_command(cmd, description, dry_run=False):
    """Run a shell command and print the output."""
    print(f"\n=== {description} ===")
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False

def get_current_version():
    """Get the current version from pyproject.toml or __init__.py."""
    # Try from pyproject.toml first
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
    
    # Try from __init__.py
    init_path = ROOT_DIR / "evrmore_rpc" / "__init__.py"
    if init_path.exists():
        with open(init_path, "r") as f:
            content = f.read()
            match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
            if match:
                return match.group(1)
    
    return None

def update_version(version):
    """Update version in pyproject.toml and __init__.py."""
    # Update pyproject.toml
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        content = re.sub(r'(version\s*=\s*)"([^"]+)"', f'\\1"{version}"', content)
        
        with open(pyproject_path, "w") as f:
            f.write(content)
    
    # Update __init__.py
    init_path = ROOT_DIR / "evrmore_rpc" / "__init__.py"
    if init_path.exists():
        with open(init_path, "r") as f:
            content = f.read()
        
        content = re.sub(r'(__version__\s*=\s*)"([^"]+)"', f'\\1"{version}"', content)
        
        with open(init_path, "w") as f:
            f.write(content)

def build_and_publish_pypi(dry_run=False):
    """Build and publish the package to PyPI."""
    # Clean old builds
    if not run_command(
        ["python3", "setup.py", "clean", "--all"],
        "Cleaning old builds",
        dry_run
    ):
        return False
    
    # Create distribution packages
    if not run_command(
        ["python3", "-m", "build"],
        "Building distribution packages",
        dry_run
    ):
        return False
    
    # Upload to PyPI
    if not run_command(
        ["python3", "-m", "twine", "upload", "dist/*"],
        "Uploading to PyPI",
        dry_run
    ):
        return False
    
    return True

def build_and_publish_docs(version, dry_run=False):
    """Build and publish documentation."""
    # Check if mkdocs is installed
    try:
        subprocess.run(["mkdocs", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Error: mkdocs is not installed. Run: pip install mkdocs mkdocs-material mkdocstrings")
        return False
    
    # Build documentation
    if not run_command(
        ["mkdocs", "build"],
        "Building documentation",
        dry_run
    ):
        return False
    
    # Deploy to GitHub Pages
    if not run_command(
        ["mkdocs", "gh-deploy", "--force"],
        "Deploying to GitHub Pages",
        dry_run
    ):
        return False
    
    # If mike is installed, create a versioned docs
    try:
        subprocess.run(["mike", "--version"], check=True, capture_output=True)
        
        # Deploy this version
        if not run_command(
            ["mike", "deploy", version],
            f"Deploying version {version}",
            dry_run
        ):
            return False
        
        # Set as default if it's not a pre-release
        if not re.search(r'(a|b|rc|dev)', version):
            if not run_command(
                ["mike", "set-default", version],
                f"Setting {version} as default",
                dry_run
            ):
                return False
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Note: mike is not installed. Skipping versioned documentation.")
    
    return True

def commit_and_push(version, dry_run=False):
    """Commit and push changes to GitHub."""
    # Add changes
    if not run_command(
        ["git", "add", "."],
        "Adding changes",
        dry_run
    ):
        return False
    
    # Commit changes
    if not run_command(
        ["git", "commit", "-m", f"Update documentation for version {version}"],
        "Committing changes",
        dry_run
    ):
        return False
    
    # Push changes
    if not run_command(
        ["git", "push", "origin", "master"],
        "Pushing changes",
        dry_run
    ):
        return False
    
    return True

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="Publish documentation for evrmore-rpc")
    parser.add_argument("--version", help="Version to publish")
    parser.add_argument("--no-pypi", action="store_true", help="Skip publishing to PyPI")
    parser.add_argument("--no-rtd", action="store_true", help="Skip publishing to Read the Docs")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually publish, just show commands")
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(ROOT_DIR)
    
    # Get current version if not specified
    version = args.version or get_current_version()
    if not version:
        print("Error: Could not determine version. Please specify with --version")
        return 1
    
    print(f"Publishing documentation for version {version}")
    
    # Update version in files
    if not args.dry_run:
        update_version(version)
    
    # Commit and push changes
    if not commit_and_push(version, args.dry_run):
        print("Error: Failed to commit and push changes")
        return 1
    
    # Build and publish to PyPI
    if not args.no_pypi:
        if not build_and_publish_pypi(args.dry_run):
            print("Error: Failed to publish to PyPI")
            return 1
    
    # Build and publish documentation
    if not args.no_rtd:
        if not build_and_publish_docs(version, args.dry_run):
            print("Error: Failed to publish documentation")
            return 1
    
    print(f"\nSuccessfully published documentation for version {version}")
    return 0

if __name__ == "__main__":
    sys.exit(main()) 