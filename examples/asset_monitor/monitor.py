#!/usr/bin/env python3
"""
Evrmore Asset Monitor Example (Simplified)

This example demonstrates how to:
1. Monitor asset creation and transfers
2. Track asset statistics and ownership
3. Detect asset issuance and transfers
4. Generate asset activity reports

Requirements:
    - Evrmore node with RPC enabled
    - evrmore-rpc package installed
"""

import asyncio
import signal
from datetime import datetime
from decimal import Decimal
from typing import Dict, Set, List, Optional
from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc.zmq.models import ZMQNotification

# Rich console for pretty output
console = Console()

@dataclass
class AssetActivity:
    """Represents an asset activity event."""
    asset_name: str
    activity_type: str  # 'issue', 'transfer', 'reissue', 'burn'
    amount: Decimal
    from_address: Optional[str]
    to_address: Optional[str]
    txid: str
    timestamp: datetime

# Global state
state = {
    'assets': {},  # Asset name -> {supply, holders, reissuable, etc.}
    'activities': [],  # List of recent asset activities
    'start_time': datetime.now(),
    'issue_count': 0,
    'transfer_count': 0,
    'reissue_count': 0,
    'burn_count': 0,
    'last_block': 0,
}

# RPC client
rpc = EvrmoreClient()
# Force sync mode
rpc.force_sync()

def format_amount(amount: Decimal) -> str:
    """Format amount with proper precision."""
    return f"{amount:,.8f}"

async def process_block(block_hash: str) -> List[AssetActivity]:
    """Process a block for asset activities."""
    activities = []
    try:
        # Get block data
        block = rpc.getblock(block_hash, 2)  # Verbose level 2 for full tx data
        block_time = datetime.fromtimestamp(block['time'])
        
        # Process each transaction
        for tx in block['tx']:
            # Track input addresses and amounts
            input_assets = {}  # asset -> {address -> amount}
            for vin in tx['vin']:
                if 'coinbase' in vin:
                    continue
                
                try:
                    # Get previous transaction
                    prev_tx = rpc.getrawtransaction(vin['txid'], True)
                    prev_out = prev_tx['vout'][vin['vout']]
                    
                    # Check for asset transfer
                    if 'asset' in prev_out.get('scriptPubKey', {}):
                        asset_info = prev_out['scriptPubKey']['asset']
                        asset_name = asset_info['name']
                        amount = Decimal(str(asset_info['amount']))
                        if 'addresses' in prev_out['scriptPubKey'] and prev_out['scriptPubKey']['addresses']:
                            from_address = prev_out['scriptPubKey']['addresses'][0]
                        else:
                            from_address = "unknown"
                        
                        if asset_name not in input_assets:
                            input_assets[asset_name] = {}
                        if from_address not in input_assets[asset_name]:
                            input_assets[asset_name][from_address] = Decimal('0')
                        input_assets[asset_name][from_address] += amount
                except Exception as e:
                    console.print(f"[red]Error processing input: {e}[/red]")
                    continue
            
            # Track output addresses and amounts
            for vout in tx['vout']:
                try:
                    if 'asset' not in vout.get('scriptPubKey', {}):
                        continue
                        
                    asset_info = vout['scriptPubKey']['asset']
                    asset_name = asset_info['name']
                    amount = Decimal(str(asset_info['amount']))
                    
                    if 'addresses' in vout['scriptPubKey'] and vout['scriptPubKey']['addresses']:
                        to_address = vout['scriptPubKey']['addresses'][0]
                    else:
                        to_address = "unknown"
                    
                    # Determine activity type
                    if asset_name not in state['assets']:
                        # New asset issuance
                        activity_type = 'issue'
                        state['issue_count'] += 1
                        from_address = None
                        state['assets'][asset_name] = {
                            'supply': amount,
                            'holders': {to_address},
                            'reissuable': asset_info.get('reissuable', False),
                            'ipfs_hash': asset_info.get('ipfs_hash'),
                            'first_seen': block_time,
                            'last_updated': block_time,
                        }
                    elif asset_name in input_assets:
                        # Asset transfer
                        activity_type = 'transfer'
                        state['transfer_count'] += 1
                        from_address = next(iter(input_assets[asset_name].keys()))
                        state['assets'][asset_name]['holders'].add(to_address)
                        if from_address in state['assets'][asset_name]['holders']:
                            input_amount = input_assets[asset_name][from_address]
                            if input_amount <= amount:
                                state['assets'][asset_name]['holders'].remove(from_address)
                    else:
                        # Asset reissuance
                        activity_type = 'reissue'
                        state['reissue_count'] += 1
                        from_address = None
                        state['assets'][asset_name]['supply'] += amount
                        state['assets'][asset_name]['holders'].add(to_address)
                        
                    # Record activity
                    activities.append(AssetActivity(
                        asset_name=asset_name,
                        activity_type=activity_type,
                        amount=amount,
                        from_address=from_address,
                        to_address=to_address,
                        txid=tx['txid'],
                        timestamp=block_time
                    ))
                    
                    # Update asset state
                    state['assets'][asset_name]['last_updated'] = block_time
                except Exception as e:
                    console.print(f"[red]Error processing output: {e}[/red]")
                    continue
    except Exception as e:
        console.print(f"[red]Error processing block: {e}[/red]")
    
    return activities

