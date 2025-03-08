#!/usr/bin/env python3
"""
Simple Evrmore ZMQ Example

This minimal example shows how to use the ZMQ client to receive blockchain notifications.
It focuses on the core functionality without additional features.
"""

import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc.zmq.models import ZMQNotification
from evrmore_rpc import EvrmoreClient

async def main():
    # Create a ZMQ client with default settings
    zmq_client = EvrmoreZMQClient()
    
    # Create an RPC client for additional queries
    # Make sure to force async mode since we're in an async context
    rpc_client = EvrmoreClient()
    rpc_client.force_async()
    
    # Register a handler for new blocks
    @zmq_client.on(ZMQTopic.HASH_BLOCK)
    async def on_new_block(notification: ZMQNotification):
        print(f"New block received: {notification.hex}")
        
        # Example of using RPC client with ZMQ
        try:
            # Get block info
            block = await rpc_client.getblock(notification.hex)
            print(f"Block height: {block['height']}, txs: {len(block['tx'])}")
        except Exception as e:
            print(f"Error getting block info: {e}")
    
    # Register a handler for new transactions
    @zmq_client.on(ZMQTopic.HASH_TX)
    async def on_new_transaction(notification: ZMQNotification):
        print(f"New transaction received: {notification.hex}")
    
    # Start the ZMQ client
    print("Starting ZMQ client...")
    await zmq_client.start()
    print("ZMQ client started. Press Ctrl+C to exit.")
    
    try:
        # Run indefinitely
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down...")
    finally:
        # Clean up resources
        await zmq_client.stop()
        await rpc_client.close()
        print("ZMQ client and RPC client stopped.")

if __name__ == "__main__":
    asyncio.run(main()) 