#!/usr/bin/env python3
"""
Evrmore Reward Distributor Example

This example demonstrates how to:
1. Take snapshots of asset holders
2. Calculate reward distributions
3. Distribute rewards to asset holders
4. Track distribution status and history

Requirements:
    - Evrmore node with RPC and ZMQ enabled
    - evrmore-rpc package installed
"""

import asyncio
import signal
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress, SpinnerColumn, TextColumn
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

# Rich console for pretty output
console = Console()

@dataclass
class Snapshot:
    """Asset holder snapshot."""
    asset_name: str
    block_height: int
    holders: Dict[str, Decimal]  # Address -> balance
    total_supply: Decimal
    timestamp: datetime

@dataclass
class Distribution:
    """Reward distribution."""
    snapshot: Snapshot
    reward_asset: str
    reward_amount: Decimal
    reward_per_token: Decimal
    status: str  # 'pending', 'in_progress', 'completed', 'failed'
    txids: List[str]
    distributed: Decimal
    remaining: Decimal
    timestamp: datetime

# Global state
state = {
    'snapshots': [],  # List of snapshots
    'distributions': [],  # List of distributions
    'start_time': datetime.now(),
    'snapshot_count': 0,
    'distribution_count': 0,
}

# RPC client
rpc = EvrmoreRPCClient()

def format_amount(amount: Decimal, asset: Optional[str] = None) -> str:
    """Format amount with proper precision."""
    if asset:
        return f"{amount:,.8f} {asset}"
    return f"{amount:,.8f}"

async def take_snapshot(asset_name: str, block_height: Optional[int] = None) -> Snapshot:
    """Take a snapshot of asset holders at a given block height."""
    try:
        # Get current block height and validate input
        info = await asyncio.to_thread(rpc.getblockchaininfo)
        current_height = info.blocks
        
        if block_height is None:
            # Use current height for the snapshot
            block_height = current_height
        elif block_height > current_height:
            raise ValueError(f"Block height {block_height} is not valid. Current height: {current_height}")
        elif block_height < 0:
            raise ValueError("Block height cannot be negative")
        
        # Verify asset exists
        try:
            asset_info = await asyncio.to_thread(rpc.getassetdata, asset_name)
            if not asset_info:
                raise ValueError(f"Asset {asset_name} does not exist")
        except Exception as e:
            raise ValueError(f"Failed to verify asset {asset_name}: {e}")
        
        # Request snapshot
        try:
            await asyncio.to_thread(
                rpc.requestsnapshot,
                asset_name,
                block_height
            )
        except Exception as e:
            raise ValueError(f"Failed to request snapshot: {e}")
        
        # Wait for snapshot to complete
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                f"Taking snapshot of {asset_name} at block {block_height}...",
                total=None
            )
            
            while True:
                try:
                    snapshot_info = await asyncio.to_thread(
                        rpc.getsnapshotrequest,
                        asset_name,
                        block_height
                    )
                    
                    if snapshot_info.status == 'complete':
                        break
                    elif snapshot_info.status == 'failed':
                        error_msg = getattr(snapshot_info, 'error', 'Unknown error')
                        raise ValueError(f"Snapshot failed: {error_msg}")
                except Exception as e:
                    raise ValueError(f"Failed to check snapshot status: {e}")
                    
                await asyncio.sleep(1)
        
        # Get snapshot data
        holders = {}
        total_supply = Decimal('0')
        
        try:
            # Get actual snapshot data from node
            balances = await asyncio.to_thread(
                rpc.listassetbalancesbyaddress,
                asset_name
            )
            
            for addr, balance in balances.items():
                amount = Decimal(str(balance))
                if amount > 0:  # Only include non-zero balances
                    holders[addr] = amount
                    total_supply += amount
                    
            if not holders:
                raise ValueError(f"No holders found for asset {asset_name}")
                
        except Exception as e:
            raise ValueError(f"Failed to get asset balances: {e}")
        
        return Snapshot(
            asset_name=asset_name,
            block_height=block_height,
            holders=holders,
            total_supply=total_supply,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise ValueError(f"Failed to take snapshot: {str(e)}")

async def distribute_rewards(
    snapshot: Snapshot,
    reward_asset: str,
    reward_amount: Decimal,
    batch_size: int = 100
) -> Distribution:
    """Distribute rewards to asset holders."""
    try:
        # Validate reward asset exists
        try:
            reward_info = await asyncio.to_thread(rpc.getassetdata, reward_asset)
            if not reward_info:
                raise ValueError(f"Reward asset {reward_asset} does not exist")
        except Exception as e:
            raise ValueError(f"Failed to verify reward asset {reward_asset}: {e}")
        
        # Verify we have enough balance
        try:
            balances = await asyncio.to_thread(rpc.listmyassets)
            available_balance = Decimal(str(balances.get(reward_asset, 0)))
            if available_balance < reward_amount:
                raise ValueError(
                    f"Insufficient balance of {reward_asset}. "
                    f"Required: {reward_amount}, Available: {available_balance}"
                )
        except Exception as e:
            raise ValueError(f"Failed to check reward asset balance: {e}")
        
        # Calculate reward per token
        reward_per_token = reward_amount / snapshot.total_supply
        
        # Create distribution
        distribution = Distribution(
            snapshot=snapshot,
            reward_asset=reward_asset,
            reward_amount=reward_amount,
            reward_per_token=reward_per_token,
            status='in_progress',
            txids=[],
            distributed=Decimal('0'),
            remaining=reward_amount,
            timestamp=datetime.now()
        )
        
        # Group holders into batches
        holders = list(snapshot.holders.items())
        batches = [
            holders[i:i + batch_size]
            for i in range(0, len(holders), batch_size)
        ]
        
        # Process each batch
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                "Distributing rewards...",
                total=len(batches)
            )
            
            for batch in batches:
                try:
                    # Create distribution transaction
                    outputs = {}
                    batch_total = Decimal('0')
                    
                    for address, balance in batch:
                        reward = balance * reward_per_token
                        if reward > 0:
                            outputs[address] = {
                                reward_asset: float(reward)
                            }
                            batch_total += reward
                    
                    if outputs:
                        try:
                            # Send rewards
                            txid = await asyncio.to_thread(
                                rpc.sendmany,
                                "",  # From default account
                                outputs
                            )
                            
                            # Update distribution status
                            distribution.txids.append(txid)
                            distribution.distributed += batch_total
                            distribution.remaining = reward_amount - distribution.distributed
                            
                        except Exception as e:
                            raise ValueError(f"Failed to send rewards: {e}")
                            
                except Exception as e:
                    distribution.status = 'failed'
                    raise ValueError(f"Failed to process batch: {e}")
                
                progress.advance(task)
        
        distribution.status = 'completed'
        return distribution
        
    except Exception as e:
        raise ValueError(f"Failed to distribute rewards: {str(e)}")

