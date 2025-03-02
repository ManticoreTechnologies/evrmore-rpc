#!/usr/bin/env python3
"""
Run all examples to verify they work correctly.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_example(example_path):
    """Run an example script and return success/failure."""
    print(f"\n{'='*50}")
    print(f"Running example: {example_path}")
    print(f"{'='*50}")
    
    result = subprocess.run([sys.executable, example_path], capture_output=True, text=True)
    
    if result.returncode == 0:
        print(f"SUCCESS: {example_path}")
        print(result.stdout)
        return True
    else:
        print(f"FAILURE: {example_path}")
        print(f"Exit code: {result.returncode}")
        print(f"Output: {result.stdout}")
        print(f"Error: {result.stderr}")
        return False

def main():
    """Run all examples."""
    examples_dir = Path("examples")
    
    # List of examples to run
    examples = [
        examples_dir / "super_simple.py",
        examples_dir / "seamless_api.py",
        examples_dir / "simple_auto_detect.py",
    ]
    
    # Run each example
    success_count = 0
    failure_count = 0
    
    for example in examples:
        if run_example(example):
            success_count += 1
        else:
            failure_count += 1
    
    # Print summary
    print(f"\n{'='*50}")
    print(f"Summary: {success_count} succeeded, {failure_count} failed")
    print(f"{'='*50}")
    
    return 0 if failure_count == 0 else 1

if __name__ == "__main__":
    sys.exit(main()) 