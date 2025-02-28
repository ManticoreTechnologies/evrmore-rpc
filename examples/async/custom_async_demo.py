#!/usr/bin/env python3
"""
Custom Async Demo for Evrmore RPC

This example demonstrates using the async client to query multiple pieces of data in parallel,
showing how developers can efficiently gather blockchain data for real applications.
"""

import asyncio
import time
from decimal import Decimal
from rich.console import Console
from rich.table import Table
from rich.progress import Progress
from evrmore_rpc import EvrmoreAsyncRPCClient

console = Console()

async def get_blockchain_stats():
    """Get general blockchain statistics"""
    async with EvrmoreAsyncRPCClient() as client:
        # Start all queries in parallel
        tasks = [
            client.getblockcount(),
            client.getblockchaininfo(),
            client.getnetworkinfo(),
            client.getmininginfo(),
            client.getwalletinfo()
        ]
        
        # Wait for all to complete
        block_count, blockchain_info, network_info, mining_info, wallet_info = await asyncio.gather(*tasks)
        
        return {
            "block_height": block_count,
            "chain": blockchain_info["chain"],
            "difficulty": blockchain_info["difficulty"],
            "connections": network_info["connections"],
            "version": network_info["version"],
            "proxy": network_info["proxy"] or "none",
            "hashrate": mining_info["networkhashps"],
            "balance": wallet_info["balance"],
            "unconfirmed_balance": wallet_info["unconfirmed_balance"],
            "immature_balance": wallet_info["immature_balance"],
            "txcount": wallet_info["txcount"]
        }

async def get_asset_analysis(asset_filter="*", limit=10):
    """Get detailed analysis of assets"""
    async with EvrmoreAsyncRPCClient() as client:
        # Get all assets
        all_assets = await client.listassets(asset_filter, verbose=True)
        
        # Process the assets - check if it's a dict or list
        if isinstance(all_assets, list):
            # Convert list to dict for compatibility
            assets_dict = {asset["name"]: asset for asset in all_assets}
        else:
            # Convert to a dict we can work with
            assets_dict = {}
            for k, v in all_assets.items():
                if isinstance(v, dict):
                    assets_dict[k] = v
                else:
                    # Handle case where v is an object with attributes
                    assets_dict[k] = {
                        "amount": getattr(v, "amount", 0),
                        "units": getattr(v, "units", 0),
                        "reissuable": getattr(v, "reissuable", False),
                        "has_ipfs": getattr(v, "has_ipfs", False),
                        "ipfs": getattr(v, "ipfs", "")
                    }
        
        # Sort by total supply (largest first)
        sorted_assets = sorted(
            [(name, details) for name, details in assets_dict.items()], 
            key=lambda x: float(x[1].get("amount", 0)) if isinstance(x[1].get("amount", 0), (str, int, float)) else 0,
            reverse=True
        )
        
        # Limit to specified number
        top_assets = sorted_assets[:limit]
        
        # Process each asset in parallel
        async def process_asset(name, details):
            # Get supply value safely
            supply = details.get("amount", 0)
            if not isinstance(supply, (int, float, Decimal)):
                try:
                    supply = Decimal(supply)
                except (TypeError, ValueError):
                    supply = Decimal(0)
            
            # In a real app, you could do more detailed analysis here
            asset_data = {
                "name": name,
                "supply": supply,
                "units": details.get("units", 0),
                "reissuable": details.get("reissuable", False),
                "has_ipfs": details.get("has_ipfs", False),
                "ipfs_hash": details.get("ipfs", "")
            }
            
            return asset_data
        
        # Process all assets in parallel
        tasks = [process_asset(name, details) for name, details in top_assets]
        results = await asyncio.gather(*tasks)
        
        return results