def create_stats_table() -> Table:
    """Create a table showing distribution statistics."""
    table = Table(title="Reward Distributor")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate rates
    runtime = (datetime.now() - state['start_time']).total_seconds()
    snapshot_rate = state['snapshot_count'] / runtime if runtime > 0 else 0
    distribution_rate = state['distribution_count'] / runtime if runtime > 0 else 0
    
    # Add statistics
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        f"Since {state['start_time'].strftime('%H:%M:%S')}"
    )
    table.add_row(
        "Snapshots",
        str(state['snapshot_count']),
        f"Rate: {snapshot_rate:.2f}/s"
    )
    table.add_row(
        "Distributions",
        str(state['distribution_count']),
        f"Rate: {distribution_rate:.2f}/s"
    )
    
    # Add recent snapshots
    if state['snapshots']:
        table.add_row("Recent Snapshots", "", "")
        for snapshot in reversed(state['snapshots'][-5:]):
            table.add_row(
                snapshot.asset_name,
                f"Block {snapshot.block_height}",
                f"Holders: {len(snapshot.holders)}, "
                f"Supply: {format_amount(snapshot.total_supply)}"
            )
    
    # Add recent distributions
    if state['distributions']:
        table.add_row("Recent Distributions", "", "")
        for dist in reversed(state['distributions'][-5:]):
            table.add_row(
                dist.snapshot.asset_name,
                dist.status.title(),
                f"Reward: {format_amount(dist.reward_amount, dist.reward_asset)}, "
                f"Per token: {format_amount(dist.reward_per_token)}"
            )
    
    return table

