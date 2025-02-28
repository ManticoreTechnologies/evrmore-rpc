#!/usr/bin/env python3
"""
Example script demonstrating Evrmore ZMQ monitoring.

This script connects to an Evrmore node's ZMQ interface and monitors:
- New transactions
- New blocks
- Sequence updates

Make sure your evrmore.conf has the following ZMQ settings:
    zmqpubhashtxhwm=10000
    zmqpubhashblockhwm=10000
    zmqpubrawblockhwm=10000
    zmqpubrawtxhwm=10000
    zmqpubsequencehwm=10000
    zmqpubhashtx=tcp://127.0.0.1:28332
    zmqpubrawtx=tcp://127.0.0.1:28332
    zmqpubhashblock=tcp://127.0.0.1:28332
    zmqpubrawblock=tcp://127.0.0.1:28332
    zmqpubsequence=tcp://127.0.0.1:28332
"""

import asyncio
import signal
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic
from evrmore_rpc.zmq.models import ZMQTransaction, ZMQBlock, ZMQSequence

# Rich console for pretty output
console = Console()

# Statistics for monitoring
stats = {
    'transactions': 0,
    'blocks': 0,
    'sequences': 0,
    'start_time': datetime.now(),
    'last_tx': None,
    'last_block': None,
    'last_sequence': None
}

def create_stats_table() -> Table:
    """Create a table showing current statistics."""
    table = Table(title="Evrmore ZMQ Monitor")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Rate", style="yellow")
    
    runtime = (datetime.now() - stats['start_time']).total_seconds()
    tx_rate = stats['transactions'] / runtime if runtime > 0 else 0
    block_rate = stats['blocks'] / runtime if runtime > 0 else 0
    
    table.add_row(
        "Runtime",
        f"{runtime:.1f} seconds",
        ""
    )
    table.add_row(
        "Transactions",
        str(stats['transactions']),
        f"{tx_rate:.2f}/s"
    )
    table.add_row(
        "Blocks",
        str(stats['blocks']),
        f"{block_rate:.2f}/s"
    )
    table.add_row(
        "Sequences",
        str(stats['sequences']),
        ""
    )
    
    if stats['last_tx']:
        table.add_row("Last Transaction", stats['last_tx'], "")
    if stats['last_block']:
        table.add_row("Last Block", stats['last_block'], "")
    if stats['last_sequence']:
        table.add_row("Last Sequence", stats['last_sequence'], "")
    
    return table

async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle transaction notifications."""
    stats['transactions'] += 1
    
    if notification.topic == ZMQTopic.RAW_TX:
        # Parse the raw transaction
        tx = ZMQTransaction.from_raw(notification.body)
        stats['last_tx'] = (
            f"ID: {tx.txid[:8]}... "
            f"Size: {tx.size} bytes "
            f"Inputs: {len(tx.vin)} "
            f"Outputs: {len(tx.vout)}"
        )
    else:
        # Just show the transaction hash
        stats['last_tx'] = f"Hash: {notification.hex[:16]}..."

async def handle_block(notification: ZMQNotification) -> None:
    """Handle block notifications."""
    stats['blocks'] += 1
    
    if notification.topic == ZMQTopic.RAW_BLOCK:
        # Parse the raw block
        block = ZMQBlock.from_raw(notification.body)
        stats['last_block'] = (
            f"Hash: {block.hash[:8]}... "
            f"Time: {block.time.strftime('%H:%M:%S')} "
            f"Nonce: {block.nonce}"
        )
    else:
        # Just show the block hash
        stats['last_block'] = f"Hash: {notification.hex[:16]}..."

async def handle_sequence(notification: ZMQNotification) -> None:
    """Handle sequence notifications."""
    stats['sequences'] += 1
    
    if notification.sequence is not None:
        seq = ZMQSequence.from_notification(notification.sequence, notification.body)
        stats['last_sequence'] = (
            f"Height: {seq.height} "
            f"Hash: {seq.hash[:8]}..."
        )
    else:
        stats['last_sequence'] = f"Hash: {notification.hex[:16]}..."

async def monitor_zmq():
    """Main monitoring function."""
    # Create ZMQ client
    client = EvrmoreZMQClient()
    
    # Register handlers
    client.on_transaction(handle_transaction)
    client.on_block(handle_block)
    client.on_sequence(handle_sequence)
    
    # Start client in background
    client_task = asyncio.create_task(client.start())
    
    # Create live display
    with Live(create_stats_table(), refresh_per_second=4) as live:
        def update_table():
            live.update(create_stats_table())
        
        # Update display periodically
        while True:
            try:
                update_table()
                await asyncio.sleep(0.25)  # 4 times per second
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]Error:[/] {e}")
                break
    
    # Stop client
    await client.stop()
    if not client_task.done():
        client_task.cancel()
        try:
            await client_task
        except asyncio.CancelledError:
            pass

async def main():
    """Main entry point."""
    try:
        console.print(Panel(
            Text.from_markup(
                "[bold cyan]Evrmore ZMQ Monitor[/]\n\n"
                "Monitoring real-time blockchain events...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Run the monitor
        await monitor_zmq()
        
    except KeyboardInterrupt:
        console.print(Panel(
            Text.from_markup("[bold yellow]Shutting down...[/]"),
            title="Stopping"
        ))

if __name__ == "__main__":
    asyncio.run(main()) 