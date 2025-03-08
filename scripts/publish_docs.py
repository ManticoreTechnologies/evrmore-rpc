#!/usr/bin/env python3
"""
Documentation Publishing Script for evrmore-rpc

This script automates the process of publishing documentation for the evrmore-rpc library
to various platforms, including GitHub, PyPI, Read the Docs, GitHub Pages, and more.

Usage:
    python3 scripts/publish_docs.py [--version VERSION] [options]

Options:
    --version VERSION     Version to publish (required if not in a release branch)
    --dry-run            Don't actually publish, just show commands
    --no-pypi            Skip publishing to PyPI
    --no-rtd             Skip Read the Docs related tasks
    --no-github-pages    Skip GitHub Pages deployment
    --force              Force publishing even if there are no changes
    --trigger-rtd-build  Trigger a build on Read the Docs (requires RTD token)
    --rtd-project NAME   Read the Docs project name (default: evrmore-rpc)
    --rtd-token TOKEN    Read the Docs API token
    --github-actions     Use GitHub Actions for GitHub Pages (trigger workflow)
    --check-platforms    Check status of documentation platforms and exit

Supported Documentation Platforms:
    - GitHub README      (automatically published on git push)
    - PyPI Documentation (published with twine)
    - Read the Docs      (webhook triggered on git push)
    - GitHub Pages       (published with mkdocs gh-deploy or GitHub Actions)
"""

import argparse
import os
import subprocess
import sys
import re
import json
import http.client
import urllib.parse
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional

# Get the project root directory
ROOT_DIR = Path(__file__).resolve().parent.parent

def run_command(cmd, description, dry_run=False):
    """Run a shell command and print the output."""
    print(f"\n=== {description} ===")
    if dry_run:
        print(f"[DRY RUN] Would execute: {' '.join(cmd)}")
        return True, ""
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False, e.stderr

