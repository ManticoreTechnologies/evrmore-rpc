#!/usr/bin/env python3
"""
Build and deploy documentation for the evrmore-rpc package.
"""

import os
import subprocess
import sys


def main():
    """
    Build and deploy documentation.
    
    This script:
    1. Builds the documentation using mkdocs
    2. Deploys the documentation to GitHub Pages if requested
    """
    # Get the project root directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.abspath(os.path.join(script_dir, ".."))
    
    # Change to the project root directory
    os.chdir(project_root)
    
    print("Building documentation...")
    subprocess.run([sys.executable, "-m", "mkdocs", "build"], check=True)
    
    # Check if the --deploy flag is set
    if "--deploy" in sys.argv:
        print("Deploying documentation to GitHub Pages...")
        subprocess.run([sys.executable, "-m", "mkdocs", "gh-deploy"], check=True)
    
    print("Documentation build complete!")
    

if __name__ == "__main__":
    main() 