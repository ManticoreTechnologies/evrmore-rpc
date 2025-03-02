#!/usr/bin/env python3
"""
Simple example demonstrating the auto-detection feature of the EvrmoreClient.
This example shows how to use the client both with and without context managers.
"""

import asyncio
from evrmore_rpc import EvrmoreClient

def sync_example():
    """Run a synchronous example"""
    print("Running in synchronous context...")
    
    # Create a client without specifying async_mode
    # It will auto-detect that we're in a sync context
    client = EvrmoreClient()
    
    # Use with context manager for automatic cleanup
    with client:
        info = client.getblockchaininfo()
        block_hash = info['bestblockhash']
        block = client.getblock(block_hash)
        
        print(f"Chain: {info['chain']}")
        print(f"Blocks: {info['blocks']}")
        print(f"Block height: {block['height']}")

async def async_example():
    """Run an asynchronous example"""
    print("\nRunning in asynchronous context...")
    
    # Create a client without specifying async_mode
    # It will auto-detect that we're in an async context
    client = EvrmoreClient()
    
    try:
        # Initialize the client (this happens automatically on first command)
        await client.initialize_async()
        
        # This will run asynchronously
        info = await client.getblockchaininfo()
        print(f"Chain: {info['chain']}")
        print(f"Blocks: {info['blocks']}")
        
        # Get a block
        block_hash = info['bestblockhash']
        block = await client.getblock(block_hash)
        print(f"Block height: {block['height']}")
    finally:
        # Explicitly close the client when done
        await client.close()

async def async_example_with_context():
    """Run an asynchronous example using context manager"""
    print("\nRunning in asynchronous context with context manager...")
    
    # Create a client without specifying async_mode
    # It will auto-detect that we're in an async context
    client = EvrmoreClient()
    
    # Use async with context manager for automatic cleanup
    async with client:
        # This will run asynchronously
        info = await client.getblockchaininfo()
        print(f"Chain: {info['chain']}")
        print(f"Blocks: {info['blocks']}")
        
        # Get a block
        block_hash = info['bestblockhash']
        block = await client.getblock(block_hash)
        print(f"Block height: {block['height']}")

def main():
    """Run all examples"""
    # Run synchronous example
    sync_example()
    
    # Run asynchronous example without context manager
    asyncio.run(async_example())
    
    # Run asynchronous example with context manager
    asyncio.run(async_example_with_context())
    
    print("\nAll examples completed successfully!")

if __name__ == "__main__":
    main() 