async def interactive_distributor():
    """Interactive reward distribution interface."""
    while True:
        console.clear()
        console.print(create_stats_table())
        
        console.print("\n[bold cyan]Available Actions:[/]")
        console.print("1. Take snapshot")
        console.print("2. Distribute rewards")
        console.print("3. View snapshots")
        console.print("4. View distributions")
        console.print("5. Exit")
        
        choice = Prompt.ask(
            "\nSelect action",
            choices=['1', '2', '3', '4', '5'],
            default='5'
        )
        
        if choice == '1':
            # Take snapshot
            asset_name = Prompt.ask("Enter asset name")
            block_height_str = Prompt.ask(
                "Enter block height (leave empty for current)",
                default=""
            )
            
            try:
                block_height = int(block_height_str) if block_height_str else None
                snapshot = await take_snapshot(asset_name, block_height)
                state['snapshots'].append(snapshot)
                state['snapshot_count'] += 1
                console.print("[green]Snapshot completed successfully![/]")
                console.print(f"Total holders: {len(snapshot.holders)}")
                console.print(f"Total supply: {format_amount(snapshot.total_supply)}")
            except ValueError as e:
                console.print(f"[red]Error taking snapshot:[/] {e}")
            except Exception as e:
                console.print(f"[red]Unexpected error:[/] {e}")
            
        elif choice == '2':
            # Distribute rewards
            if not state['snapshots']:
                console.print("[yellow]No snapshots available![/]")
                continue
            
            # List available snapshots
            console.print("\n[bold cyan]Available Snapshots:[/]")
            for i, snapshot in enumerate(state['snapshots']):
                console.print(
                    f"{i + 1}. {snapshot.asset_name} "
                    f"at block {snapshot.block_height} "
                    f"({len(snapshot.holders)} holders)"
                )
            
            try:
                snapshot_idx = int(Prompt.ask(
                    "Select snapshot",
                    choices=[str(i + 1) for i in range(len(state['snapshots']))],
                    default='1'
                )) - 1
                
                snapshot = state['snapshots'][snapshot_idx]
                reward_asset = Prompt.ask("Enter reward asset name")
                reward_amount = Decimal(Prompt.ask("Enter total reward amount"))
                
                distribution = await distribute_rewards(
                    snapshot,
                    reward_asset,
                    reward_amount
                )
                state['distributions'].append(distribution)
                state['distribution_count'] += 1
                console.print("[green]Distribution completed successfully![/]")
            except ValueError as e:
                console.print(f"[red]Error distributing rewards:[/] {e}")
            except Exception as e:
                console.print(f"[red]Unexpected error:[/] {e}")
            
        elif choice == '3':
            # View snapshots
            if not state['snapshots']:
                console.print("[yellow]No snapshots available![/]")
            else:
                table = Table(title="Snapshots")
                table.add_column("Asset")
                table.add_column("Block")
                table.add_column("Holders")
                table.add_column("Supply")
                table.add_column("Time")
                
                for snapshot in state['snapshots']:
                    table.add_row(
                        snapshot.asset_name,
                        str(snapshot.block_height),
                        str(len(snapshot.holders)),
                        format_amount(snapshot.total_supply),
                        snapshot.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    )
                
                console.print(table)
            
        elif choice == '4':
            # View distributions
            if not state['distributions']:
                console.print("[yellow]No distributions available![/]")
            else:
                table = Table(title="Distributions")
                table.add_column("Asset")
                table.add_column("Status")
                table.add_column("Reward")
                table.add_column("Progress")
                table.add_column("Time")
                
                for dist in state['distributions']:
                    progress = (
                        f"{format_amount(dist.distributed)} / "
                        f"{format_amount(dist.reward_amount)} "
                        f"{dist.reward_asset}"
                    )
                    
                    table.add_row(
                        dist.snapshot.asset_name,
                        dist.status.title(),
                        format_amount(dist.reward_amount, dist.reward_asset),
                        progress,
                        dist.timestamp.strftime('%Y-%m-%d %H:%M:%S')
                    )
                
                console.print(table)
            
        elif choice == '5':
            break
            
        input("\nPress Enter to continue...")

async def main():
    """Main entry point."""
    try:
        # Show welcome message
        console.print(Panel(
            Text.from_markup(
                "[bold cyan]Evrmore Reward Distributor[/]\n\n"
                "Interactive tool for managing asset rewards.\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Start the interactive interface
        await interactive_distributor()
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.from_markup("[bold yellow]Shutting down...[/]"),
            title="Stopping"
        ))
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")

if __name__ == "__main__":
    asyncio.run(main()) 