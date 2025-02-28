#!/usr/bin/env python3
"""
Interactive WebSocket Dashboard for Evrmore Blockchain

This example creates an interactive dashboard that displays real-time blockchain data
using WebSockets. It shows block and transaction information as they occur.
"""

import asyncio
import json
import logging
import signal
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from evrmore_rpc.websockets import EvrmoreWebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("dashboard.log"), logging.StreamHandler()]
)
logger = logging.getLogger("websocket-dashboard")

# Global state
blocks: List[Dict[str, Any]] = []
transactions: List[Dict[str, Any]] = []
stats = {
    "start_time": datetime.now(),
    "blocks_count": 0,
    "tx_count": 0,
    "last_block_time": None,
    "tx_per_second": 0.0,
    "connected": False,
}

# Console for output
console = Console()

def create_layout() -> Layout:
    """Create the layout for the dashboard."""
    layout = Layout(name="root")
    
    # Split the screen into header, body, and footer
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body"),
        Layout(name="footer", size=3),
    )
    
    # Split the body into left and right columns
    layout["body"].split_row(
        Layout(name="left", ratio=1),
        Layout(name="right", ratio=1),
    )
    
    # Split the left column into blocks and stats
    layout["left"].split(
        Layout(name="blocks", ratio=2),
        Layout(name="stats", ratio=1),
    )
    
    # Right column is for transactions
    layout["right"].update(name="transactions")
    
    return layout

