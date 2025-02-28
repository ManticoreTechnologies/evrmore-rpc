import sys
import argparse
from pathlib import Path
from typing import List, Optional
import json
from rich.console import Console
from rich.table import Table

from evrmore_rpc.client import EvrmoreRPCClient
from evrmore_rpc.interactive import interactive_menu

console = Console()

def create_parser() -> argparse.ArgumentParser:
    """Create the command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Evrmore RPC CLI - A Python wrapper for evrmore-cli",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Add interactive mode
    parser.add_argument(
        "-i", "--interactive",
        action="store_true",
        help="Start in interactive mode"
    )
    
    parser.add_argument(
        "command",
        nargs="?",
        help="The RPC command to execute"
    )
    
    parser.add_argument(
        "args",
        nargs="*",
        help="Arguments for the RPC command"
    )
    
    parser.add_argument(
        "--datadir",
        type=Path,
        help="Path to Evrmore data directory"
    )
    
    parser.add_argument(
        "--rpcuser",
        help="RPC username"
    )
    
    parser.add_argument(
        "--rpcpassword",
        help="RPC password"
    )
    
    parser.add_argument(
        "--rpcport",
        type=int,
        help="RPC port number"
    )
    
    parser.add_argument(
        "--testnet",
        action="store_true",
        help="Use testnet"
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON"
    )
    
    return parser

def format_output(result: any, use_json: bool = False) -> None:
    """Format and display the command output."""
    if use_json:
        if isinstance(result, (dict, list)):
            console.print(json.dumps(result, indent=2))
        else:
            console.print(json.dumps({"result": result}, indent=2))
    else:
        if isinstance(result, dict):
            table = Table(show_header=True)
            table.add_column("Key")
            table.add_column("Value")
            for key, value in result.items():
                table.add_row(str(key), str(value))
            console.print(table)
        elif isinstance(result, list):
            if all(isinstance(item, dict) for item in result):
                if result:
                    table = Table(show_header=True)
                    for key in result[0].keys():
                        table.add_column(str(key))
                    for item in result:
                        table.add_row(*[str(v) for v in item.values()])
                    console.print(table)
            else:
                for item in result:
                    console.print(item)
        else:
            console.print(result)

def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for the CLI."""
    parser = create_parser()
    args = parser.parse_args(argv)
    
    try:
        client = EvrmoreRPCClient(
            datadir=args.datadir,
            rpcuser=args.rpcuser,
            rpcpassword=args.rpcpassword,
            rpcport=args.rpcport,
            testnet=args.testnet
        )
        
        if args.interactive:
            interactive_menu()
            return 0
            
        if not args.command:
            parser.print_help()
            return 1
            
        result = client.execute_command(args.command, *args.args)
        format_output(result, args.json)
        return 0
        
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 