#!/usr/bin/env python3
"""
WebSocket Simulator for Evrmore Blockchain

This script simulates a WebSocket server that generates fake blockchain events
for testing WebSocket clients without requiring a real Evrmore node.
"""

import asyncio
import json
import logging
import random
import signal
import string
import sys
import time
from datetime import datetime
from typing import Dict, List, Any, Optional, Set

import websockets
from websockets.server import WebSocketServerProtocol
from pydantic import BaseModel

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("websocket-simulator")

# Global state
connected_clients: Set[WebSocketServerProtocol] = set()
subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {
    "blocks": set(),
    "transactions": set(),
    "sequence": set(),
}

# Simulation settings
BLOCK_INTERVAL = 60  # seconds between blocks
TX_INTERVAL = 2      # seconds between transactions
SEQUENCE_INTERVAL = 10  # seconds between sequence updates

# Blockchain state
current_block_height = 100000
current_sequence = 1000000

class WebSocketSubscription(BaseModel):
    """Model for WebSocket subscription requests."""
    action: str
    topic: str

class WebSocketMessage(BaseModel):
    """Model for WebSocket messages."""
    type: str
    data: Any

def generate_hash() -> str:
    """Generate a random hash."""
    return ''.join(random.choices(string.hexdigits.lower(), k=64))

def generate_block() -> Dict[str, Any]:
    """Generate a fake block."""
    global current_block_height
    current_block_height += 1
    
    # Generate random transactions
    num_txs = random.randint(1, 20)
    txs = [generate_hash() for _ in range(num_txs)]
    
    # Generate block data
    block = {
        "hash": generate_hash(),
        "height": current_block_height,
        "time": int(time.time()),
        "tx": txs,
        "size": random.randint(1000, 10000),
        "weight": random.randint(4000, 40000),
        "version": 536870912,
        "merkleroot": generate_hash(),
        "nonce": random.randint(0, 2**32 - 1),
        "bits": "1d00ffff",
        "difficulty": random.uniform(1.0, 10.0),
        "chainwork": "0000000000000000000000000000000000000000000000000000000000123456",
        "previousblockhash": generate_hash(),
        "nextblockhash": None
    }
    
    return block

def generate_transaction() -> Dict[str, Any]:
    """Generate a fake transaction."""
    # Generate random inputs
    num_inputs = random.randint(1, 5)
    inputs = []
    for _ in range(num_inputs):
        inputs.append({
            "txid": generate_hash(),
            "vout": random.randint(0, 5),
            "scriptSig": {
                "asm": "asm_script",
                "hex": "hex_script"
            },
            "sequence": random.randint(0, 2**32 - 1)
        })
    
    # Generate random outputs
    num_outputs = random.randint(1, 5)
    outputs = []
    for i in range(num_outputs):
        outputs.append({
            "value": random.uniform(0.1, 100.0),
            "n": i,
            "scriptPubKey": {
                "asm": "asm_script",
                "hex": "hex_script",
                "reqSigs": 1,
                "type": "pubkeyhash",
                "addresses": ["E" + ''.join(random.choices(string.ascii_letters + string.digits, k=33))]
            }
        })
    
    # Generate transaction data
    tx = {
        "txid": generate_hash(),
        "hash": generate_hash(),
        "size": random.randint(200, 1000),
        "vsize": random.randint(200, 1000),
        "version": 1,
        "locktime": 0,
        "vin": inputs,
        "vout": outputs,
        "hex": "raw_transaction_hex",
        "blockhash": generate_hash(),
        "confirmations": random.randint(0, 10),
        "time": int(time.time()),
        "blocktime": int(time.time())
    }
    
    return tx

def generate_sequence() -> Dict[str, Any]:
    """Generate a fake sequence update."""
    global current_sequence
    current_sequence += 1
    
    return {
        "sequence": current_sequence,
        "hash": generate_hash()
    }

async def broadcast(topic: str, data: Any) -> None:
    """Broadcast a message to all subscribed clients."""
    if topic not in subscriptions:
        return
    
    message = WebSocketMessage(type=topic.rstrip("s"), data=data)
    message_json = message.model_dump_json()
    
    disconnected_clients = set()
    for client in subscriptions[topic]:
        try:
            await client.send(message_json)
        except websockets.exceptions.ConnectionClosed:
            disconnected_clients.add(client)
    
    # Remove disconnected clients
    for client in disconnected_clients:
        if client in connected_clients:
            connected_clients.remove(client)
        for topic_clients in subscriptions.values():
            if client in topic_clients:
                topic_clients.remove(client)

