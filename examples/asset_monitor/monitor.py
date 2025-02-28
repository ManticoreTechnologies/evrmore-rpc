#!/usr/bin/env python3
"""
Evrmore Asset Monitor Example

This example demonstrates how to:
1. Monitor asset creation and transfers in real-time
2. Track asset statistics and ownership
3. Detect asset reissuance and burns
4. Generate asset activity reports

Requirements:
    - Evrmore node with RPC and ZMQ enabled
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
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

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
}

# RPC client
rpc = EvrmoreRPCClient()

def format_amount(amount: Decimal) -> str:
    """Format amount with proper precision."""
    return f"{amount:,.8f}"

async def process_transaction(tx_data: dict) -> List[AssetActivity]:
    """Process a transaction for asset activities."""
    activities = []
    try:
        # Get transaction details
        tx = await asyncio.to_thread(rpc.getrawtransaction, tx_data['txid'], True)
        timestamp = datetime.fromtimestamp(tx.blocktime if hasattr(tx, 'blocktime') else tx.time)
        
        # Track input addresses and amounts
        input_assets: Dict[str, Dict[str, Decimal]] = {}  # asset -> {address -> amount}
        for vin in tx.vin:
            if hasattr(vin, 'coinbase'):
                continue
            
            try:
                # Get previous transaction
                prev_tx = await asyncio.to_thread(
                    rpc.getrawtransaction,
                    vin.txid,
                    True
                )
                prev_out = prev_tx.vout[vin.vout]
                
                # Check for asset transfer
                if hasattr(prev_out, 'asset'):
                    asset_name = prev_out.asset.name
                    amount = Decimal(str(prev_out.asset.amount))
                    from_address = prev_out.scriptPubKey.addresses[0]
                    
                    if asset_name not in input_assets:
                        input_assets[asset_name] = {}
                    if from_address not in input_assets[asset_name]:
                        input_assets[asset_name][from_address] = Decimal('0')
                    input_assets[asset_name][from_address] += amount
            except Exception as e:
                print(f"Error processing input: {e}")
                continue
        
        # Track output addresses and amounts
        for vout in tx.vout:
            try:
                if not hasattr(vout, 'asset'):
                    continue
                    
                asset_name = vout.asset.name
                amount = Decimal(str(vout.asset.amount))
                to_address = vout.scriptPubKey.addresses[0]
                
                # Determine activity type
                if asset_name not in state['assets']:
                    # New asset issuance
                    activity_type = 'issue'
                    state['issue_count'] += 1
                    state['assets'][asset_name] = {
                        'supply': amount,
                        'holders': {to_address},
                        'reissuable': vout.asset.reissuable,
                        'ipfs_hash': vout.asset.ipfs_hash if hasattr(vout.asset, 'ipfs_hash') else None,
                        'first_seen': timestamp,
                        'last_updated': timestamp,
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
                    state['assets'][asset_name]['supply'] += amount
                    state['assets'][asset_name]['holders'].add(to_address)
                    
                # Record activity
                activities.append(AssetActivity(
                    asset_name=asset_name,
                    activity_type=activity_type,
                    amount=amount,
                    from_address=None if activity_type == 'issue' else from_address,
                    to_address=to_address,
                    txid=tx.txid,
                    timestamp=timestamp
                ))
                
                # Update asset state
                state['assets'][asset_name]['last_updated'] = timestamp
            except Exception as e:
                print(f"Error processing output: {e}")
                continue
    except Exception as e:
        print(f"Error processing transaction: {e}")
    
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
                details = (
                    f"Amount: {format_amount(activity.amount)}, "
                    f"From: {activity.from_address[:8]}..., "
                    f"To: {activity.to_address[:8]}..."
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

async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle new transaction notifications."""
    try:
        # Get transaction details
        tx_data = {'txid': notification.hex}  # Pass txid to process_transaction
        
        # Process transaction
        activities = await process_transaction(tx_data)
        if activities:
            state['tx_count'] += 1
            
            # Update state
            state['activities'].extend(activities)
            if len(state['activities']) > 100:
                state['activities'] = state['activities'][-100:]
    except Exception as e:
        print(f"Error handling transaction: {e}")

async def monitor() -> None:
    """Main monitoring function."""
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient()
    
    # Register handlers
    zmq_client.on(ZMQTopic.HASH_TX)(handle_transaction)
    
    # Start ZMQ client
    zmq_task = asyncio.create_task(zmq_client.start())
    
    # Create live display
    with Live(create_stats_table(), refresh_per_second=4) as live:
        def update_display():
            live.update(create_stats_table())
        
        # Update display periodically
        while True:
            try:
                update_display()
                await asyncio.sleep(0.25)
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]Error:[/] {e}")
                break
    
    # Cleanup
    await zmq_client.stop()
    if not zmq_task.done():
        zmq_task.cancel()
        try:
            await zmq_task
        except asyncio.CancelledError:
            pass

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
        
        # Initialize state with current asset list
        try:
            assets = await asyncio.to_thread(rpc.listassets, "*", True)
            for name, info in assets.items():
                state['assets'][name] = {
                    'supply': info.amount,
                    'holders': set(),  # We'll populate this as we see transfers
                    'reissuable': info.reissuable,
                    'ipfs_hash': info.ipfs_hash if hasattr(info, 'ipfs_hash') else None,
                    'first_seen': datetime.now(),  # Approximate
                    'last_updated': datetime.now(),
                }
        except Exception as e:
            print(f"Error initializing asset list: {e}")
        
        # Start the monitor
        await monitor()
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.from_markup("[bold yellow]Shutting down...[/]"),
            title="Stopping"
        ))
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")

if __name__ == "__main__":
    asyncio.run(main()) 