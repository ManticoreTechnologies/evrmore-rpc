#!/usr/bin/env python3
"""
Stress test for evrmore-rpc client
Run directly with: python -m evrmore_rpc.stress_test
"""

import asyncio
import argparse
import json
import time
import threading
from queue import Queue
from typing import Dict, Any, Optional, Union
from rich.console import Console
from rich.table import Table
from rich import box

# Import client directly to avoid circular imports
from evrmore_rpc.client import EvrmoreClient
from evrmore_rpc.utils import sync_or_async, is_async_context

console = Console()

async def run_stress_test_async(
    url: Optional[str] = None,
    datadir: Optional[str] = None,
    rpcuser: Optional[str] = None,
    rpcpassword: Optional[str] = None,
    testnet: bool = False,
    timeout: int = 30,
    num_calls: int = 100,
    command: str = "getblockcount",
    concurrency: int = 10
) -> Dict[str, Any]:
    """
    Run asynchronous stress test with the specified parameters
    
    Args:
        url: RPC URL (e.g., http://user:pass@localhost:8819/)
        datadir: Evrmore data directory
        rpcuser: RPC username
        rpcpassword: RPC password
        testnet: Use testnet
        timeout: Request timeout in seconds
        num_calls: Number of calls to make
        command: RPC command to execute
        concurrency: Concurrency level for test
        
    Returns:
        Dictionary with test results
    """
    console.print(f"[bold green]Running async stress test with {num_calls} calls to {command}...[/]")
    
    client = EvrmoreClient(
        url=url,
        datadir=datadir,
        rpcuser=rpcuser,
        rpcpassword=rpcpassword,
        testnet=testnet,
        timeout=timeout,
        async_mode=True
    )
    
    async with client:
        results = await client.stress_test(
            num_calls=num_calls,
            command=command,
            concurrency=concurrency
        )
    
    display_results(results)
    return results

def run_stress_test_sync(
    url: Optional[str] = None,
    datadir: Optional[str] = None,
    rpcuser: Optional[str] = None,
    rpcpassword: Optional[str] = None,
    testnet: bool = False,
    timeout: int = 30,
    num_calls: int = 100,
    command: str = "getblockcount",
    concurrency: int = 10
) -> Dict[str, Any]:
    """
    Run synchronous stress test with the specified parameters
    
    Args:
        url: RPC URL (e.g., http://user:pass@localhost:8819/)
        datadir: Evrmore data directory
        rpcuser: RPC username
        rpcpassword: RPC password
        testnet: Use testnet
        timeout: Request timeout in seconds
        num_calls: Number of calls to make
        command: RPC command to execute
        concurrency: Concurrency level for test
        
    Returns:
        Dictionary with test results
    """
    console.print(f"[bold green]Running sync stress test with {num_calls} calls to {command}...[/]")
    
    client = EvrmoreClient(
        url=url,
        datadir=datadir,
        rpcuser=rpcuser,
        rpcpassword=rpcpassword,
        testnet=testnet,
        timeout=timeout,
        async_mode=False
    )
    
    with client:
        results = client.stress_test(
            num_calls=num_calls,
            command=command,
            concurrency=concurrency
        )
    
    display_results(results)
    return results

def run_stress_test(
    url: Optional[str] = None,
    datadir: Optional[str] = None,
    rpcuser: Optional[str] = None,
    rpcpassword: Optional[str] = None,
    testnet: bool = False,
    timeout: int = 30,
    num_calls: int = 100,
    command: str = "getblockcount",
    concurrency: int = 10,
    async_mode: Optional[bool] = None
) -> Union[Dict[str, Any], asyncio.coroutine]:
    """
    Run stress test with the specified parameters.
    Automatically detects whether to run in sync or async mode based on the context.
    
    Args:
        url: RPC URL (e.g., http://user:pass@localhost:8819/)
        datadir: Evrmore data directory
        rpcuser: RPC username
        rpcpassword: RPC password
        testnet: Use testnet
        timeout: Request timeout in seconds
        num_calls: Number of calls to make
        command: RPC command to execute
        concurrency: Concurrency level for test
        async_mode: Force async mode (True) or sync mode (False). If None, auto-detect.
        
    Returns:
        Dictionary with test results or coroutine if async
    """
    # Create a client with auto-detection
    client = EvrmoreClient(
        url=url,
        datadir=datadir,
        rpcuser=rpcuser,
        rpcpassword=rpcpassword,
        testnet=testnet,
        timeout=timeout,
        async_mode=async_mode
    )
    
    # Use sync_or_async to automatically choose the right implementation
    return sync_or_async(
        lambda: run_with_sync_client(client, num_calls, command, concurrency),
        lambda: run_with_async_client(client, num_calls, command, concurrency)
    )()