async def handle_client(websocket: WebSocketServerProtocol, path: str) -> None:
    """Handle a WebSocket client connection."""
    connected_clients.add(websocket)
    client_id = id(websocket)
    client_address = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
    logger.info(f"Client connected: {client_address} (ID: {client_id})")
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                subscription = WebSocketSubscription(**data)
                
                if subscription.action == "subscribe":
                    if subscription.topic in subscriptions:
                        subscriptions[subscription.topic].add(websocket)
                        logger.info(f"Client {client_id} subscribed to {subscription.topic}")
                        
                        # Send confirmation
                        await websocket.send(json.dumps({
                            "type": "subscription",
                            "data": {
                                "status": "success",
                                "topic": subscription.topic,
                                "action": "subscribe"
                            }
                        }))
                    else:
                        # Send error for invalid topic
                        await websocket.send(json.dumps({
                            "type": "error",
                            "data": {
                                "code": 1001,
                                "message": f"Invalid topic: {subscription.topic}"
                            }
                        }))
                
                elif subscription.action == "unsubscribe":
                    if subscription.topic in subscriptions and websocket in subscriptions[subscription.topic]:
                        subscriptions[subscription.topic].remove(websocket)
                        logger.info(f"Client {client_id} unsubscribed from {subscription.topic}")
                        
                        # Send confirmation
                        await websocket.send(json.dumps({
                            "type": "subscription",
                            "data": {
                                "status": "success",
                                "topic": subscription.topic,
                                "action": "unsubscribe"
                            }
                        }))
                    else:
                        # Send error for invalid topic or not subscribed
                        await websocket.send(json.dumps({
                            "type": "error",
                            "data": {
                                "code": 1002,
                                "message": f"Not subscribed to topic: {subscription.topic}"
                            }
                        }))
                
                else:
                    # Send error for invalid action
                    await websocket.send(json.dumps({
                        "type": "error",
                        "data": {
                            "code": 1003,
                            "message": f"Invalid action: {subscription.action}"
                        }
                    }))
            
            except json.JSONDecodeError:
                # Send error for invalid JSON
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {
                        "code": 1004,
                        "message": "Invalid JSON"
                    }
                }))
            except Exception as e:
                # Send error for other exceptions
                await websocket.send(json.dumps({
                    "type": "error",
                    "data": {
                        "code": 1005,
                        "message": f"Error: {str(e)}"
                    }
                }))
    
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client disconnected: {client_address} (ID: {client_id})")
    finally:
        # Clean up when client disconnects
        if websocket in connected_clients:
            connected_clients.remove(websocket)
        for topic_clients in subscriptions.values():
            if websocket in topic_clients:
                topic_clients.remove(websocket)

async def simulate_blocks() -> None:
    """Simulate block generation."""
    while True:
        await asyncio.sleep(BLOCK_INTERVAL)
        if not subscriptions["blocks"]:
            continue
        
        block = generate_block()
        logger.info(f"Generated block: {block['hash'][:10]}... (height: {block['height']})")
        await broadcast("blocks", block)

async def simulate_transactions() -> None:
    """Simulate transaction generation."""
    while True:
        await asyncio.sleep(TX_INTERVAL)
        if not subscriptions["transactions"]:
            continue
        
        tx = generate_transaction()
        logger.info(f"Generated transaction: {tx['txid'][:10]}...")
        await broadcast("transactions", tx)

async def simulate_sequences() -> None:
    """Simulate sequence updates."""
    while True:
        await asyncio.sleep(SEQUENCE_INTERVAL)
        if not subscriptions["sequence"]:
            continue
        
        sequence = generate_sequence()
        logger.info(f"Generated sequence: {sequence['sequence']}")
        await broadcast("sequence", sequence)

async def main() -> None:
    """Run the WebSocket simulator."""
    # Start the WebSocket server
    host = "localhost"
    port = 8765
    
    # Create the server
    server = await websockets.serve(
        handle_client,
        host,
        port,
        ping_interval=30,
        ping_timeout=10,
        close_timeout=10,
        max_size=2**20,  # 1MB
    )
    
    logger.info(f"WebSocket simulator started on ws://{host}:{port}")
    logger.info("Press Ctrl+C to stop the server")
    
    # Start simulation tasks
    block_task = asyncio.create_task(simulate_blocks())
    tx_task = asyncio.create_task(simulate_transactions())
    sequence_task = asyncio.create_task(simulate_sequences())
    
    # Keep the server running until interrupted
    try:
        await asyncio.Future()  # Run forever
    finally:
        # Cancel simulation tasks
        block_task.cancel()
        tx_task.cancel()
        sequence_task.cancel()
        
        # Close the server
        server.close()
        await server.wait_closed()
        logger.info("WebSocket simulator stopped")

if __name__ == "__main__":
    # Set up signal handlers for clean shutdown
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: loop.stop())
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    finally:
        loop.close()
        logger.info("WebSocket simulator stopped")