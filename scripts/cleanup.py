#!/usr/bin/env python3
"""
Cleanup script to remove unnecessary files after streamlining the codebase.

This script removes old client implementations, command modules, and other files
that are no longer needed in the simplified API.
"""

import os
import shutil
from pathlib import Path

# Files to remove
FILES_TO_REMOVE = [
    # Old client implementations
    "evrmore_rpc/async_client.py",
    "evrmore_rpc/base_client.py",
    "evrmore_rpc/direct_client.py",
    "evrmore_rpc/async_direct_client.py",
    "evrmore_rpc/client.pyi",
    
    # Old examples
    "examples/async_client_example.py",
    "examples/async_example.py",
    "examples/async_reliable_demo.py",
    "examples/async_test.py",
    "examples/auto_detect_example.py",
    "examples/custom_async_demo.py",
    "examples/no_context_manager.py",
    "examples/polymorphic_example.py",
    "examples/simple_async_demo.py",
    "examples/zmq_quick_test.py",
]

# Directories to remove
DIRS_TO_REMOVE = [
    "evrmore_rpc/commands",
    "evrmore_rpc/websockets",
    "evrmore_rpc/zmq",
    "build",
    "dist",
    "evrmore_rpc.egg-info",
    "examples/websockets",
    "examples/zmq",
    "examples/async",
]

def main():
    """Run the cleanup process"""
    print("Starting cleanup process...")
    
    # Remove individual files
    for file_path in FILES_TO_REMOVE:
        path = Path(file_path)
        if path.exists():
            print(f"Removing file: {file_path}")
            path.unlink()
        else:
            print(f"File not found, skipping: {file_path}")
    
    # Remove directories
    for dir_path in DIRS_TO_REMOVE:
        path = Path(dir_path)
        if path.exists() and path.is_dir():
            print(f"Removing directory: {dir_path}")
            shutil.rmtree(path)
        else:
            print(f"Directory not found, skipping: {dir_path}")
    
    print("Cleanup completed!")

if __name__ == "__main__":
    main() 