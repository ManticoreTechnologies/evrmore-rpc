#!/usr/bin/env python3
"""
Super Simple Example

This example demonstrates the core functionality of the seamless API:
- No context managers needed
- No explicit mode setting needed
- Same client works with or without await
"""

import asyncio
from evrmore_rpc import EvrmoreClient

# Create a single client instance
client = EvrmoreClient()

def sync_example():
    """Synchronous example"""
    # Just call methods directly - no 'with' needed
    info = client.getblockchaininfo()
    print(f"Sync - Chain: {info['chain']}, Blocks: {info['blocks']}")

async def async_example():
    """Asynchronous example"""
    # Just await methods directly - no 'async with' needed
    info = await client.getblockchaininfo()
    print(f"Async - Chain: {info['chain']}, Blocks: {info['blocks']}")

async def main():
    """Run both examples with the same client instance"""
    # Run sync example
    sync_example()
    
    # Reset client state before async usage
    client.reset()
    
    # Run async example
    await async_example()
    
    # Clean up resources when done
    await client.close()
    print("Client closed")

if __name__ == "__main__":
    asyncio.run(main()) 