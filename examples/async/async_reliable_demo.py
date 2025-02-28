#!/usr/bin/env python3
"""
Reliable Async Demo for Evrmore RPC

This example demonstrates basic usage of the EvrmoreAsyncRPCClient
with robust handling of responses that can be either dictionaries or objects.
"""

import asyncio
import time
from rich.console import Console
from rich.table import Table
from evrmore_rpc import EvrmoreAsyncRPCClient

console = Console()

def safe_get(obj, key, default=None):
    """
    Safely access a property from an object that might be a dict or an object with attributes.
    
    Args:
        obj: The object to access a property from
        key: The property/key to access
        default: Default value if property doesn't exist
        
    Returns:
        The property value or default
    """
    if hasattr(obj, key):
        return getattr(obj, key)
    elif isinstance(obj, dict) and key in obj:
        return obj[key]
    return default

async def get_blockchain_info():
    """Get basic blockchain information"""
    async with EvrmoreAsyncRPCClient() as client:
        info = await client.getblockchaininfo()
        
        # Extract relevant information using the safe_get helper
        return {
            "chain": safe_get(info, "chain", "unknown"),
            "blocks": safe_get(info, "blocks", 0),
            "headers": safe_get(info, "headers", 0),
            "bestblockhash": safe_get(info, "bestblockhash", "unknown"),
            "difficulty": safe_get(info, "difficulty", 0),
            "mediantime": safe_get(info, "mediantime", 0),
            "size_on_disk": safe_get(info, "size_on_disk", 0),
        }

async def get_latest_block_details():
    """Get details about the latest block"""
    async with EvrmoreAsyncRPCClient() as client:
        # Get the latest block count and hash
        block_count = await client.getblockcount()
        block_hash = await client.getblockhash(block_count)
        
        # Get detailed block information
        block = await client.getblock(block_hash)
        
        return {
            "hash": safe_get(block, "hash", "unknown"),
            "confirmations": safe_get(block, "confirmations", 0),
            "size": safe_get(block, "size", 0),
            "height": safe_get(block, "height", 0),
            "merkleroot": safe_get(block, "merkleroot", "unknown"),
            "tx_count": len(safe_get(block, "tx", [])),
            "time": safe_get(block, "time", 0),
            "nonce": safe_get(block, "nonce", 0),
            "bits": safe_get(block, "bits", "unknown"),
            "difficulty": safe_get(block, "difficulty", 0),
        }

async def get_asset_info():
    """Get information about Evrmore assets"""
    async with EvrmoreAsyncRPCClient() as client:
        # Get the top 5 assets
        assets = await client.listassets("*", verbose=True)
        
        asset_info = []
        count = 0
        
        # Handle both dictionary responses and object responses
        if isinstance(assets, dict):
            for name, details in assets.items():
                if count >= 5:
                    break
                    
                asset_data = {
                    "name": name,
                    "amount": safe_get(details, "amount", 0),
                    "units": safe_get(details, "units", 0),
                    "reissuable": safe_get(details, "reissuable", False),
                    "has_ipfs": safe_get(details, "has_ipfs", False)
                }
                asset_info.append(asset_data)
                count += 1
        elif isinstance(assets, list):
            for asset in assets[:5]:
                asset_data = {
                    "name": safe_get(asset, "name", "unknown"),
                    "amount": safe_get(asset, "amount", 0),
                    "units": safe_get(asset, "units", 0),
                    "reissuable": safe_get(asset, "reissuable", False),
                    "has_ipfs": safe_get(asset, "has_ipfs", False)
                }
                asset_info.append(asset_data)
                
        return asset_info

async def main():
    """Main demo function"""
    console.print("[bold green]Evrmore Reliable Async Demo[/]")
    console.print("[cyan]Demonstrating robust async RPC functionality[/]")
    console.print()
    
    # Start timing
    start_time = time.time()
    
    # Run all queries in parallel
    blockchain_info_task = asyncio.create_task(get_blockchain_info())
    block_details_task = asyncio.create_task(get_latest_block_details())
    asset_info_task = asyncio.create_task(get_asset_info())
    
    # Wait for all tasks to complete
    blockchain_info, block_details, asset_info = await asyncio.gather(
        blockchain_info_task, block_details_task, asset_info_task
    )
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Display blockchain info
    console.print("[bold blue]Blockchain Information[/]")
    blockchain_table = Table(show_header=True, header_style="bold green")
    blockchain_table.add_column("Field")
    blockchain_table.add_column("Value")
    
    for key, value in blockchain_info.items():
        blockchain_table.add_row(key, str(value))
    
    console.print(blockchain_table)
    console.print()
    
    # Display block details
    console.print("[bold blue]Latest Block Details[/]")
    block_table = Table(show_header=True, header_style="bold green")
    block_table.add_column("Field")
    block_table.add_column("Value")
    
    for key, value in block_details.items():
        block_table.add_row(key, str(value))
    
    console.print(block_table)
    console.print()
    
    # Display asset information
    console.print("[bold blue]Asset Information[/]")
    asset_table = Table(show_header=True, header_style="bold green")
    asset_table.add_column("Name")
    asset_table.add_column("Amount")
    asset_table.add_column("Units")
    asset_table.add_column("Reissuable")
    asset_table.add_column("Has IPFS")
    
    for asset in asset_info:
        asset_table.add_row(
            str(asset["name"]),
            str(asset["amount"]),
            str(asset["units"]),
            "Yes" if asset["reissuable"] else "No",
            "Yes" if asset["has_ipfs"] else "No"
        )
    
    console.print(asset_table)
    console.print()
    
    # Display execution time
    console.print(f"[bold green]Total execution time: {execution_time:.2f} seconds[/]")
    console.print("[italic]Using async/await allowed these queries to run in parallel![/]")

if __name__ == "__main__":
    asyncio.run(main()) 