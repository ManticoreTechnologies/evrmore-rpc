#!/usr/bin/env python3
"""
Simple stress test for the EvrmoreClient

This test demonstrates the seamless API by using the same client
for both synchronous and asynchronous calls.
"""

import asyncio
import time
from evrmore_rpc import EvrmoreClient

# Create a single client instance
client = EvrmoreClient()

def run_sync_test():
    """Run a simple synchronous test"""
    start = time.time()
    result = client.getblockcount()
    elapsed = (time.time() - start) * 1000
    print(f"Sync - Block count: {result}")
    print(f"Sync - Time taken: {elapsed:.2f} ms")
    return result

async def run_async_test():
    """Run a simple asynchronous test"""
    start = time.time()
    result = await client.getblockcount()
    elapsed = (time.time() - start) * 1000
    print(f"Async - Block count: {result}")
    print(f"Async - Time taken: {elapsed:.2f} ms")
    return result

async def main():
    """Run both sync and async tests"""
    print("Running stress test...")
    
    # Run sync test
    sync_result = run_sync_test()
    
    # Reset client state before async usage
    client.reset()
    
    # Run async test
    async_result = await run_async_test()
    
    # Verify results match
    assert sync_result == async_result, "Sync and async results don't match!"
    
    # Clean up resources
    await client.close()
    print("Test completed successfully!")

if __name__ == "__main__":
    asyncio.run(main()) 