#!/usr/bin/env python3
"""
Simple Async Demo for Evrmore RPC

This example demonstrates basic usage of the EvrmoreAsyncRPCClient.
It gets blockchain information, block details, and asset listings.
"""

import asyncio
import time
from rich.console import Console
from rich.table import Table
from evrmore_rpc import EvrmoreAsyncRPCClient

console = Console()

async def main():
    """Main demo function"""
    console.print("[bold green]Evrmore Simple Async Demo[/]")
    console.print("[cyan]Demonstrating basic async RPC functionality[/]")
    console.print()
    
    # Record start time to show performance benefits
    start_time = time.time()
    
    # Connect to the node and make queries
    async with EvrmoreAsyncRPCClient() as client:
        # Start all queries in parallel
        blockcount_task = client.getblockcount()
        blockhash_task = None  # We'll create this after we get the blockcount
        assets_task = client.listassets("*", False)
        
        # Get blockcount first
        blockcount = await blockcount_task
        console.print(f"Current block height: [bold cyan]{blockcount}[/]")
        
        # Now get block hash for this height and start that query
        blockhash_task = client.getblockhash(blockcount)
        blockhash = await blockhash_task
        
        # Then get full block details and assets info in parallel
        block_task = client.getblock(blockhash)
        block, assets = await asyncio.gather(block_task, assets_task)
        
        # Display block information
        console.print("\n[bold blue]Latest Block Information[/]")
        block_table = Table(show_header=True, header_style="bold green")
        block_table.add_column("Field")
        block_table.add_column("Value")
        
        block_table.add_row("Hash", block.hash)
        block_table.add_row("Previous Block", block.previousblockhash)
        block_table.add_row("Merkle Root", block.merkleroot)
        block_table.add_row("Time", str(block.time))
        block_table.add_row("Difficulty", str(block.difficulty))
        block_table.add_row("Number of Transactions", str(len(block.tx)))
        block_table.add_row("Size", f"{block.size:,} bytes")
        
        console.print(block_table)
        
        # Display assets (just 5 for brevity)
        console.print("\n[bold blue]Some Evrmore Assets[/]")
        assets_table = Table(show_header=True, header_style="bold green")
        assets_table.add_column("Asset Name")
        assets_table.add_column("Balance/Supply")
        
        # Take just 5 assets for demonstration
        for i, (name, amount) in enumerate(assets.items()):
            if i >= 5:
                break
            assets_table.add_row(name, str(amount))
        
        console.print(assets_table)
        
        # Show some transactions from the block
        console.print("\n[bold blue]Latest Transactions[/]")
        tx_table = Table(show_header=True, header_style="bold green")
        tx_table.add_column("TXID", no_wrap=True)
        
        # Show just 3 transactions
        for txid in block.tx[:3]:
            tx_table.add_row(txid)
        
        console.print(tx_table)
    
    # Calculate and display execution time
    execution_time = time.time() - start_time
    console.print(f"\n[bold green]Total execution time: {execution_time:.2f} seconds[/]")
    console.print("[italic]Using async/await allowed these queries to run efficiently![/]")

if __name__ == "__main__":
    asyncio.run(main()) 