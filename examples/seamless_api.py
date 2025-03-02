#!/usr/bin/env python3
"""
Seamless API Example

This example demonstrates the seamless API of EvrmoreClient that works
in both synchronous and asynchronous contexts without requiring context
managers or explicit mode setting.

The same client instance can be used with or without await, and it will
automatically adapt to the context.
"""

import asyncio
import time
from evrmore_rpc import EvrmoreClient

def sync_function():
    """Demonstrate synchronous usage without context managers"""
    print("\n=== Synchronous Function ===")
    
    # Create a client - no context manager needed
    client = EvrmoreClient()
    
    try:
        # Call methods synchronously - no 'with' statement needed
        start = time.time()
        info = client.getblockchaininfo()
        elapsed = (time.time() - start) * 1000
        
        print(f"Chain: {info['chain']}")
        print(f"Blocks: {info['blocks']}")
        print(f"Time taken: {elapsed:.2f} ms")
        
        # Get a block
        block_hash = info['bestblockhash']
        block = client.getblock(block_hash)
        print(f"Block height: {block['height']}")
    finally:
        # Explicitly close the client when done (optional but recommended)
        client.close_sync()
        print("Client closed")

async def async_function():
    """Demonstrate asynchronous usage without context managers"""
    print("\n=== Asynchronous Function ===")
    
    # Create a client - no context manager needed
    client = EvrmoreClient()
    
    try:
        # Call methods asynchronously - no 'async with' statement needed
        start = time.time()
        info = await client.getblockchaininfo()
        elapsed = (time.time() - start) * 1000
        
        print(f"Chain: {info['chain']}")
        print(f"Blocks: {info['blocks']}")
        print(f"Time taken: {elapsed:.2f} ms")
        
        # Get a block
        block_hash = info['bestblockhash']
        block = await client.getblock(block_hash)
        print(f"Block height: {block['height']}")
    finally:
        # Explicitly close the client when done
        await client.close()
        print("Client closed")

async def mixed_function():
    """Demonstrate mixed sync/async usage with the same client instance"""
    print("\n=== Mixed Sync/Async Function ===")
    
    # Create a single client instance
    client = EvrmoreClient()
    
    try:
        # Use it synchronously in a thread by forcing sync mode
        loop = asyncio.get_running_loop()
        sync_info = await loop.run_in_executor(
            None, 
            lambda: client.force_sync().getblockchaininfo()
        )
        print(f"Sync call - Chain: {sync_info['chain']}")
        
        # Reset to auto-detect mode for async usage
        client._async_mode = None
        
        # Use it asynchronously directly
        async_info = await client.getblockchaininfo()
        print(f"Async call - Chain: {async_info['chain']}")
        
        # Both approaches work with the same client instance!
    finally:
        # Close the client when done
        await client.close()
        print("Client closed")

def main():
    """Run all examples"""
    print("Demonstrating the seamless EvrmoreClient API")
    
    # Run synchronous example
    sync_function()
    
    # Run asynchronous examples
    asyncio.run(async_function())
    
    # Run mixed example
    asyncio.run(mixed_function())
    
    print("\nAll examples completed successfully!")

if __name__ == "__main__":
    main() 