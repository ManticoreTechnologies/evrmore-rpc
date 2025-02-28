#!/usr/bin/env python3
"""
Evrmore Wallet Tracker Example

This example demonstrates how to:
1. Monitor wallet balances and transactions in real-time
2. Track asset holdings and transfers
3. Calculate profit/loss for trades
4. Generate transaction reports

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
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

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
    'balance': None,  # Current wallet balance
    'transactions': [],  # Recent transactions
    'addresses': set(),  # Known addresses
    'start_time': datetime.now(),
    'tx_count': 0,
    'asset_tx_count': 0,
}

# RPC client
rpc = EvrmoreRPCClient()

def format_amount(amount: Decimal, asset: Optional[str] = None) -> str:
    """Format amount with proper precision."""
    if asset:
        return f"{amount:,.8f} {asset}"
    return f"{amount:,.8f} EVR"

async def get_wallet_balance() -> Balance:
    """Get current wallet balance."""
    # Get EVR balance
    balance = await asyncio.to_thread(rpc.getbalance, "*", 0)
    unconfirmed = await asyncio.to_thread(rpc.getunconfirmedbalance)
    
    # Get asset balances
    assets = {}
    my_assets = await asyncio.to_thread(rpc.listmyassets)
    my_assets_dict = dict(my_assets)  # Convert to dictionary
    for name, amount in my_assets_dict.items():
        if name != "":  # Skip owner tokens
            assets[name] = Decimal(str(amount))
    
    return Balance(
        total=Decimal(str(balance)) + Decimal(str(unconfirmed)),
        available=Decimal(str(balance)),
        pending=Decimal(str(unconfirmed)),
        assets=assets,
        last_updated=datetime.now()
    )

async def process_transaction(tx_data: dict) -> Optional[Transaction]:
    """Process a transaction for wallet activity."""
    try:
        tx_dict = dict(tx_data)  # Convert to dictionary
        
        # Skip if not related to our wallet
        our_tx = False
        our_addresses = await asyncio.to_thread(rpc.getaddressesbyaccount, "")
        
        for vin in tx_dict.get('vin', []):
            if 'coinbase' in vin:
                continue
            try:
                prev_tx = await asyncio.to_thread(
                    rpc.getrawtransaction,
                    vin.get('txid', ''),
                    True
                )
                prev_tx_dict = dict(prev_tx)  # Convert to dictionary
                prev_out = prev_tx_dict['vout'][vin.get('vout', 0)]
                for addr in prev_out.get('scriptPubKey', {}).get('addresses', []):
                    if addr in our_addresses:
                        our_tx = True
                        break
            except Exception as e:
                print(f"Error processing input: {e}")
                continue
        
        if not our_tx:
            for vout in tx_dict.get('vout', []):
                for addr in vout.get('scriptPubKey', {}).get('addresses', []):
                    if addr in our_addresses:
                        our_tx = True
                        break
        
        if not our_tx:
            return None
        
        # Calculate transaction details
        timestamp = datetime.fromtimestamp(tx_dict.get('time', 0))
        tx_type = 'generate' if any('coinbase' in vin for vin in tx_dict.get('vin', [])) else 'unknown'
        amount = Decimal('0')
        fee = None
        address = None
        assets = {}
        
        # Calculate amount and determine type
        our_inputs = Decimal('0')
        our_outputs = Decimal('0')
        
        for vin in tx_dict.get('vin', []):
            if 'coinbase' in vin:
                continue
            try:
                prev_tx = await asyncio.to_thread(
                    rpc.getrawtransaction,
                    vin.get('txid', ''),
                    True
                )
                prev_tx_dict = dict(prev_tx)  # Convert to dictionary
                prev_out = prev_tx_dict['vout'][vin.get('vout', 0)]
                if any(addr in our_addresses for addr in prev_out.get('scriptPubKey', {}).get('addresses', [])):
                    our_inputs += Decimal(str(prev_out.get('value', 0)))
            except Exception as e:
                print(f"Error calculating input amount: {e}")
                continue
        
        for vout in tx_dict.get('vout', []):
            try:
                if any(addr in our_addresses for addr in vout.get('scriptPubKey', {}).get('addresses', [])):
                    our_outputs += Decimal(str(vout.get('value', 0)))
                    if 'asset' in vout:
                        asset_data = vout['asset']
                        asset_name = asset_data.get('name', '')
                        asset_amount = Decimal(str(asset_data.get('amount', 0)))
                        if asset_name not in assets:
                            assets[asset_name] = Decimal('0')
                        assets[asset_name] += asset_amount
            except Exception as e:
                print(f"Error calculating output amount: {e}")
                continue
        
        # Determine transaction type and amount
        if our_inputs > 0:
            if our_outputs > 0:
                # Moving funds between our addresses
                tx_type = 'move'
                amount = our_outputs
                fee = our_inputs - our_outputs
            else:
                # Sending to someone else
                tx_type = 'send'
                amount = -our_inputs
                fee = our_inputs - sum(Decimal(str(o.get('value', 0))) for o in tx_dict.get('vout', []))
        else:
            # Receiving from someone else
            tx_type = 'receive'
            amount = our_outputs
        
        # Get recipient address for sends
        if tx_type == 'send':
            for vout in tx_dict.get('vout', []):
                addrs = vout.get('scriptPubKey', {}).get('addresses', [])
                if addrs and addrs[0] not in our_addresses:
                    address = addrs[0]
                    break
        
        return Transaction(
            txid=tx_dict.get('txid', ''),
            type=tx_type,
            amount=amount,
            fee=fee,
            confirmations=tx_dict.get('confirmations', 0),
            timestamp=timestamp,
            address=address,
            category=tx_type,
            assets=assets
        )
    except Exception as e:
        print(f"Error processing transaction: {e}")
    tx_dict = dict(tx_data)  # Convert to dictionary
    
    # Skip if not related to our wallet
    our_tx = False
    our_addresses = await asyncio.to_thread(rpc.getaddressesbyaccount, "")
    
    for vin in tx_dict.get('vin', []):
        if 'coinbase' in vin:
            continue
        prev_tx = await asyncio.to_thread(
            rpc.getrawtransaction,
            vin['txid'],
            True
        )
        prev_tx_dict = dict(prev_tx)  # Convert to dictionary
        prev_out = prev_tx_dict['vout'][vin['vout']]
        for addr in prev_out['scriptPubKey'].get('addresses', []):
            if addr in our_addresses:
                our_tx = True
                break
    
    if not our_tx:
        for vout in tx_dict.get('vout', []):
            for addr in vout['scriptPubKey'].get('addresses', []):
                if addr in our_addresses:
                    our_tx = True
                    break
    
    if not our_tx:
        return None
    
    # Calculate transaction details
    timestamp = datetime.fromtimestamp(tx_dict.get('time', 0))
    tx_type = 'generate' if any('coinbase' in vin for vin in tx_dict.get('vin', [])) else 'unknown'
    amount = Decimal('0')
    fee = None
    address = None
    assets = {}
    
    # Calculate amount and determine type
    our_inputs = Decimal('0')
    our_outputs = Decimal('0')
    
    for vin in tx_dict.get('vin', []):
        if 'coinbase' in vin:
            continue
        prev_tx = await asyncio.to_thread(
            rpc.getrawtransaction,
            vin['txid'],
            True
        )
        prev_tx_dict = dict(prev_tx)  # Convert to dictionary
        prev_out = prev_tx_dict['vout'][vin['vout']]
        if any(addr in our_addresses for addr in prev_out['scriptPubKey'].get('addresses', [])):
            our_inputs += Decimal(str(prev_out['value']))
    
    for vout in tx_dict.get('vout', []):
        if any(addr in our_addresses for addr in vout['scriptPubKey'].get('addresses', [])):
            our_outputs += Decimal(str(vout['value']))
            if 'asset' in vout:
                asset_data = vout['asset']
                asset_name = asset_data['name']
                asset_amount = Decimal(str(asset_data['amount']))
                if asset_name not in assets:
                    assets[asset_name] = Decimal('0')
                assets[asset_name] += asset_amount
    
    # Determine transaction type and amount
    if our_inputs > 0:
        if our_outputs > 0:
            # Moving funds between our addresses
            tx_type = 'move'
            amount = our_outputs
            fee = our_inputs - our_outputs
        else:
            # Sending to someone else
            tx_type = 'send'
            amount = -our_inputs
            fee = our_inputs - sum(Decimal(str(o['value'])) for o in tx_dict.get('vout', []))
    else:
        # Receiving from someone else
        tx_type = 'receive'
        amount = our_outputs
    
    # Get recipient address for sends
    if tx_type == 'send':
        for vout in tx_dict.get('vout', []):
            addrs = vout['scriptPubKey'].get('addresses', [])
            if addrs and addrs[0] not in our_addresses:
                address = addrs[0]
                break
    
    return Transaction(
        txid=tx_dict.get('txid', ''),
        type=tx_type,
        amount=amount,
        fee=fee,
        confirmations=tx_dict.get('confirmations', 0),
        timestamp=timestamp,
        address=address,
        category=tx_type,
        assets=assets
    )

def create_stats_table() -> Table:
    """Create a table showing current wallet statistics."""
    table = Table(title="Wallet Tracker")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate rates
    runtime = (datetime.now() - state['start_time']).total_seconds()
    tx_rate = state['tx_count'] / runtime if runtime > 0 else 0
    
    # Add statistics
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        f"Since {state['start_time'].strftime('%H:%M:%S')}"
    )
    
    # Add balance info
    if state['balance']:
        table.add_row(
            "EVR Balance",
            format_amount(state['balance'].available),
            f"Pending: {format_amount(state['balance'].pending)}"
        )
        
        if state['balance'].assets:
            table.add_row("Asset Balances", "", "")
            for name, amount in state['balance'].assets.items():
                table.add_row("", name, format_amount(amount))
    
    # Add transaction stats
    table.add_row(
        "Transactions",
        str(state['tx_count']),
        f"Rate: {tx_rate:.2f} tx/s"
    )
    
    # Add recent transactions
    if state['transactions']:
        table.add_row("Recent Transactions", "", "")
        for tx in reversed(state['transactions'][-5:]):
            if tx.assets:
                details = ", ".join(
                    f"{format_amount(amount, name)}"
                    for name, amount in tx.assets.items()
                )
            else:
                details = format_amount(tx.amount)
                if tx.fee:
                    details += f", Fee: {format_amount(tx.fee)}"
            
            if tx.address:
                details += f", {tx.address[:8]}..."
                
            table.add_row(
                tx.txid[:8] + "...",
                tx.type.title(),
                details
            )
    
    return table

async def update_balance():
    """Update wallet balance."""
    try:
        state['balance'] = await get_wallet_balance()
    except Exception as e:
        print(f"Error updating balance: {e}")
        state['balance'] = Balance(
            total=Decimal('0'),
            available=Decimal('0'),
            pending=Decimal('0'),
            assets={},
            last_updated=datetime.now()
        )

async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle new transaction notifications."""
    try:
        # Get transaction details
        tx_data = await asyncio.to_thread(
            rpc.getrawtransaction,
            notification.hex,
            True
        )
        
        # Process transaction
        tx = await process_transaction(tx_data)
        if tx:
            state['tx_count'] += 1
            if tx.assets:
                state['asset_tx_count'] += 1
            
            # Update state
            state['transactions'].append(tx)
            if len(state['transactions']) > 100:
                state['transactions'] = state['transactions'][-100:]
                
            # Update balance after a short delay
            try:
                await asyncio.sleep(1)  # Wait for transaction to be processed
                await update_balance()
            except Exception as e:
                print(f"Error updating balance: {e}")
    except Exception as e:
        print(f"Error handling transaction: {e}")

async def tracker() -> None:
    """Main tracking function."""
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
                "[bold cyan]Evrmore Wallet Tracker[/]\n\n"
                "Monitoring wallet activity in real-time...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Initialize state
        try:
            await update_balance()
        except Exception as e:
            print(f"Error getting initial balance: {e}")
        
        # Get recent transactions
        try:
            txs = await asyncio.to_thread(
                rpc.listtransactions,
                "*",
                20,  # Get last 20 transactions
                0,
                True
            )
            
            for tx_info in reversed(txs):
                try:
                    if 'txid' not in tx_info:
                        continue
                    tx_data = await asyncio.to_thread(
                        rpc.getrawtransaction,
                        tx_info['txid'],
                        True
                    )
                    tx = await process_transaction(tx_data)
                    if tx:
                        state['transactions'].append(tx)
                except Exception as e:
                    print(f"Error processing transaction: {e}")
                    continue
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
        
        # Start the tracker
        await tracker()
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.from_markup("[bold yellow]Shutting down...[/]"),
            title="Stopping"
        ))
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")

if __name__ == "__main__":
    asyncio.run(main()) 