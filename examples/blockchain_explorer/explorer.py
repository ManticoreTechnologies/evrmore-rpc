#!/usr/bin/env python3
"""
Evrmore Blockchain Explorer Example (Simplified)

This example demonstrates how to build a simple blockchain explorer that:
1. Monitors new blocks and transactions using polling
2. Allows querying historical data using RPC
3. Provides detailed information about blocks, transactions, and addresses
4. Calculates network statistics

Requirements:
    - Evrmore node with RPC enabled
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
from evrmore_rpc import EvrmoreClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc.zmq.models import ZMQNotification

# Rich console for pretty output
console = Console()

# Global state
state = {
    'latest_blocks': [],  # Keep track of last 10 blocks
    'latest_txs': [],     # Keep track of last 10 transactions
    'start_time': datetime.now(),
    'block_count': 0,
    'tx_count': 0,
    'last_block': 0,
}

# RPC client
rpc = EvrmoreClient()
# Force sync mode
rpc.force_sync()

def format_amount(amount: Decimal) -> str:
    """Format EVR amount with proper precision."""
    return f"{amount:,.8f} EVR"

async def get_block_info(block_hash: str) -> dict:
    """Get detailed block information."""
    block = rpc.getblock(block_hash, 2)  # Verbose output with tx details
    
    # Calculate block reward
    reward = Decimal('0')
    for tx in block['tx']:
        if 'vin' not in tx or not tx['vin'] or 'coinbase' not in tx['vin'][0]:
            continue
        for vout in tx['vout']:
            reward += Decimal(str(vout['value']))
    
    return {
        'hash': block['hash'],
        'height': block['height'],
        'time': datetime.fromtimestamp(block['time']),
        'transactions': len(block['tx']),
        'size': block['size'],
        'weight': block.get('weight', 0),
        'difficulty': Decimal(str(block['difficulty'])),
        'reward': reward,
        'tx_ids': [tx['txid'] for tx in block['tx'][:10]],  # Just store first 10 txids
    }

async def get_transaction_info(txid: str) -> dict:
    """Get detailed transaction information."""
    tx = rpc.getrawtransaction(txid, True)
    
    # Calculate total input/output values
    total_in = Decimal('0')
    total_out = Decimal('0')
    
    for vin in tx.get('vin', []):
        if 'coinbase' in vin:
            continue
        try:
            prev_tx = rpc.getrawtransaction(vin['txid'], True)
            total_in += Decimal(str(prev_tx['vout'][vin['vout']]['value']))
        except Exception as e:
            console.print(f"[yellow]Warning getting input value: {e}[/yellow]")
    
    for vout in tx.get('vout', []):
        total_out += Decimal(str(vout['value']))
    
    # Get block time for transaction
    block_hash = tx.get('blockhash')
    if block_hash:
        block_time = tx.get('blocktime', 0)
        if not block_time:
            try:
                block = rpc.getblock(block_hash, 1)
                block_time = block['time']
            except:
                block_time = int(datetime.now().timestamp())
    else:
        # For mempool transactions, use current time
        block_time = int(datetime.now().timestamp())
    
    return {
        'txid': tx['txid'],
        'size': tx.get('size', 0),
        'time': datetime.fromtimestamp(block_time),
        'total_input': total_in,
        'total_output': total_out,
        'fee': total_in - total_out if total_in > 0 else Decimal('0'),
        'confirmations': tx.get('confirmations', 0),
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
        "Current Height",
        str(state['last_block']),
        f"{block_rate:.4f} blocks/s"
    )
    table.add_row(
        "Transactions",
        str(state['tx_count']),
        f"{tx_rate:.2f} tx/s"
    )
    
    # Add latest blocks
    if state['latest_blocks']:
        table.add_row("Latest Blocks", "", "")
        for block in state['latest_blocks'][:5]:
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
        for tx in state['latest_txs'][:5]:
            table.add_row(
                tx['txid'][:8] + "...",
                format_amount(tx['total_output']),
                f"Fee: {format_amount(tx['fee'])}, "
                f"Confs: {tx['confirmations']}"
            )
    
    return table

async def process_new_blocks(start_height: int, end_height: int) -> None:
    """Process new blocks from start_height to end_height (inclusive)."""
    for height in range(start_height, end_height + 1):
        try:
            # Get block hash
            block_hash = rpc.getblockhash(height)
            
            # Get detailed block info
            block = await get_block_info(block_hash)
            state['latest_blocks'].insert(0, block)
            state['block_count'] += 1
            
            # Process transactions in the block
            for txid in block['tx_ids']:
                tx = await get_transaction_info(txid)
                state['latest_txs'].insert(0, tx)
                state['tx_count'] += 1
            
            # Keep only last 10 blocks and transactions
            if len(state['latest_blocks']) > 10:
                state['latest_blocks'] = state['latest_blocks'][:10]
                
            if len(state['latest_txs']) > 10:
                state['latest_txs'] = state['latest_txs'][:10]
                
            # Update last processed block
            state['last_block'] = height
            
        except Exception as e:
            console.print(f"[red]Error processing block {height}: {e}[/red]")

async def explorer() -> None:
    """Main explorer function."""
    # Get initial blockchain info
    chain_info = rpc.getblockchaininfo()
    state['last_block'] = chain_info['blocks'] - 10  # Start 10 blocks back
    if state['last_block'] < 0:
        state['last_block'] = 0
    
    # Initialize with some blocks
    current_height = chain_info['blocks']
    await process_new_blocks(state['last_block'] + 1, current_height)
    
    # Create live display
    with Live(create_stats_table(), refresh_per_second=4) as live:
        while True:
            try:
                # Check for new blocks
                current_height = rpc.getblockcount()
                
                if current_height > state['last_block']:
                    console.print(f"[green]New blocks detected: {state['last_block'] + 1} to {current_height}[/green]")
                    await process_new_blocks(state['last_block'] + 1, current_height)
                
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
                "[bold cyan]Evrmore Blockchain Explorer[/]\n\n"
                "Monitoring blockchain activity...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Set up signal handling
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown()))
        
        # Start explorer
        await explorer()
    
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