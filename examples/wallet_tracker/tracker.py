#!/usr/bin/env python3
"""
Evrmore Wallet Tracker Example (Simplified)

This example demonstrates how to:
1. Track wallet balances, including assets
2. Monitor incoming and outgoing transactions
3. Display transaction history
4. Calculate wallet statistics

Requirements:
    - Evrmore node with RPC enabled
    - evrmore-rpc package installed
"""

import asyncio
import signal
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
import time

from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.traceback import install
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc.zmq.models import ZMQNotification

# Rich console for pretty output
console = Console()

@dataclass
class Transaction:
    """Represents a wallet transaction."""
    txid: str
    type: str  # 'send', 'receive', 'generate'
    amount: Decimal
    fee: Optional[Decimal]
    confirmations: int
    timestamp: datetime
    address: Optional[str]
    category: str
    assets: Dict[str, Decimal]  # Asset name -> amount

@dataclass
class Balance:
    """Represents a wallet balance."""
    total: Decimal
    available: Decimal
    pending: Decimal
    assets: Dict[str, Decimal]  # Asset name -> amount
    last_updated: datetime

# Global state
state = {
    'balance': None,  # Current balance
    'transactions': [],  # List of recent transactions
    'start_time': datetime.now(),
    'tx_count': 0,
    'assets': {},  # Asset name -> {balance, metadata}
    'addresses': [],  # List of wallet addresses
    'last_block': 0,
}

# RPC client
rpc = EvrmoreClient()
# Force sync mode
rpc.force_sync()

def format_amount(amount: Decimal, asset: Optional[str] = None) -> str:
    """Format amount with proper precision."""
    formatted = f"{amount:,.8f}"
    if asset:
        formatted += f" {asset}"
    return formatted

async def get_wallet_balance() -> Balance:
    """Get current wallet balance."""
    # Get EVR balance
    balance_info = rpc.getbalance("*", 0, True)  # Include unconfirmed
    confirmed = rpc.getbalance("*", 1, True)     # Only confirmed
    
    # Get asset balances
    assets = {}
    my_assets = rpc.listmyassets()
    for asset, amount in my_assets.items():
        if isinstance(amount, (int, float, Decimal)):
            assets[asset] = Decimal(str(amount))
        elif isinstance(amount, dict) and 'balance' in amount:
            assets[asset] = Decimal(str(amount['balance']))
    
    # Create balance object
    return Balance(
        total=Decimal(str(balance_info)),
        available=Decimal(str(confirmed)),
        pending=Decimal(str(balance_info)) - Decimal(str(confirmed)),
        assets=assets,
        last_updated=datetime.now(),
    )

async def get_transactions(count: int = 20) -> List[Transaction]:
    """Get recent transactions."""
    tx_list = rpc.listtransactions("*", count)
    transactions = []
    
    for tx in tx_list:
        # Extract asset information
        assets = {}
        if 'asset' in tx and tx['asset']:
            if isinstance(tx['asset'], dict):
                for asset, info in tx['asset'].items():
                    assets[asset] = Decimal(str(info.get('amount', 0)))
        
        # Create transaction object
        transactions.append(Transaction(
            txid=tx['txid'],
            type=tx['category'],
            amount=Decimal(str(tx.get('amount', 0))),
            fee=Decimal(str(tx.get('fee', 0))) if 'fee' in tx else None,
            confirmations=tx.get('confirmations', 0),
            timestamp=datetime.fromtimestamp(tx.get('time', time.time())),
            address=tx.get('address'),
            category=tx.get('category', ''),
            assets=assets,
        ))
    
    return transactions

def create_stats_table() -> Table:
    """Create a table showing wallet statistics."""
    table = Table(title="Wallet Tracker")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate runtime
    runtime = (datetime.now() - state['start_time']).total_seconds()
    
    # Add statistics
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        f"Since {state['start_time'].strftime('%H:%M:%S')}"
    )
    
    # Add balance info
    if state['balance']:
        table.add_row("Balance", "", "")
        table.add_row(
            "  Available EVR",
            format_amount(state['balance'].available),
            f"Pending: {format_amount(state['balance'].pending)}"
        )
        
        # Add asset balances
        if state['balance'].assets:
            table.add_row("Assets", "", "")
            for asset, amount in sorted(state['balance'].assets.items())[:5]:  # Show top 5 assets
                table.add_row(
                    f"  {asset}",
                    format_amount(amount),
                    ""
                )
    
    # Add transaction info
    if state['transactions']:
        table.add_row("Recent Transactions", "", "")
        for tx in state['transactions'][:5]:  # Show last 5 transactions
            if tx.type == 'receive':
                style = "green"
                prefix = "+"
            elif tx.type == 'send':
                style = "red"
                prefix = "-"
            else:
                style = "yellow"
                prefix = ""
                
            amount_str = f"{prefix}{format_amount(abs(tx.amount))}"
            
            # Add asset information
            asset_details = ""
            if tx.assets:
                asset_items = list(tx.assets.items())
                if asset_items:
                    asset_name, asset_amount = asset_items[0]
                    asset_details = f"Asset: {asset_name} ({asset_amount})"
            
            table.add_row(
                f"  {tx.timestamp.strftime('%m-%d %H:%M')}",
                f"[{style}]{amount_str}[/{style}]",
                f"{tx.address if tx.address else ''} {asset_details}"
            )
    
    return table

async def update_state() -> None:
    """Update global state."""
    try:
        # Update balance
        state['balance'] = await get_wallet_balance()
        
        # Update transactions
        state['transactions'] = await get_transactions()
        
        # Update asset information
        if state['balance'] and state['balance'].assets:
            for asset, amount in state['balance'].assets.items():
                if asset not in state['assets']:
                    # Try to get asset data
                    try:
                        asset_data = rpc.getassetdata(asset)
                        state['assets'][asset] = {
                            'balance': amount,
                            'metadata': asset_data,
                            'last_updated': datetime.now(),
                        }
                    except:
                        state['assets'][asset] = {
                            'balance': amount,
                            'metadata': {},
                            'last_updated': datetime.now(),
                        }
                else:
                    state['assets'][asset]['balance'] = amount
                    state['assets'][asset]['last_updated'] = datetime.now()
        
        # Update addresses - try different methods as they vary by wallet version
        try:
            # Try newer wallet method
            state['addresses'] = list(rpc.getaddressesbylabel(""))
        except:
            try:
                # Try older wallet method
                state['addresses'] = rpc.getaddressesbyaccount("")
            except:
                # If both fail, just use an empty list
                state['addresses'] = []
        
    except Exception as e:
        console.print(f"[red]Error updating state: {e}[/red]")

async def tracker() -> None:
    """Main tracking function."""
    # Initialize state
    await update_state()
    
    # Create live display
    with Live(create_stats_table(), refresh_per_second=1) as live:
        while True:
            try:
                # Update state
                await update_state()
                
                # Update display
                live.update(create_stats_table())
                
                # Sleep to avoid excessive polling
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]Error: {e}[/red]")
                await asyncio.sleep(10)  # Wait longer after an error

async def main():
    """Main entry point."""
    try:
        # Enable better exception handling
        install()
        
        # Show welcome message
        console.print(Panel(
            Text.from_markup(
                "[bold cyan]Evrmore Wallet Tracker[/]\n\n"
                "Monitoring wallet activity...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Set up signal handling
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
        # Start tracker
        await tracker()
    
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