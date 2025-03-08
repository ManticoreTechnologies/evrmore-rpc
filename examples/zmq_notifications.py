#!/usr/bin/env python3
"""
Evrmore ZMQ Notifications Example

This example demonstrates how to use the ZMQ client to receive real-time
notifications from the Evrmore blockchain, including:

1. Setting up the ZMQ client
2. Registering handlers for different notification types
3. Starting and stopping the client
4. Processing block and transaction notifications
5. Using the RPC client alongside ZMQ for additional data

Requirements:
- Evrmore node with ZMQ enabled in the configuration:
  zmqpubhashtx=tcp://127.0.0.1:28332
  zmqpubhashblock=tcp://127.0.0.1:28332
  zmqpubrawtx=tcp://127.0.0.1:28332
  zmqpubrawblock=tcp://127.0.0.1:28332
"""

import asyncio
import signal
import time
from datetime import datetime
from typing import Dict, Set, List, Optional
import binascii

# Import the ZMQ client and topic enum
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc.zmq.models import ZMQNotification

# Import the RPC client for additional blockchain queries
from evrmore_rpc import EvrmoreClient

# Statistics tracking
stats = {
    'start_time': time.time(),
    'blocks_seen': 0,
    'txs_seen': 0,
    'last_block_time': None,
    'last_tx_time': None,
    'latest_block_hash': None,
    'latest_tx_hash': None,
    'asset_txs': set(),  # Set of transactions involving assets
}

# Create RPC client for blockchain queries
# Important: We'll initialize it properly in main()
rpc_client = None

# Flag to control the main loop
running = True

def format_time_ago(timestamp: Optional[float]) -> str:
    """Format how long ago an event occurred."""
    if timestamp is None:
        return "never"
    
    seconds_ago = time.time() - timestamp
    if seconds_ago < 60:
        return f"{seconds_ago:.1f} seconds ago"
    elif seconds_ago < 3600:
        return f"{seconds_ago/60:.1f} minutes ago"
    else:
        return f"{seconds_ago/3600:.1f} hours ago"

def print_stats() -> None:
    """Print current statistics."""
    uptime = time.time() - stats['start_time']
    print("\n=== ZMQ Notification Monitor ===")
    print(f"Uptime: {uptime:.1f} seconds")
    print(f"Blocks seen: {stats['blocks_seen']} (last: {format_time_ago(stats['last_block_time'])})")
    print(f"Transactions seen: {stats['txs_seen']} (last: {format_time_ago(stats['last_tx_time'])})")
    
    if stats['latest_block_hash']:
        print(f"Latest block: {stats['latest_block_hash'].hex()}")
    
    if stats['latest_tx_hash']:
        print(f"Latest transaction: {stats['latest_tx_hash'].hex()}")
    
    print(f"Asset transactions: {len(stats['asset_txs'])}")
    print("================================\n")

async def check_for_assets(tx_hash: bytes) -> None:
    """Check if a transaction involves assets using RPC."""
    global rpc_client
    
    try:
        # Get the transaction details
        tx_hex = await rpc_client.getrawtransaction(tx_hash.hex())
        tx_data = await rpc_client.decoderawtransaction(tx_hex)
        
        # Check if any outputs involve assets
        for output in tx_data.get('vout', []):
            script_pub_key = output.get('scriptPubKey', {})
            if 'asset' in script_pub_key:
                stats['asset_txs'].add(tx_hash.hex())
                asset = script_pub_key['asset']
                asset_name = asset['name']
                asset_amount = asset['amount']
                print(f"Asset transaction detected: {asset_name} = {asset_amount}")
                return
    except Exception as e:
        print(f"Error checking transaction for assets: {e}")

async def main():
    global running, rpc_client
    
    # Initialize the RPC client in async mode
    rpc_client = EvrmoreClient()
    # Force the client into async mode since we'll use it in async context
    rpc_client.force_async()
    
    # Create a ZMQ client
    zmq_client = EvrmoreZMQClient(
        zmq_host="127.0.0.1",  # Change this if your node uses a different address
        zmq_port=28332,        # Change this if your node uses a different ZMQ port
        topics=[               # Specify which notifications you want to receive
            ZMQTopic.HASH_BLOCK,
            ZMQTopic.HASH_TX,
            ZMQTopic.RAW_BLOCK,  # Comment this out if you don't need full blocks
            ZMQTopic.RAW_TX      # Comment this out if you don't need full transactions
        ]
    )
    
    # Register a handler for new blocks (lightweight notification)
    @zmq_client.on(ZMQTopic.HASH_BLOCK)
    async def handle_block(notification: ZMQNotification) -> None:
        stats['blocks_seen'] += 1
        stats['last_block_time'] = time.time()
        stats['latest_block_hash'] = notification.body
        print(f"New block: {notification.hex}")
        
        # Get block details using RPC
        try:
            block_data = await rpc_client.getblock(notification.hex)
            print(f"Block height: {block_data['height']}, Transactions: {len(block_data['tx'])}")
        except Exception as e:
            print(f"Error getting block details: {e}")
    
    # Register a handler for new transactions (lightweight notification)
    @zmq_client.on(ZMQTopic.HASH_TX)
    async def handle_transaction(notification: ZMQNotification) -> None:
        stats['txs_seen'] += 1
        stats['last_tx_time'] = time.time()
        stats['latest_tx_hash'] = notification.body
        print(f"New transaction: {notification.hex}")
        
        # Check if this transaction involves assets
        await check_for_assets(notification.body)
    
    # Register a handler for raw blocks (full block data)
    @zmq_client.on(ZMQTopic.RAW_BLOCK)
    async def handle_raw_block(notification: ZMQNotification) -> None:
        # This handler receives the full serialized block
        # Processing this data requires low-level deserialization
        # Just print the size for demonstration purposes
        print(f"Raw block received: {len(notification.body)} bytes")
    
    # Register a handler for raw transactions (full transaction data)
    @zmq_client.on(ZMQTopic.RAW_TX)
    async def handle_raw_transaction(notification: ZMQNotification) -> None:
        # This handler receives the full serialized transaction
        # Processing this data requires low-level deserialization
        # Just print the size for demonstration purposes
        print(f"Raw transaction received: {len(notification.body)} bytes")
    
    # Setup signal handlers for clean shutdown
    def signal_handler():
        global running
        running = False
        print("Shutting down...")
    
    # Register signal handlers
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, signal_handler)
    
    print("Starting ZMQ notification monitor...")
    print("Press Ctrl+C to exit")
    
    # Start the ZMQ client
    await zmq_client.start()
    print("ZMQ client started")
    
    # Print stats periodically
    while running:
        try:
            print_stats()
            await asyncio.sleep(10)
        except asyncio.CancelledError:
            break
    
    # Clean shutdown
    print("Stopping ZMQ client...")
    await zmq_client.stop()
    await rpc_client.close()
    print("ZMQ client stopped")

if __name__ == "__main__":
    asyncio.run(main()) 