def run_with_sync_client(client: EvrmoreClient, num_calls: int, command: str, concurrency: int) -> Dict[str, Any]:
    """Run stress test with a synchronous client"""
    console.print(f"[bold green]Running auto-detected sync stress test with {num_calls} calls to {command}...[/]")
    with client:
        results = client.stress_test(num_calls=num_calls, command=command, concurrency=concurrency)
    display_results(results)
    return results

async def run_with_async_client(client: EvrmoreClient, num_calls: int, command: str, concurrency: int) -> Dict[str, Any]:
    """Run stress test with an asynchronous client"""
    console.print(f"[bold green]Running auto-detected async stress test with {num_calls} calls to {command}...[/]")
    async with client:
        results = await client.stress_test(num_calls=num_calls, command=command, concurrency=concurrency)
    display_results(results)
    return results

def display_results(results: Dict[str, Any]) -> None:
    """Display test results in a nice table"""
    table = Table(title="Stress Test Results", box=box.ROUNDED)
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("Total Time", f"{results['total_time']:.2f} seconds")
    table.add_row("Requests Per Second", f"{results['requests_per_second']:.2f}")
    table.add_row("Average Response Time", f"{results['avg_time']:.2f} ms")
    table.add_row("Median Response Time", f"{results['median_time']:.2f} ms")
    table.add_row("Min Response Time", f"{results['min_time']:.2f} ms")
    table.add_row("Max Response Time", f"{results['max_time']:.2f} ms")
    table.add_row("Number of Calls", str(results['num_calls']))
    table.add_row("Concurrency", str(results['concurrency']))
    
    # Add last result in a readable format
    last_result = results['last_result']
    if isinstance(last_result, (dict, list)):
        last_result = json.dumps(last_result, indent=2)
    table.add_row("Last Result", str(last_result))
    
    console.print(table)

async def _main_async():
    """Asynchronous command-line entry point"""
    parser = argparse.ArgumentParser(description="Stress test for evrmore-rpc client")
    parser.add_argument("--url", help="RPC URL (e.g., http://user:pass@localhost:8819/)")
    parser.add_argument("--datadir", help="Evrmore data directory")
    parser.add_argument("--rpcuser", help="RPC username")
    parser.add_argument("--rpcpassword", help="RPC password")
    parser.add_argument("--testnet", action="store_true", help="Use testnet")
    parser.add_argument("--timeout", type=int, default=30, help="Request timeout in seconds")
    parser.add_argument("--num-calls", type=int, default=100, help="Number of calls to make")
    parser.add_argument("--command", default="getblockcount", help="RPC command to execute")
    parser.add_argument("--concurrency", type=int, default=10, help="Concurrency level for test")
    parser.add_argument("--sync", action="store_true", help="Force synchronous mode")
    
    args = parser.parse_args()
    
    start_time = time.time()
    
    # Use the run_stress_test function which auto-detects the context
    result = run_stress_test(
        url=args.url,
        datadir=args.datadir,
        rpcuser=args.rpcuser,
        rpcpassword=args.rpcpassword,
        testnet=args.testnet,
        timeout=args.timeout,
        num_calls=args.num_calls,
        command=args.command,
        concurrency=args.concurrency,
        async_mode=args.sync is False if args.sync else None
    )
    
    # If we're in an async context and result is a coroutine, await it
    if is_async_context() and asyncio.iscoroutine(result):
        await result
    
    total_time = time.time() - start_time
    console.print(f"[bold]Total test time: {total_time:.2f} seconds[/]")

def main():
    """Synchronous entry point for command-line usage"""
    asyncio.run(_main_async())

if __name__ == "__main__":
    main() 