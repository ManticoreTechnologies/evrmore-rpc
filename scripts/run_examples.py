#!/usr/bin/env python3
"""
Run Evrmore RPC Examples

This script runs the examples in the examples directory.
"""

import argparse
import os
import subprocess
import sys

# Available examples
EXAMPLES = {
    "basic": [
        "super_simple.py",
        "seamless_api.py",
        "simple_auto_detect.py",
    ],
    "advanced": [
        "asset_monitor/monitor.py",
        "blockchain_explorer/explorer.py",
        "network_monitor/monitor.py",
        "wallet_tracker/tracker.py",
        "asset_swap/simple_swap.py",
    ],
}

# Simplified names for easier access
SIMPLIFIED_NAMES = {
    "super_simple": "super_simple.py",
    "seamless_api": "seamless_api.py",
    "simple_auto_detect": "simple_auto_detect.py",
    "asset_monitor": "asset_monitor/monitor.py",
    "blockchain_explorer": "blockchain_explorer/explorer.py",
    "network_monitor": "network_monitor/monitor.py",
    "wallet_tracker": "wallet_tracker/tracker.py",
    "asset_swap": "asset_swap/simple_swap.py",
}

def main():
    # Parse arguments
    parser = argparse.ArgumentParser(description="Run Evrmore RPC examples")
    parser.add_argument("example", nargs="?", help="Example to run")
    parser.add_argument("--list", action="store_true", help="List available examples")
    args = parser.parse_args()
    
    # List examples
    if args.list:
        print("Available examples:")
        print("\nBasic examples:")
        for example in EXAMPLES["basic"]:
            print(f"  {example}")
        print("\nAdvanced examples:")
        for example in EXAMPLES["advanced"]:
            print(f"  {example}")
        print("\nSimplified names:")
        for name, path in SIMPLIFIED_NAMES.items():
            print(f"  {name} -> {path}")
        return
    
    # Run example
    if args.example:
        # Check if it's a simplified name
        if args.example in SIMPLIFIED_NAMES:
            example_path = SIMPLIFIED_NAMES[args.example]
        else:
            # Find the example
            example_path = None
            for category in EXAMPLES:
                for example in EXAMPLES[category]:
                    if example == args.example or example.endswith(f"/{args.example}"):
                        example_path = example
                        break
                if example_path:
                    break
        
        if not example_path:
            print(f"Example '{args.example}' not found")
            return
        
        # Run the example
        print(f"Running example: {example_path}")
        example_full_path = os.path.join("examples", example_path)
        
        try:
            subprocess.run([sys.executable, example_full_path], check=True)
        except subprocess.CalledProcessError:
            print(f"Example '{example_path}' failed")
        except KeyboardInterrupt:
            print("\nExample interrupted")
    else:
        # No example specified
        parser.print_help()

if __name__ == "__main__":
    main() 