import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient
from evrmore_rpc.client import EvrmoreRPCError
from rich.console import Console

console = Console()

async def get_blockchain_info():
    """Get and display blockchain info."""
    async with EvrmoreAsyncRPCClient() as client:
        info = await client.getblockchaininfo()
        console.print("[bold green]Blockchain Info[/]")
        console.print(f"Current block height: {info.blocks}")
        console.print(f"Chain: {info.chain}")
        console.print(f"Difficulty: {info.difficulty}\n")
        return info

async def get_block_info(height=1):
    """Get and display block info for a specific height."""
    async with EvrmoreAsyncRPCClient() as client:
        block_hash = await client.getblockhash(height)
        block = await client.getblock(block_hash)
        console.print(f"[bold green]Block #{height}[/]")
        console.print(f"Hash: {block.hash}")
        console.print(f"Time: {block.time}")
        console.print(f"Transactions: {len(block.tx)}\n")
        return block

async def get_asset_info():
    """Get and display asset information."""
    async with EvrmoreAsyncRPCClient() as client:
        console.print("[bold]Listing assets...[/]")
        assets = await client.listassets()
        if assets:
            console.print(f"Found {len(assets)} assets:")
            asset_list = list(assets)[:5]  # Show first 5 assets
            
            # Use gather to fetch asset data in parallel
            asset_data_tasks = [client.getassetdata(asset) for asset in asset_list]
            asset_data_results = await asyncio.gather(*asset_data_tasks, return_exceptions=True)
            
            for i, asset in enumerate(asset_list):
                data = asset_data_results[i]
                if isinstance(data, Exception):
                    console.print(f"\n[bold]{asset}[/]")
                    console.print(f"[yellow]Warning:[/] Could not get data: {data}")
                else:
                    console.print(f"\n[bold]{asset}[/]")
                    console.print(f"Amount: {data.amount}")
                    console.print(f"Units: {data.units}")
                    console.print(f"Reissuable: {data.reissuable}")
                    console.print(f"Has IPFS: {data.has_ipfs}")
        else:
            console.print("[yellow]No assets found[/]")

async def get_my_assets():
    """Get and display my owned assets."""
    async with EvrmoreAsyncRPCClient() as client:
        console.print("\n[bold]Listing my assets...[/]")
        try:
            my_assets = await client.listmyassets()
            if my_assets:
                console.print(f"Found {len(my_assets)} owned assets:")
                for name, balance in list(my_assets.items())[:5]:
                    console.print(f"\n[bold]{name}[/]")
                    console.print(f"Balance: {balance}")
            else:
                console.print("[yellow]No owned assets found[/]")
        except EvrmoreRPCError as e:
            console.print(f"[red]Error listing my assets:[/] {e}")

async def main():
    """Run all examples concurrently."""
    try:
        # Run the first two tasks concurrently
        blockchain_info, block_info = await asyncio.gather(
            get_blockchain_info(),
            get_block_info()
        )
        
        # Run asset information tasks
        await get_asset_info()
        await get_my_assets()
        
    except EvrmoreRPCError as e:
        console.print(f"[red]Error:[/] {e}")
    except Exception as e:
        console.print(f"[red]Unexpected error:[/] {e}")

if __name__ == "__main__":
    asyncio.run(main()) 