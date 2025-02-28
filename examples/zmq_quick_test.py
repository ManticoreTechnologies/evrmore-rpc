#!/usr/bin/env python3
"""
Quick ZMQ Monitor Example

Demonstrates how to use the ZMQ client to monitor blockchain events in real-time.
This example subscribes to transaction, block, and sequence notifications.
"""

import asyncio
import signal
from datetime import datetime

from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic
from rich.console import Console
from rich.panel import Panel

console = Console()

# Track stats
stats = {
    "transactions": 0,
    "blocks": 0,
    "sequences": 0,
    "start_time": datetime.now()
}


async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle transaction notifications."""
    stats["transactions"] += 1
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    
    console.print(f"[yellow]New Transaction:[/] [cyan]{notification.hex[:10]}...[/]")
    console.print(f"[green]Stats:[/] {stats['transactions']} txs, {stats['blocks']} blocks in {elapsed:.1f}s")


async def handle_block(notification: ZMQNotification) -> None:
    """Handle block notifications."""
    stats["blocks"] += 1
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    
    console.print(Panel(
        f"[bold yellow]NEW BLOCK:[/] [cyan]{notification.hex}[/]\n"
        f"[green]Stats:[/] {stats['transactions']} txs, {stats['blocks']} blocks in {elapsed:.1f}s",
        title="Block Notification",
        border_style="blue"
    ))


async def handle_sequence(notification: ZMQNotification) -> None:
    """Handle sequence notifications."""
    stats["sequences"] += 1
    console.print(f"[purple]Sequence:[/] {notification.topic_name} - {notification.sequence}")


async def main():
    """Main entry point."""
    # Print welcome message
    console.print(Panel(
        "This example monitors Evrmore blockchain activity in real-time using ZMQ.\n"
        "It will display new transactions and blocks as they are detected.\n"
        "Press Ctrl+C to exit.",
        title="Evrmore ZMQ Monitor",
        border_style="green"
    ))
    
    # Set up signal handlers for clean shutdown
    loop = asyncio.get_running_loop()
    client = EvrmoreZMQClient()
    
    # Register interrupt handler
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(client.stop()))
    
    # Register callback handlers
    client.on_transaction(handle_transaction)
    client.on_block(handle_block)
    client.on_sequence(handle_sequence)
    
    # Start the client
    try:
        console.print("[yellow]Starting ZMQ client...[/]")
        await client.start()
        
        # Keep running until stopped
        while client._running:
            await asyncio.sleep(1)
    finally:
        # Ensure we stop the client
        if client._running:
            await client.stop()
    
    console.print("[yellow]ZMQ client stopped.[/]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]Interrupted by user[/]") 