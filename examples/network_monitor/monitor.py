#!/usr/bin/env python3
"""
Evrmore Network Monitor Example

This example demonstrates how to:
1. Monitor network connections and peer information
2. Track network traffic and bandwidth usage
3. Detect network issues and peer misbehavior
4. Generate network health reports

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
from rich.progress import Progress
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic

# Rich console for pretty output
console = Console()

@dataclass
class NetworkStats:
    """Network statistics."""
    connections: int
    inbound: int
    outbound: int
    total_sent: int
    total_recv: int
    banned: int
    uptime: int
    last_updated: datetime

@dataclass
class PeerInfo:
    """Information about a connected peer."""
    id: int
    addr: str
    services: str
    last_send: datetime
    last_recv: datetime
    bytes_sent: int
    bytes_recv: int
    connection_time: datetime
    version: int
    subver: str
    inbound: bool
    release_time: int
    ping_time: Optional[float]
    ban_score: int
    sync_height: int
    last_updated: datetime

# Global state
state = {
    'stats': None,  # Current network stats
    'peers': {},  # Peer ID -> PeerInfo
    'banned': set(),  # Set of banned addresses
    'start_time': datetime.now(),
    'tx_count': 0,
    'block_count': 0,
}

# RPC client
rpc = EvrmoreRPCClient()

def format_size(size: int) -> str:
    """Format size in bytes to human readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} TB"

def format_speed(bytes_per_sec: float) -> str:
    """Format speed in bytes/sec to human readable format."""
    return format_size(bytes_per_sec) + "/s"

async def get_network_stats() -> NetworkStats:
    """Get current network statistics."""
    try:
        # Get peer info
        peers = await asyncio.to_thread(rpc.getpeerinfo)
        peers_dict = [dict(p) for p in peers]  # Convert to dictionaries
        inbound = sum(1 for p in peers_dict if p.get('inbound', False))
        outbound = len(peers_dict) - inbound
        
        # Get network totals
        net_totals = await asyncio.to_thread(rpc.getnettotals)
        net_totals_dict = dict(net_totals)  # Convert to dictionary
        
        # Get banned list
        banned = await asyncio.to_thread(rpc.listbanned)
        banned_dict = [dict(b) for b in banned]  # Convert to dictionary
        
        # Get uptime
        uptime = await asyncio.to_thread(rpc.uptime)
        
        return NetworkStats(
            connections=len(peers_dict),
            inbound=inbound,
            outbound=outbound,
            total_sent=net_totals_dict.get('totalbytessent', 0),
            total_recv=net_totals_dict.get('totalbytesrecv', 0),
            banned=len(banned_dict),
            uptime=uptime,
            last_updated=datetime.now()
        )
    except Exception as e:
        print(f"Error getting network stats: {e}")
        return NetworkStats(
            connections=0,
            inbound=0,
            outbound=0,
            total_sent=0,
            total_recv=0,
            banned=0,
            uptime=0,
            last_updated=datetime.now()
        )

async def update_peer_info() -> None:
    """Update peer information."""
    try:
        peers = await asyncio.to_thread(rpc.getpeerinfo)
        peers_dict = [dict(p) for p in peers]  # Convert to dictionaries
        now = datetime.now()
        
        # Update peer info
        current_peers = set()
        for peer_data in peers_dict:
            try:
                peer_id = peer_data.get('id', 0)
                current_peers.add(peer_id)
                
                state['peers'][peer_id] = PeerInfo(
                    id=peer_id,
                    addr=peer_data.get('addr', 'unknown'),
                    services=peer_data.get('services', ''),
                    last_send=datetime.fromtimestamp(peer_data.get('lastsend', 0)),
                    last_recv=datetime.fromtimestamp(peer_data.get('lastrecv', 0)),
                    bytes_sent=peer_data.get('bytessent', 0),
                    bytes_recv=peer_data.get('bytesrecv', 0),
                    connection_time=datetime.fromtimestamp(peer_data.get('conntime', 0)),
                    version=peer_data.get('version', 0),
                    subver=peer_data.get('subver', ''),
                    inbound=peer_data.get('inbound', False),
                    release_time=peer_data.get('releasetime', 0),
                    ping_time=peer_data.get('pingtime'),
                    ban_score=peer_data.get('banscore', 0),
                    sync_height=peer_data.get('synced_headers', 0),
                    last_updated=now
                )
            except Exception as e:
                print(f"Error processing peer data: {e}")
                continue
        
        # Remove disconnected peers
        for peer_id in list(state['peers'].keys()):
            if peer_id not in current_peers:
                del state['peers'][peer_id]
        
        # Update banned addresses
        try:
            banned = await asyncio.to_thread(rpc.listbanned)
            banned_dict = [dict(b) for b in banned]  # Convert to dictionary
            state['banned'] = {b.get('address', '') for b in banned_dict if b.get('address')}
        except Exception as e:
            print(f"Error getting banned addresses: {e}")
            state['banned'] = set()
            
    except Exception as e:
        print(f"Error updating peer info: {e}")
        state['peers'] = {}

