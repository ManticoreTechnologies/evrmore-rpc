#!/usr/bin/env python3
"""
Evrmore Blockchain Explorer Example

This example demonstrates how to build a simple blockchain explorer that:
1. Monitors new blocks and transactions in real-time using ZMQ
2. Allows querying historical data using RPC
3. Provides detailed information about blocks, transactions, and addresses
4. Calculates network statistics

Requirements:
    - Evrmore node with RPC and ZMQ enabled
    - evrmore-rpc package installed
"""

import asyncio
import signal
from datetime import datetime
from decimal import Decimal
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.prompt import Prompt
from rich.progress import Progress
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic
from evrmore_rpc.commands.blockchain import Block as BlockModel
from evrmore_rpc.commands.rawtransactions import DecodedRawTransaction

# Rich console for pretty output
console = Console()

# Global state
state = {
    'latest_blocks': [],  # Keep track of last 10 blocks
    'latest_txs': [],     # Keep track of last 10 transactions
    'start_time': datetime.now(),
    'block_count': 0,
    'tx_count': 0,
}

# RPC client
rpc = EvrmoreRPCClient()

def format_amount(amount: Decimal) -> str:
    """Format EVR amount with proper precision."""
    return f"{amount:,.8f} EVR"

async def get_block_info(block_hash: str) -> dict:
    """Get detailed block information."""
    block = await asyncio.to_thread(rpc.getblock, block_hash, 2)  # Verbose output
    block_dict = dict(block)  # Convert to dictionary since verbosity 2 returns raw data
    
    # Calculate block reward
    reward = Decimal('0')
    for tx in block_dict['tx']:
        if not tx['vin'][0].get('coinbase'):
            continue
        for vout in tx['vout']:
            reward += Decimal(str(vout['value']))
    
    return {
        'hash': block_dict['hash'],
        'height': block_dict['height'],
        'time': datetime.fromtimestamp(block_dict['time']),
        'transactions': len(block_dict['tx']),
        'size': block_dict['size'],
        'weight': block_dict['weight'],
        'difficulty': Decimal(str(block_dict['difficulty'])),
        'reward': reward,
    }

async def get_transaction_info(txid: str) -> dict:
    """Get detailed transaction information."""
    tx = await asyncio.to_thread(rpc.getrawtransaction, txid, True)
    tx_dict = dict(tx)  # Convert to dictionary since we need raw data
    
    # Calculate total input/output values
    total_in = Decimal('0')
    total_out = Decimal('0')
    
    for vin in tx_dict['vin']:
        if 'coinbase' in vin:
            continue
        prev_tx = await asyncio.to_thread(
            rpc.getrawtransaction,
            vin['txid'],
            True
        )
        prev_tx_dict = dict(prev_tx)  # Convert to dictionary
        total_in += Decimal(str(prev_tx_dict['vout'][vin['vout']]['value']))
    
    for vout in tx_dict['vout']:
        total_out += Decimal(str(vout['value']))
    
    # Get block time for transaction
    block_hash = tx_dict.get('blockhash')
    if block_hash:
        block = await asyncio.to_thread(rpc.getblock, block_hash, 1)
        block_dict = dict(block)
        tx_time = block_dict['time']
    else:
        # For mempool transactions, use current time
        tx_time = int(datetime.now().timestamp())
    
    return {
        'txid': tx_dict['txid'],
        'size': tx_dict['size'],
        'time': datetime.fromtimestamp(tx_time),
        'total_input': total_in,
        'total_output': total_out,
        'fee': total_in - total_out if total_in > 0 else Decimal('0'),
    }

def create_stats_table() -> Table:
    """Create a table showing current blockchain statistics."""
    table = Table(title="Blockchain Explorer")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate rates
    runtime = (datetime.now() - state['start_time']).total_seconds()
    block_rate = state['block_count'] / runtime if runtime > 0 else 0
    tx_rate = state['tx_count'] / runtime if runtime > 0 else 0
    
    # Add statistics
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        f"Since {state['start_time'].strftime('%H:%M:%S')}"
    )
    table.add_row(
        "Blocks",
        str(state['block_count']),
        f"{block_rate:.2f} blocks/s"
    )
    table.add_row(
        "Transactions",
        str(state['tx_count']),
        f"{tx_rate:.2f} tx/s"
    )
    
    # Add latest blocks
    if state['latest_blocks']:
        table.add_row("Latest Blocks", "", "")
        for block in reversed(state['latest_blocks'][-5:]):
            table.add_row(
                f"Block {block['height']}",
                block['hash'][:8] + "...",
                f"Txs: {block['transactions']}, "
                f"Size: {block['size']} bytes, "
                f"Reward: {format_amount(block['reward'])}"
            )
    
    # Add latest transactions
    if state['latest_txs']:
        table.add_row("Latest Transactions", "", "")
        for tx in reversed(state['latest_txs'][-5:]):
            table.add_row(
                tx['txid'][:8] + "...",
                format_amount(tx['total_output']),
                f"Fee: {format_amount(tx['fee'])}, "
                f"Size: {tx['size']} bytes"
            )
    
    return table

async def handle_block(notification: ZMQNotification) -> None:
    """Handle new block notifications."""
    state['block_count'] += 1
    
    # Get detailed block info
    block = await get_block_info(notification.hex)
    state['latest_blocks'].append(block)
    
    # Keep only last 10 blocks
    if len(state['latest_blocks']) > 10:
        state['latest_blocks'].pop(0)

async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle new transaction notifications."""
    state['tx_count'] += 1
    
    # Get detailed transaction info
    tx = await get_transaction_info(notification.hex)
    state['latest_txs'].append(tx)
    
    # Keep only last 10 transactions
    if len(state['latest_txs']) > 10:
        state['latest_txs'].pop(0)

async def explorer() -> None:
    """Main explorer function."""
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient()
    
    # Register handlers
    zmq_client.on(ZMQTopic.HASH_BLOCK)(handle_block)
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
                "[bold cyan]Evrmore Blockchain Explorer[/]\n\n"
                "Monitoring blockchain activity in real-time...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Initialize state with current blockchain info
        info = await asyncio.to_thread(rpc.getblockchaininfo)
        tip = await get_block_info(info.bestblockhash)
        state['latest_blocks'].append(tip)
        
        # Get some recent transactions
        mempool = await asyncio.to_thread(rpc.getrawmempool)
        for txid in mempool[:5]:  # Get first 5 transactions
            tx = await get_transaction_info(txid)
            state['latest_txs'].append(tx)
        
        # Start the explorer
        await explorer()
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.from_markup("[bold yellow]Shutting down...[/]"),
            title="Stopping"
        ))
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")

if __name__ == "__main__":
    asyncio.run(main()) 