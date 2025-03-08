#!/usr/bin/env python3
"""
Deploy script for publishing evrmore-rpc to PyPI

This script performs pre-publication checks and then publishes the package to PyPI.
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add parent directory to path to import check_publication
script_dir = Path(__file__).resolve().parent
sys.path.append(str(script_dir))

# Import check_publication functions
from check_publication import (
    check_version_consistency,
    check_readme,
    check_license,
    check_docs,
    check_examples,
    check_build,
    check_tests,
)

def run_checks():
    """Run all pre-publication checks."""
    print("Running pre-publication checks...")
    
    checks = [
        check_version_consistency,
        check_readme,
        check_license,
        check_docs,
        check_examples,
        check_build,
        check_tests,
    ]
    
    results = []
    for check in checks:
        print(f"\n{'-' * 40}")
        print(f"Running {check.__name__}...")
        try:
            result = check()
            results.append(result)
        except Exception as e:
            print(f"ERROR: Check failed with exception: {e}")
            results.append(False)
    
    print(f"\n{'-' * 40}")
    print(f"Summary: {sum(results)}/{len(results)} checks passed")
    
    if all(results):
        print("\nAll checks passed! The package is ready for publication.")
        return True
    else:
        print("\nSome checks failed. Please fix the issues before publication.")
        return False

def clean_build():
    """Clean build artifacts."""
    print("Cleaning build artifacts...")
    
    dirs_to_clean = [
        "build",
        "dist",
        "evrmore_rpc.egg-info",
    ]
    
    for dir_path in dirs_to_clean:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"Removing {dir_path}...")
            subprocess.run(["rm", "-rf", dir_path], check=True)

def build_package():
    """Build the package for distribution."""
    print("Building package...")
    
    result = subprocess.run(
        ["python3", "-m", "build"],
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        print(f"ERROR: Build failed with exit code {result.returncode}")
        print(result.stderr)
        return False
    
    print("Package built successfully.")
    return True

def upload_to_pypi(test=True):
    """Upload the package to PyPI or TestPyPI."""
    if test:
        print("Uploading to TestPyPI...")
        repository = "--repository testpypi"
    else:
        print("Uploading to PyPI...")
        repository = ""
    
    cmd = f"python3 -m twine upload {repository} dist/*"
    
    print(f"Running: {cmd}")
    result = subprocess.run(
        cmd.split(),
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        print(f"ERROR: Upload failed with exit code {result.returncode}")
        print(result.stderr)
        return False
    
    print("Upload successful!")
    return True

def main():
    """Main function to deploy the package."""
    parser = argparse.ArgumentParser(description="Deploy evrmore-rpc to PyPI")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Upload to TestPyPI instead of PyPI",
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip pre-publication checks",
    )
    parser.add_argument(
        "--skip-clean",
        action="store_true",
        help="Skip cleaning build artifacts",
    )
    args = parser.parse_args()
    
    # Change directory to project root
    os.chdir(str(script_dir.parent))
    
    # Run checks
    if not args.skip_checks:
        if not run_checks():
            print("Aborting due to failed checks.")
            return 1
    
    # Clean build artifacts
    if not args.skip_clean:
        clean_build()
    
    # Build package
    if not build_package():
        print("Aborting due to build failure.")
        return 1
    
    # Upload to PyPI
    if not upload_to_pypi(test=args.test):
        print("Aborting due to upload failure.")
        return 1
    
    print("\nDeployment completed successfully!")
    if args.test:
        print("\nTest package URL: https://test.pypi.org/project/evrmore-rpc/")
        print("To install from TestPyPI:")
        print("pip install -i https://test.pypi.org/simple/ evrmore-rpc")
    else:
        print("\nPackage URL: https://pypi.org/project/evrmore-rpc/")
        print("To install:")
        print("pip install evrmore-rpc")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 