def create_stats_table() -> Table:
    """Create a table showing current network statistics."""
    table = Table(title="Network Monitor")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    table.add_column("Details", style="yellow")
    
    # Calculate rates
    runtime = (datetime.now() - state['start_time']).total_seconds()
    tx_rate = state['tx_count'] / runtime if runtime > 0 else 0
    block_rate = state['block_count'] / runtime if runtime > 0 else 0
    
    # Add statistics
    if state['stats']:
        stats = state['stats']
        table.add_row(
            "Connections",
            str(stats.connections),
            f"In: {stats.inbound}, Out: {stats.outbound}"
        )
        table.add_row(
            "Network Traffic",
            format_size(stats.total_recv),
            f"Sent: {format_size(stats.total_sent)}"
        )
        table.add_row(
            "Banned Peers",
            str(stats.banned),
            f"Uptime: {timedelta(seconds=stats.uptime)}"
        )
    
    # Add transaction stats
    table.add_row(
        "Transactions",
        str(state['tx_count']),
        f"Rate: {tx_rate:.2f} tx/s"
    )
    table.add_row(
        "Blocks",
        str(state['block_count']),
        f"Rate: {block_rate:.2f} blocks/s"
    )
    
    # Add peer information
    if state['peers']:
        table.add_row("Connected Peers", "", "")
        for peer in sorted(state['peers'].values(), key=lambda p: p.id)[:5]:
            ping = f"Ping: {peer.ping_time:.2f}ms" if peer.ping_time is not None else ""
            table.add_row(
                peer.addr,
                "Inbound" if peer.inbound else "Outbound",
                f"Version: {peer.subver}, {ping}"
            )
    
    # Add banned peers
    if state['banned']:
        table.add_row("Banned Addresses", "", "")
        for addr in sorted(state['banned'])[:5]:
            table.add_row(addr, "Banned", "")
    
    return table

async def handle_transaction(notification: ZMQNotification) -> None:
    """Handle new transaction notifications."""
    state['tx_count'] += 1

async def handle_block(notification: ZMQNotification) -> None:
    """Handle new block notifications."""
    state['block_count'] += 1

async def monitor() -> None:
    """Main monitoring function."""
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient()
    
    # Register handlers
    zmq_client.on(ZMQTopic.HASH_TX)(handle_transaction)
    zmq_client.on(ZMQTopic.HASH_BLOCK)(handle_block)
    
    # Start ZMQ client
    zmq_task = asyncio.create_task(zmq_client.start())
    
    # Create update task
    async def update_stats():
        while True:
            try:
                state['stats'] = await get_network_stats()
                await update_peer_info()
                await asyncio.sleep(5)  # Update every 5 seconds
            except asyncio.CancelledError:
                break
            except Exception as e:
                console.print(f"[red]Error updating stats:[/] {e}")
                await asyncio.sleep(1)
    
    update_task = asyncio.create_task(update_stats())
    
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
    update_task.cancel()
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
                "[bold cyan]Evrmore Network Monitor[/]\n\n"
                "Monitoring network activity in real-time...\n"
                "Press [bold]Ctrl+C[/] to stop"
            ),
            title="Starting"
        ))
        
        # Initialize state
        state['stats'] = await get_network_stats()
        await update_peer_info()
        
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