async def get_latest_transactions(count=5):
    """Get details about the latest transactions"""
    async with EvrmoreAsyncRPCClient() as client:
        # Get latest block
        block_count = await client.getblockcount()
        block_hash = await client.getblockhash(block_count)
        block = await client.getblock(block_hash)
        
        # Get the transactions from the latest block
        txids = block["tx"][:count] if isinstance(block, dict) else block.tx[:count]  # Limit to the first 'count' transactions
        
        # Process each transaction in parallel
        async def get_tx_details(txid):
            try:
                # Get full transaction details
                tx = await client.getrawtransaction(txid, True)
                
                # Calculate the total input and output values
                vin_count = len(tx["vin"] if isinstance(tx, dict) else tx.vin)
                vout_count = len(tx["vout"] if isinstance(tx, dict) else tx.vout)
                
                # Calculate total output from all vouts
                if isinstance(tx, dict):
                    total_output = sum(out.get("value", 0) for out in tx["vout"])
                else:
                    total_output = sum(getattr(out, "value", 0) for out in tx.vout)
                
                # Look for asset transactions
                assets = []
                vouts = tx["vout"] if isinstance(tx, dict) else tx.vout
                
                for vout in vouts:
                    # Handle both dict and object access
                    if isinstance(vout, dict):
                        scriptPubKey = vout.get("scriptPubKey", {})
                        asset_info = scriptPubKey.get("asset", {}) if isinstance(scriptPubKey, dict) else None
                        
                        if asset_info:
                            assets.append({
                                "name": asset_info.get("name", ""),
                                "amount": asset_info.get("amount", 0)
                            })
                    else:
                        scriptPubKey = getattr(vout, "scriptPubKey", None)
                        if scriptPubKey and hasattr(scriptPubKey, "asset"):
                            asset_info = scriptPubKey.asset
                            assets.append({
                                "name": getattr(asset_info, "name", ""),
                                "amount": getattr(asset_info, "amount", 0)
                            })
                
                return {
                    "txid": txid,
                    "size": tx.get("size", 0) if isinstance(tx, dict) else getattr(tx, "size", 0),
                    "time": tx.get("time", 0) if isinstance(tx, dict) else getattr(tx, "time", 0),
                    "vin_count": vin_count,
                    "vout_count": vout_count,
                    "total_output": total_output,
                    "has_assets": len(assets) > 0,
                    "assets": assets
                }
            except Exception as e:
                return {"txid": txid, "error": str(e)}
        
        # Get all transaction details in parallel
        tasks = [get_tx_details(txid) for txid in txids]
        
        # Show a progress indicator
        with Progress() as progress:
            task = progress.add_task("[cyan]Fetching transactions...", total=len(txids))
            
            # Process the transactions with progress updates
            results = []
            for coro in asyncio.as_completed(tasks):
                tx = await coro
                results.append(tx)
                progress.update(task, advance=1)
        
        return results
        
async def main():
    """Main demo function"""
    console.print("[bold green]Evrmore Async API Demo[/]")
    console.print("[cyan]Demonstrating parallel queries for efficient blockchain data retrieval[/]")
    console.print()
    
    # Start timing
    start_time = time.time()
    
    # Get blockchain stats, asset analysis, and latest transactions in parallel
    stats_task = asyncio.create_task(get_blockchain_stats())
    assets_task = asyncio.create_task(get_asset_analysis(limit=5))
    tx_task = asyncio.create_task(get_latest_transactions(count=3))
    
    # Wait for all to complete
    stats, assets, transactions = await asyncio.gather(
        stats_task, assets_task, tx_task
    )
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    # Display blockchain stats
    console.print("[bold blue]Blockchain Statistics[/]")
    stats_table = Table(show_header=True, header_style="bold green")
    stats_table.add_column("Stat")
    stats_table.add_column("Value")
    
    for key, value in stats.items():
        stats_table.add_row(key, str(value))
    
    console.print(stats_table)
    console.print()
    
    # Display asset information
    console.print("[bold blue]Top Assets by Supply[/]")
    assets_table = Table(show_header=True, header_style="bold green")
    assets_table.add_column("Name")
    assets_table.add_column("Supply")
    assets_table.add_column("Units")
    assets_table.add_column("Reissuable")
    assets_table.add_column("Has IPFS")
    
    for asset in assets:
        assets_table.add_row(
            asset["name"],
            str(asset["supply"]),
            str(asset["units"]),
            "Yes" if asset["reissuable"] else "No",
            "Yes" if asset["has_ipfs"] else "No"
        )
    
    console.print(assets_table)
    console.print()
    
    # Display transaction information
    console.print("[bold blue]Latest Transactions[/]")
    tx_table = Table(show_header=True, header_style="bold green")
    tx_table.add_column("TXID")
    tx_table.add_column("Size")
    tx_table.add_column("Inputs")
    tx_table.add_column("Outputs")
    tx_table.add_column("Total Value")
    tx_table.add_column("Assets")
    
    for tx in transactions:
        if "error" in tx:
            tx_table.add_row(
                tx["txid"][:10] + "...",
                "ERROR",
                "",
                "",
                "",
                tx["error"]
            )
        else:
            asset_str = ", ".join([f"{a['name']}: {a['amount']}" for a in tx["assets"]]) if tx["assets"] else "None"
            tx_table.add_row(
                tx["txid"][:10] + "...",
                str(tx["size"]),
                str(tx["vin_count"]),
                str(tx["vout_count"]),
                f"{tx['total_output']:.8f}",
                asset_str
            )
    
    console.print(tx_table)
    console.print()
    
    # Show execution time and benefits of async
    console.print(f"[bold green]Total execution time: {execution_time:.2f} seconds[/]")
    console.print("[italic]Using async/await allowed all these queries to run in parallel![/]")
    console.print("[italic]A synchronous implementation would take significantly longer.[/]")

if __name__ == "__main__":
    asyncio.run(main()) 