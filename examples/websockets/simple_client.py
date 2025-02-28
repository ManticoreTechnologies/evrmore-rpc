#!/usr/bin/env python3
"""
Simple WebSocket Client Example

This example demonstrates how to use the EvrmoreWebSocketClient to subscribe to
blockchain events like new blocks and transactions.
"""

import asyncio
import signal
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from evrmore_rpc.websockets import EvrmoreWebSocketClient

# Create a rich console for pretty output
console = Console()

async def main():
    """Main function to demonstrate WebSocket client usage."""
    # Print header
    console.print(Panel.fit(
        "[bold blue]Evrmore WebSocket Client Example[/bold blue]",
        subtitle="Press Ctrl+C to exit"
    ))
    
    # Create a WebSocket client
    client = EvrmoreWebSocketClient(
        uri="ws://localhost:8820",  # Change this to your WebSocket server address
        ping_interval=30.0,
        ping_timeout=10.0
    )
    
    # Set up signal handling for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(client)))
    
    try:
        # Connect to the WebSocket server
        console.print("[yellow]Connecting to WebSocket server...[/yellow]")
        await client.connect()
        console.print("[green]Connected![/green]")
        
        # Subscribe to blocks and transactions
        console.print("[yellow]Subscribing to blocks and transactions...[/yellow]")
        await client.subscribe("blocks")
        await client.subscribe("transactions")
        console.print("[green]Subscribed![/green]")
        
        # Listen for messages
        console.print("[bold]Listening for blockchain events...[/bold]")
        console.print("[dim]Waiting for new blocks and transactions...[/dim]")
        
        # Process messages
        async for message in client:
            if message.type == "block":
                # Display block information
                block = message.data
                block_table = Table(title=f"New Block #{block.height}")
                block_table.add_column("Property", style="cyan")
                block_table.add_column("Value", style="green")
                block_table.add_row("Hash", block.hash)
                block_table.add_row("Height", str(block.height))
                block_table.add_row("Time", str(block.time))
                block_table.add_row("Transactions", str(len(block.tx)))
                block_table.add_row("Size", f"{block.size} bytes")
                console.print(block_table)
                
            elif message.type == "transaction":
                # Display transaction information
                tx = message.data
                tx_table = Table(title=f"New Transaction")
                tx_table.add_column("Property", style="cyan")
                tx_table.add_column("Value", style="green")
                tx_table.add_row("TXID", tx.txid)
                tx_table.add_row("Size", f"{tx.size} bytes")
                tx_table.add_row("Inputs", str(len(tx.vin)))
                tx_table.add_row("Outputs", str(len(tx.vout)))
                console.print(tx_table)
                
            else:
                # Display other message types
                console.print(f"[yellow]Received message of type: {message.type}[/yellow]")
                
    except ConnectionError as e:
        console.print(f"[bold red]Connection error: {e}[/bold red]")
    except Exception as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
    finally:
        # Ensure client is disconnected
        if client.connected:
            await client.disconnect()
            console.print("[yellow]Disconnected from WebSocket server[/yellow]")

async def shutdown(client):
    """Gracefully shut down the client."""
    console.print("[yellow]Shutting down...[/yellow]")
    if client.connected:
        # Unsubscribe from topics
        for topic in list(client.subscriptions):
            await client.unsubscribe(topic)
        # Disconnect
        await client.disconnect()
    # Stop the event loop
    asyncio.get_event_loop().stop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        console.print("[yellow]Interrupted by user[/yellow]") 