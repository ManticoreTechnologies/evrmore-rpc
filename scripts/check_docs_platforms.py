#!/usr/bin/env python3
"""
Documentation Platforms Checker for evrmore-rpc

This script checks the status of various documentation platforms and tools
for the evrmore-rpc project.

Usage:
    python3 scripts/check_docs_platforms.py
"""

import subprocess
import sys
import os
import re
import requests
from pathlib import Path
import json

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

def check_command(command, args=None):
    """Check if a command is available and get its version."""
    cmd = [command]
    if args:
        cmd.extend(args)
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        # Try to extract version from output
        version_match = re.search(r'version\s+(\S+)', result.stdout, re.IGNORECASE)
        if version_match:
            return True, version_match.group(1)
        else:
            return True, "Unknown version"
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False, None

def check_pypi_package(package_name):
    """Check if a package exists on PyPI and get its latest version."""
    try:
        response = requests.get(f"https://pypi.org/pypi/{package_name}/json")
        if response.status_code == 200:
            data = response.json()
            return True, data["info"]["version"]
        else:
            return False, None
    except requests.RequestException:
        return False, None

def check_readthedocs_project(project_name):
    """Check if a project exists on Read the Docs."""
    try:
        response = requests.get(f"https://readthedocs.org/api/v3/projects/{project_name}/")
        if response.status_code == 200:
            data = response.json()
            return True, data.get("default_version", "latest")
        else:
            return False, None
    except requests.RequestException:
        return False, None

def get_github_info():
    """Get GitHub repository information."""
    try:
        # Get remote URL
        result = subprocess.run(
            ["git", "config", "--get", "remote.origin.url"],
            check=True, capture_output=True, text=True
        )
        remote_url = result.stdout.strip()
        
        # Extract owner and repo from URL
        match = re.search(r'[:/]([^/]+)/([^/]+?)(\.git)?$', remote_url)
        if match:
            owner, repo = match.groups()[0:2]
            return owner, repo, remote_url
    except:
        pass
    
    return None, None, None

def check_file(file_path):
    """Check if a file exists and return its size."""
    path = ROOT_DIR / file_path
    if path.exists():
        return True, path.stat().st_size
    else:
        return False, None

def main():
    print("=== Evrmore RPC Documentation Platforms Checker ===\n")
    
    # Get project information
    project_name = "evrmore-rpc"
    current_version = "Unknown"
    
    # Try to get version from pyproject.toml or __init__.py
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
            match = re.search(r'version\s*=\s*"([^"]+)"', content)
            if match:
                current_version = match.group(1)
    
    if current_version == "Unknown":
        init_path = ROOT_DIR / "evrmore_rpc" / "__init__.py"
        if init_path.exists():
            with open(init_path, "r") as f:
                content = f.read()
                match = re.search(r'__version__\s*=\s*"([^"]+)"', content)
                if match:
                    current_version = match.group(1)
    
    # Get GitHub information
    github_owner, github_repo, github_url = get_github_info()
    
    # Print project information
    print(f"Project: {project_name}")
    print(f"Version: {current_version}")
    if github_owner and github_repo:
        print(f"GitHub: {github_owner}/{github_repo}")
    print()
    
    # Check documentation tools
    print("=== Documentation Tools ===")
    tools = [
        ("Python", "python3", ["--version"]),
        ("pip", "pip3", ["--version"]),
        ("MkDocs", "mkdocs", ["--version"]),
        ("Twine", "twine", ["--version"]),
        ("Build", "python3", ["-m", "build", "--version"]),
        ("Mike", "mike", ["--version"]),
    ]
    
    for name, cmd, args in tools:
        installed, version = check_command(cmd, args)
        status = "✅ " if installed else "❌ "
        version_info = f"v{version}" if version else "Not installed"
        print(f"{status}{name:<15} {version_info}")
    print()
    
    # Check configuration files
    print("=== Configuration Files ===")
    files = [
        ("README.md", "README.md"),
        ("pyproject.toml", "pyproject.toml"),
        ("setup.py", "setup.py"),
        ("mkdocs.yml", "mkdocs.yml"),
        ("Read the Docs config", ".readthedocs.yml"),
        ("GitHub Pages", ".github/workflows/docs.yml"),
    ]
    
    for name, path in files:
        exists, size = check_file(path)
        status = "✅ " if exists else "❌ "
        size_info = f"{size} bytes" if size else "Not found"
        print(f"{status}{name:<20} {size_info}")
    print()
    
    # Check online platforms
    print("=== Online Platforms ===")
    
    # PyPI
    pypi_exists, pypi_version = check_pypi_package(project_name)
    pypi_status = "✅ " if pypi_exists else "❌ "
    pypi_info = f"v{pypi_version}" if pypi_version else "Not found"
    print(f"{pypi_status}{'PyPI':<20} {pypi_info}")
    
    # Read the Docs
    rtd_exists, rtd_version = check_readthedocs_project(project_name)
    rtd_status = "✅ " if rtd_exists else "❌ "
    rtd_info = f"Default: {rtd_version}" if rtd_version else "Not found"
    print(f"{rtd_status}{'Read the Docs':<20} {rtd_info}")
    
    # GitHub Pages
    if github_owner and github_repo:
        github_pages_url = f"https://{github_owner}.github.io/{github_repo}/"
        try:
            response = requests.head(github_pages_url, timeout=5)
            gh_pages_exists = response.status_code < 400
        except:
            gh_pages_exists = False
        
        gh_pages_status = "✅ " if gh_pages_exists else "❌ "
        gh_pages_info = github_pages_url if gh_pages_exists else "Not published"
        print(f"{gh_pages_status}{'GitHub Pages':<20} {gh_pages_info}")
    else:
        print(f"❌ {'GitHub Pages':<20} Unable to determine URL")
    
    print()
    
    # Print documentation URLs
    print("=== Documentation URLs ===")
    if github_owner and github_repo:
        print(f"GitHub README: https://github.com/{github_owner}/{github_repo}#readme")
    
    if pypi_exists:
        print(f"PyPI: https://pypi.org/project/{project_name}/")
    
    if rtd_exists:
        print(f"Read the Docs: https://{project_name}.readthedocs.io/")
    
    if github_owner and github_repo and gh_pages_exists:
        print(f"GitHub Pages: https://{github_owner}.github.io/{github_repo}/")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 