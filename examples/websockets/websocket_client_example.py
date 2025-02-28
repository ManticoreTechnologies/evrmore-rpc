#!/usr/bin/env python3
"""
Example WebSocket client for Evrmore blockchain.

This script demonstrates how to use the EvrmoreWebSocketClient to subscribe to
real-time blockchain events like new blocks and transactions.
"""

import asyncio
import json
import logging
from typing import Dict, Any

from evrmore_rpc.websockets import EvrmoreWebSocketClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("websocket-client-example")

async def main():
    """Run the WebSocket client example."""
    # Create a WebSocket client
    client = EvrmoreWebSocketClient(
        uri="ws://localhost:8765",  # Default WebSocket server URI
        ping_interval=30,           # Send ping every 30 seconds
        reconnect_interval=5,       # Try to reconnect every 5 seconds if disconnected
        max_reconnect_attempts=10   # Maximum number of reconnection attempts
    )
    
    try:
        # Connect to the WebSocket server
        await client.connect()
        logger.info("Connected to WebSocket server")
        
        # Subscribe to block and transaction notifications
        await client.subscribe("blocks")
        await client.subscribe("transactions")
        
        logger.info("Subscribed to blocks and transactions")
        logger.info("Waiting for messages... (Press Ctrl+C to exit)")
        
        # Process incoming messages
        async for message in client:
            if message.type == "block":
                block_data = message.data
                logger.info(f"New block: {block_data.hash} (height: {block_data.height})")
                logger.info(f"  Transactions: {len(block_data.tx)}")
                logger.info(f"  Time: {block_data.time}")
                logger.info(f"  Size: {block_data.size} bytes")
                
            elif message.type == "transaction":
                tx_data = message.data
                logger.info(f"New transaction: {tx_data.txid}")
                logger.info(f"  Size: {tx_data.size} bytes")
                logger.info(f"  Inputs: {len(tx_data.vin)}")
                logger.info(f"  Outputs: {len(tx_data.vout)}")
                
            elif message.type == "error":
                logger.error(f"Error: {message.data.message} (code: {message.data.code})")
                
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received, shutting down...")
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        # Unsubscribe and disconnect
        try:
            await client.unsubscribe("blocks")
            await client.unsubscribe("transactions")
            await client.disconnect()
            logger.info("Disconnected from WebSocket server")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")

if __name__ == "__main__":
    asyncio.run(main()) 