def get_current_branch():
    """Get the current Git branch name."""
    try:
        result = subprocess.run(
            ["git", "branch", "--show-current"], 
            check=True, 
            capture_output=True, 
            text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        # Default to main if we can't determine
        return "main"

def check_uncommitted_changes():
    """Check if there are uncommitted changes in the repository."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            check=True,
            capture_output=True,
            text=True
        )
        return bool(result.stdout.strip())
    except subprocess.CalledProcessError:
        # Assume there are changes if we can't determine
        return True

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
    files_updated = []
    
    # Update pyproject.toml
    pyproject_path = ROOT_DIR / "pyproject.toml"
    if pyproject_path.exists():
        with open(pyproject_path, "r") as f:
            content = f.read()
        
        new_content = re.sub(r'(version\s*=\s*)"([^"]+)"', f'\\1"{version}"', content)
        
        if new_content != content:
            with open(pyproject_path, "w") as f:
                f.write(new_content)
            files_updated.append(str(pyproject_path))
    
    # Update __init__.py
    init_path = ROOT_DIR / "evrmore_rpc" / "__init__.py"
    if init_path.exists():
        with open(init_path, "r") as f:
            content = f.read()
        
        new_content = re.sub(r'(__version__\s*=\s*)"([^"]+)"', f'\\1"{version}"', content)
        
        if new_content != content:
            with open(init_path, "w") as f:
                f.write(new_content)
            files_updated.append(str(init_path))
    
    return files_updated

def build_and_publish_pypi(dry_run=False):
    """Build and publish the package to PyPI."""
    # Clean old builds
    success, _ = run_command(
        ["python3", "setup.py", "clean", "--all"],
        "Cleaning old builds",
        dry_run
    )
    if not success:
        return False
    
    # Create distribution packages
    success, _ = run_command(
        ["python3", "-m", "build"],
        "Building distribution packages",
        dry_run
    )
    if not success:
        return False
    
    # Upload to PyPI
    success, _ = run_command(
        ["python3", "-m", "twine", "upload", "dist/*"],
        "Uploading to PyPI",
        dry_run
    )
    if not success:
        return False
    
    return True

def build_and_publish_github_pages(use_github_actions=False, dry_run=False):
    """Build and publish documentation to GitHub Pages."""
    if use_github_actions:
        print("\n=== Using GitHub Actions for GitHub Pages ===")
        print("No local action needed. GitHub Actions will build and deploy automatically.")
        print("Changes pushed to the repo will trigger the workflow.")
        print("You can also manually trigger the workflow from the Actions tab on GitHub.")
        return True
    
    # Traditional approach using mkdocs gh-deploy
    success, _ = run_command(
        ["mkdocs", "build"],
        "Building documentation",
        dry_run
    )
    if not success:
        return False
    
    success, _ = run_command(
        ["mkdocs", "gh-deploy", "--force"],
        "Deploying to GitHub Pages",
        dry_run
    )
    if not success:
        return False
    
    return True

def trigger_github_actions_workflow(dry_run=False):
    """Trigger a GitHub Actions workflow_dispatch event."""
    # Get GitHub repository information
    github_owner, github_repo, _ = get_github_info()
    
    if not github_owner or not github_repo:
        print("Error: Could not determine GitHub repository information")
        return False
    
    # GitHub CLI must be installed
    if dry_run:
        print(f"\n=== Triggering GitHub Actions workflow ===")
        print(f"[DRY RUN] Would trigger workflow_dispatch for {github_owner}/{github_repo}")
        return True
    
    try:
        # Check if GitHub CLI is installed
        subprocess.run(["gh", "--version"], check=True, capture_output=True)
        
        # Trigger workflow_dispatch
        result = subprocess.run(
            ["gh", "workflow", "run", "docs.yml", "--repo", f"{github_owner}/{github_repo}"],
            check=True,
            capture_output=True,
            text=True
        )
        
        print(f"\n=== Triggering GitHub Actions workflow ===")
        print(result.stdout or "Workflow triggered successfully")
        return True
    except FileNotFoundError:
        print("Error: GitHub CLI (gh) is not installed. Install it to trigger workflows.")
        print("Visit: https://cli.github.com/")
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error triggering GitHub Actions workflow: {e}")
        print(f"Output: {e.stdout}")
        print(f"Error output: {e.stderr}")
        return False

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
        if "github.com" in remote_url:
            if remote_url.startswith("git@"):
                # SSH format: git@github.com:owner/repo.git
                match = re.search(r'github\.com:([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
            else:
                # HTTPS format: https://github.com/owner/repo.git
                match = re.search(r'github\.com/([^/]+)/([^/]+?)(?:\.git)?$', remote_url)
            
            if match:
                owner, repo = match.groups()
                return owner, repo, remote_url
    except:
        pass
    
    return None, None, None

def build_versioned_docs(version, dry_run=False):
    """Build and publish versioned documentation if mike is installed."""
    try:
        subprocess.run(["mike", "--version"], check=True, capture_output=True)
        
        # Deploy this version
        success, _ = run_command(
            ["mike", "deploy", version],
            f"Deploying version {version} with mike",
            dry_run
        )
        if not success:
            return False
        
        # Set as default if it's not a pre-release
        if not re.search(r'(a|b|rc|dev)', version):
            success, _ = run_command(
                ["mike", "set-default", version],
                f"Setting {version} as default",
                dry_run
            )
            if not success:
                return False
        
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("Note: mike is not installed. Skipping versioned documentation.")
        return True  # Not a failure, just skipped

def trigger_readthedocs_build(project_name, token, version="latest", dry_run=False):
    """Trigger a build on Read the Docs."""
    if dry_run:
        print(f"\n=== Triggering Read the Docs build for {project_name} ===")
        print(f"[DRY RUN] Would trigger build for project {project_name}, version {version}")
        return True
    
    print(f"\n=== Triggering Read the Docs build for {project_name} ===")
    
    try:
        # Build the payload
        payload = {
            "token": token,
            "version": version,
        }
        
        # Convert payload to JSON
        json_payload = json.dumps(payload).encode('utf-8')
        
        # Set up the connection
        conn = http.client.HTTPSConnection("readthedocs.org")
        headers = {
            "Content-Type": "application/json",
        }
        
        # Make the request
        conn.request(
            "POST", 
            f"/api/v3/projects/{project_name}/versions/{version}/builds/", 
            body=json_payload,
            headers=headers
        )
        
        # Get the response
        response = conn.getresponse()
        data = response.read().decode('utf-8')
        
        # Check the response
        if response.status == 202:
            print(f"Read the Docs build triggered successfully for {project_name} ({version})")
            return True
        else:
            print(f"Error triggering Read the Docs build: {response.status} {response.reason}")
            print(f"Response: {data}")
            return False
    except Exception as e:
        print(f"Error triggering Read the Docs build: {e}")
        return False

def commit_and_push(files, version, dry_run=False):
    """Commit and push changes to GitHub."""
    if not files:
        print("No files to commit")
        return True
    
    # Get the current branch
    branch = get_current_branch()
    print(f"Current branch: {branch}")
    
    # Add changes
    for file in files:
        success, _ = run_command(
            ["git", "add", file],
            f"Adding file: {file}",
            dry_run
        )
        if not success:
            return False
    
    # Commit changes
    success, _ = run_command(
        ["git", "commit", "-m", f"Update documentation for version {version}"],
        "Committing changes",
        dry_run
    )
    if not success:
        return False
    
    # Push changes
    success, _ = run_command(
        ["git", "push", "origin", branch],
        f"Pushing changes to {branch}",
        dry_run
    )
    if not success:
        return False
    
    return True

def check_github_actions_file():
    """Check if GitHub Actions workflow file exists."""
    workflow_path = ROOT_DIR / ".github" / "workflows" / "docs.yml"
    return workflow_path.exists()

def print_platform_status():
    """Print the status of all documentation platforms."""
    print("\n=== Documentation Platforms Status ===")
    
    # Check if MkDocs is installed
    try:
        subprocess.run(["mkdocs", "--version"], check=True, capture_output=True, text=True)
        mkdocs_status = "✅ Installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        mkdocs_status = "❌ Not installed"
    
    # Check if mike is installed
    try:
        subprocess.run(["mike", "--version"], check=True, capture_output=True, text=True)
        mike_status = "✅ Installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        mike_status = "❌ Not installed"
    
    # Check if twine is installed
    try:
        subprocess.run(["twine", "--version"], check=True, capture_output=True, text=True)
        twine_status = "✅ Installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        twine_status = "❌ Not installed"
    
    # Check if build is installed
    try:
        subprocess.run(["python3", "-m", "build", "--version"], check=True, capture_output=True, text=True)
        build_status = "✅ Installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        build_status = "❌ Not installed"
    
    # Check for GitHub CLI
    try:
        subprocess.run(["gh", "--version"], check=True, capture_output=True, text=True)
        gh_cli_status = "✅ Installed"
    except (subprocess.CalledProcessError, FileNotFoundError):
        gh_cli_status = "❌ Not installed"
    
    # Check for config files
    readthedocs_yaml = "✅ Found" if (ROOT_DIR / ".readthedocs.yml").exists() else "❌ Not found"
    mkdocs_yaml = "✅ Found" if (ROOT_DIR / "mkdocs.yml").exists() else "❌ Not found"
    github_actions = "✅ Found" if check_github_actions_file() else "❌ Not found"
    
    # Get GitHub info
    github_owner, github_repo, _ = get_github_info()
    github_info = f"{github_owner}/{github_repo}" if github_owner and github_repo else "❌ Not detected"
    
    # Print status table
    print(f"{'Platform':<20} {'Status':<15} {'Details':<30}")
    print(f"{'-'*20} {'-'*15} {'-'*30}")
    print(f"{'GitHub README':<20} {'✅ Ready':<15} {'Auto-published on push':<30}")
    print(f"{'PyPI':<20} {twine_status:<15} {'Package documentation':<30}")
    print(f"{'Read the Docs':<20} {readthedocs_yaml:<15} {'Webhook integration':<30}")
    print(f"{'GitHub Pages':<20} {mkdocs_status:<15} {'MkDocs gh-deploy':<30}")
    print(f"{'GitHub Actions':<20} {github_actions:<15} {'Automated Pages deployment':<30}")
    print(f"{'Versioned Docs':<20} {mike_status:<15} {'Multiple version support':<30}")
    
    print("\nTools Status:")
    print(f"{'MkDocs':<20} {mkdocs_status:<15}")
    print(f"{'Mike':<20} {mike_status:<15}")
    print(f"{'Twine':<20} {twine_status:<15}")
    print(f"{'Build':<20} {build_status:<15}")
    print(f"{'GitHub CLI':<20} {gh_cli_status:<15}")
    
    print("\nConfig Files:")
    print(f"{'.readthedocs.yml':<20} {readthedocs_yaml:<15}")
    print(f"{'mkdocs.yml':<20} {mkdocs_yaml:<15}")
    print(f"{'GitHub Actions':<20} {github_actions:<15}")
    
    print(f"\nGitHub Repository: {github_info}")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Publish documentation for evrmore-rpc to multiple platforms",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Supported Documentation Platforms:
    - GitHub README      (automatically published on git push)
    - PyPI Documentation (published with twine)
    - Read the Docs      (webhook triggered on git push)
    - GitHub Pages       (published with mkdocs gh-deploy or GitHub Actions)
    - Versioned Docs     (published with mike if installed)
        """
    )
    parser.add_argument("--version", help="Version to publish")
    parser.add_argument("--no-pypi", action="store_true", help="Skip publishing to PyPI")
    parser.add_argument("--no-rtd", action="store_true", help="Skip Read the Docs related tasks")
    parser.add_argument("--no-github-pages", action="store_true", help="Skip GitHub Pages deployment")
    parser.add_argument("--dry-run", action="store_true", help="Don't actually publish, just show commands")
    parser.add_argument("--force", action="store_true", help="Force publishing even if there are no changes")
    parser.add_argument("--trigger-rtd-build", action="store_true", help="Trigger a build on Read the Docs")
    parser.add_argument("--rtd-project", default="evrmore-rpc", help="Read the Docs project name")
    parser.add_argument("--rtd-token", help="Read the Docs API token")
    parser.add_argument("--github-actions", action="store_true", help="Use GitHub Actions for GitHub Pages")
    parser.add_argument("--check-platforms", action="store_true", help="Check status of documentation platforms and exit")
    
    args = parser.parse_args()
    
    # Change to project root directory
    os.chdir(ROOT_DIR)
    
    # Check platform status if requested
    if args.check_platforms:
        print_platform_status()
        return 0
    
    # Detect GitHub Actions workflow file
    has_github_actions = check_github_actions_file()
    if args.github_actions and not has_github_actions:
        print("Warning: GitHub Actions workflow file not found, but --github-actions flag was used.")
        print("Create .github/workflows/docs.yml to use GitHub Actions for GitHub Pages.")
    
    # Get current version if not specified
    version = args.version or get_current_version()
    if not version:
        print("Error: Could not determine version. Please specify with --version")
        return 1
    
    print(f"Publishing documentation for version {version}")
    
    # Check if there are uncommitted changes
    has_changes = check_uncommitted_changes()
    if not has_changes and not args.force and not args.dry_run:
        print("No uncommitted changes detected. Use --force to publish anyway.")
        return 0
    
    # Update version in files
    if not args.dry_run:
        updated_files = update_version(version)
        if updated_files:
            print(f"Updated version in: {', '.join(updated_files)}")
        else:
            print("No files needed version updates")
    else:
        # For dry run, pretend we updated files
        updated_files = ["pyproject.toml", "evrmore_rpc/__init__.py"]
    
    # Commit and push changes if files were updated
    if updated_files and not commit_and_push(updated_files, version, args.dry_run):
        print("Error: Failed to commit and push changes")
        return 1
    
    # Build and publish to PyPI
    if not args.no_pypi:
        if not build_and_publish_pypi(args.dry_run):
            print("Error: Failed to publish to PyPI")
            return 1
    
    # Build and deploy to GitHub Pages
    if not args.no_github_pages:
        # Determine whether to use GitHub Actions or mkdocs gh-deploy
        use_github_actions = args.github_actions or (has_github_actions and not args.dry_run)
        
        if use_github_actions:
            # Trigger GitHub Actions workflow
            if not trigger_github_actions_workflow(args.dry_run):
                print("Warning: Failed to trigger GitHub Actions workflow")
                print("Documentation will still be built on next push to main branch")
        else:
            # Use traditional mkdocs gh-deploy
            if not build_and_publish_github_pages(False, args.dry_run):
                print("Error: Failed to publish to GitHub Pages")
                return 1
    
    # Build versioned documentation
    if not args.no_github_pages and not args.github_actions:
        build_versioned_docs(version, args.dry_run)
    
    # Trigger Read the Docs build if requested
    if args.trigger_rtd_build and not args.no_rtd:
        if not args.rtd_token:
            print("Warning: Read the Docs token not provided, skipping RTD build trigger")
        else:
            if not trigger_readthedocs_build(args.rtd_project, args.rtd_token, "latest", args.dry_run):
                print("Error: Failed to trigger Read the Docs build")
                return 1
    
    # Get GitHub repository info for URLs
    github_owner, github_repo, _ = get_github_info()
    
    print(f"\nSuccessfully published documentation for version {version}")
    print("\nDocumentation is now available at:")
    
    if github_owner and github_repo:
        print(f"- GitHub: https://github.com/{github_owner}/{github_repo}#readme")
        print(f"- GitHub Pages: https://{github_owner}.github.io/{github_repo}/")
    else:
        print("- GitHub: <repository URL not detected>")
    
    print(f"- PyPI: https://pypi.org/project/evrmore-rpc/")
    print(f"- Read the Docs: https://{args.rtd_project}.readthedocs.io/")
    
    if args.github_actions and has_github_actions:
        print("\nNote: GitHub Pages deployment via GitHub Actions may take a few minutes to complete.")
        print("Check the Actions tab on GitHub for progress.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 