def render_header() -> Panel:
    """Render the header panel."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")
    grid.add_row(
        "[bold cyan]Evrmore Blockchain Real-time Dashboard[/]",
        f"[{'green' if stats['connected'] else 'red'}]{'Connected' if stats['connected'] else 'Disconnected'}[/]"
    )
    return Panel(grid, style="white on blue")

def render_footer() -> Panel:
    """Render the footer panel."""
    grid = Table.grid(expand=True)
    grid.add_column(justify="left", ratio=1)
    grid.add_column(justify="center", ratio=1)
    grid.add_column(justify="right")
    
    # Calculate uptime
    uptime = datetime.now() - stats["start_time"]
    uptime_str = f"{uptime.seconds // 3600:02}:{(uptime.seconds // 60) % 60:02}:{uptime.seconds % 60:02}"
    
    grid.add_row(
        f"[bold]Uptime:[/] {uptime_str}",
        f"[bold]Blocks:[/] {stats['blocks_count']}",
        f"[bold]Transactions:[/] {stats['tx_count']}"
    )
    return Panel(grid, style="white on blue")

def render_blocks() -> Panel:
    """Render the blocks panel."""
    table = Table(show_header=True, header_style="bold magenta", box=True)
    table.add_column("Height", justify="right", style="cyan", no_wrap=True)
    table.add_column("Hash", style="green")
    table.add_column("Time", justify="right", style="yellow")
    table.add_column("Txs", justify="right", style="red")
    table.add_column("Size", justify="right", style="blue")
    
    # Add the most recent blocks (up to 10)
    for block in blocks[:10]:
        timestamp = datetime.fromtimestamp(block["time"]).strftime("%H:%M:%S")
        table.add_row(
            str(block["height"]),
            block["hash"][:10] + "...",
            timestamp,
            str(len(block["tx"])),
            f"{block['size']:,} bytes"
        )
    
    return Panel(table, title="Recent Blocks", border_style="green")

def render_transactions() -> Panel:
    """Render the transactions panel."""
    table = Table(show_header=True, header_style="bold magenta", box=True)
    table.add_column("TXID", style="cyan")
    table.add_column("Size", justify="right", style="yellow")
    table.add_column("Inputs", justify="right", style="red")
    table.add_column("Outputs", justify="right", style="green")
    table.add_column("Time", justify="right", style="blue")
    
    # Add the most recent transactions (up to 15)
    for tx in transactions[:15]:
        timestamp = datetime.now().strftime("%H:%M:%S")
        if "time" in tx and tx["time"]:
            timestamp = datetime.fromtimestamp(tx["time"]).strftime("%H:%M:%S")
        
        table.add_row(
            tx["txid"][:10] + "...",
            f"{tx['size']:,} bytes",
            str(len(tx["vin"])),
            str(len(tx["vout"])),
            timestamp
        )
    
    return Panel(table, title="Recent Transactions", border_style="red")

def render_stats() -> Panel:
    """Render the stats panel."""
    table = Table(show_header=False, box=True)
    table.add_column("Stat", style="cyan")
    table.add_column("Value", style="yellow")
    
    # Calculate time since last block
    last_block_time_str = "N/A"
    if stats["last_block_time"]:
        time_since = datetime.now() - stats["last_block_time"]
        last_block_time_str = f"{time_since.seconds} seconds ago"
    
    table.add_row("Transactions/sec", f"{stats['tx_per_second']:.2f}")
    table.add_row("Last block", last_block_time_str)
    table.add_row("Avg block size", f"{calculate_avg_block_size():,} bytes")
    table.add_row("Avg txs per block", f"{calculate_avg_txs_per_block():.1f}")
    
    return Panel(table, title="Statistics", border_style="yellow")

def calculate_avg_block_size() -> float:
    """Calculate the average block size."""
    if not blocks:
        return 0
    return sum(block["size"] for block in blocks[:10]) / len(blocks[:10]) if blocks else 0

def calculate_avg_txs_per_block() -> float:
    """Calculate the average number of transactions per block."""
    if not blocks:
        return 0
    return sum(len(block["tx"]) for block in blocks[:10]) / len(blocks[:10]) if blocks else 0

def update_tx_per_second():
    """Update the transactions per second statistic."""
    elapsed = (datetime.now() - stats["start_time"]).total_seconds()
    if elapsed > 0:
        stats["tx_per_second"] = stats["tx_count"] / elapsed

async def handle_messages(client: EvrmoreWebSocketClient):
    """Handle incoming WebSocket messages."""
    try:
        async for message in client:
            if message.type == "block":
                block_data = message.data
                # Convert to dict for easier handling
                block_dict = block_data.dict()
                blocks.insert(0, block_dict)
                stats["blocks_count"] += 1
                stats["last_block_time"] = datetime.now()
                logger.info(f"New block: {block_dict['hash']} (height: {block_dict['height']})")
                
            elif message.type == "transaction":
                tx_data = message.data
                # Convert to dict for easier handling
                tx_dict = tx_data.dict()
                transactions.insert(0, tx_dict)
                stats["tx_count"] += 1
                update_tx_per_second()
                logger.info(f"New transaction: {tx_dict['txid']}")
                
            elif message.type == "error":
                error_data = message.data
                logger.error(f"Error: {error_data.message} (code: {error_data.code})")
    except Exception as e:
        logger.error(f"Error handling messages: {e}")
        stats["connected"] = False

async def main():
    """Run the WebSocket dashboard."""
    # Create a WebSocket client
    client = EvrmoreWebSocketClient(
        uri="ws://localhost:8765",
        ping_interval=30,
        reconnect_interval=5,
        max_reconnect_attempts=10
    )
    
    # Create the layout
    layout = create_layout()
    
    # Set up signal handlers for clean shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(client.disconnect()))
    
    try:
        # Connect to the WebSocket server
        await client.connect()
        stats["connected"] = True
        logger.info("Connected to WebSocket server")
        
        # Subscribe to block and transaction notifications
        await client.subscribe("blocks")
        await client.subscribe("transactions")
        logger.info("Subscribed to blocks and transactions")
        
        # Start the message handler
        message_task = asyncio.create_task(handle_messages(client))
        
        # Start the live display
        with Live(layout, refresh_per_second=4, screen=True) as live:
            while True:
                # Update the layout components
                layout["header"].update(render_header())
                layout["blocks"].update(render_blocks())
                layout["transactions"].update(render_transactions())
                layout["stats"].update(render_stats())
                layout["footer"].update(render_footer())
                
                # Sleep briefly to allow other tasks to run
                await asyncio.sleep(0.25)
                
                # Check if we're still connected
                if not stats["connected"] or message_task.done():
                    break
    
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Clean up
        stats["connected"] = False
        try:
            await client.unsubscribe("blocks")
            await client.unsubscribe("transactions")
            await client.disconnect()
            logger.info("Disconnected from WebSocket server")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    console.print("[bold green]Starting Evrmore Blockchain Dashboard...[/]")
    console.print("[yellow]Press Ctrl+C to exit[/]")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[bold red]Dashboard stopped by user[/]")
    except Exception as e:
        console.print(f"[bold red]Error:[/] {e}")
    finally:
        console.print("[bold green]Dashboard stopped[/]") 