def create_stats_table() -> Table:
    """Create a table showing current asset statistics."""
    table = Table(title="Asset Monitor")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate rates
    runtime = (datetime.now() - state['start_time']).total_seconds()
    issue_rate = state['issue_count'] / runtime if runtime > 0 else 0
    transfer_rate = state['transfer_count'] / runtime if runtime > 0 else 0
    
    # Add statistics
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        f"Since {state['start_time'].strftime('%H:%M:%S')}"
    )
    table.add_row(
        "Last Block",
        str(state['last_block']),
        ""
    )
    table.add_row(
        "Total Assets",
        str(len(state['assets'])),
        f"Issue rate: {issue_rate:.2f}/s"
    )
    table.add_row(
        "Activities",
        str(len(state['activities'])),
        f"Transfer rate: {transfer_rate:.2f}/s"
    )
    
    # Add recent activities
    if state['activities']:
        table.add_row("Recent Activities", "", "")
        for activity in reversed(state['activities'][-5:]):
            if activity.activity_type == 'issue':
                details = f"Initial supply: {format_amount(activity.amount)}"
            elif activity.activity_type == 'transfer':
                from_addr = activity.from_address[:8] + "..." if activity.from_address else "N/A"
                to_addr = activity.to_address[:8] + "..." if activity.to_address else "N/A"
                details = (
                    f"Amount: {format_amount(activity.amount)}, "
                    f"From: {from_addr}, "
                    f"To: {to_addr}"
                )
            else:
                details = f"New supply: {format_amount(activity.amount)}"
                
            table.add_row(
                activity.asset_name,
                activity.activity_type.title(),
                details
            )
    
    # Add top assets by holder count
    top_assets = sorted(
        state['assets'].items(),
        key=lambda x: len(x[1]['holders']),
        reverse=True
    )[:5]
    
    if top_assets:
        table.add_row("Top Assets by Holders", "", "")
        for name, info in top_assets:
            table.add_row(
                name,
                str(len(info['holders'])),
                f"Supply: {format_amount(info['supply'])}"
            )
    
    return table

async def monitor() -> None:
    """Main monitoring function."""
    # Get initial blockchain info
    chain_info = rpc.getblockchaininfo()
    state['last_block'] = chain_info['blocks']
    
    # Start monitoring
    with Live(create_stats_table(), refresh_per_second=4) as live:
        while True:
            try:
                # Check for new blocks
                current_height = rpc.getblockcount()
                
                if current_height > state['last_block']:
                    console.print(f"[green]New block detected: {current_height}[/green]")
                    
                    # Process new blocks
                    for height in range(state['last_block'] + 1, current_height + 1):
                        block_hash = rpc.getblockhash(height)
                        activities = await process_block(block_hash)
                        
                        # Update state
                        state['activities'].extend(activities)
                        if len(state['activities']) > 100:
                            state['activities'] = state['activities'][-100:]
                        
                        state['last_block'] = height
                
                # Update display
                live.update(create_stats_table())
                
                # Sleep to avoid excessive polling
                await asyncio.sleep(2)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(5)  # Wait longer after an error

async def main():
    """Main entry point."""
    try:
        # Show welcome message
        console.print(Panel(
            Text.from_markup(
                "[bold cyan]Evrmore Asset Monitor[/]\n\n"
                "Monitoring asset activity in real-time...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Set up signal handling
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
            
        # Start monitoring
        await monitor()
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
    finally:
        console.print("[yellow]Shutting down...[/yellow]")

async def shutdown():
    """Handle graceful shutdown."""
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    asyncio.run(main()) 