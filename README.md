# evrmore-rpc

A high-performance Python wrapper for Evrmore blockchain RPC commands, supporting both synchronous and asynchronous usage with a seamless API.

## Features

- **Seamless API**: Use the same client for both synchronous and asynchronous code without context managers
- **High-Performance Direct RPC**: Communicates directly with the Evrmore daemon over HTTP JSON-RPC
- **Automatic Configuration**: Automatically reads and parses `evrmore.conf` for connection details
- **Enhanced Auto-Detection**: Client automatically detects whether it's being used in a synchronous or asynchronous context
- **Connection Pooling**: Maintains persistent connections for better performance
- **Type Hints**: Comprehensive type annotations for better IDE support
- **Pydantic Models**: Response models for common RPC commands
- **Integrated Stress Testing**: Built-in performance testing tools
- **Concurrency**: Easily make concurrent RPC calls for maximum throughput

## Installation

```bash
pip install evrmore-rpc
```

## Quick Start

### Seamless API (Recommended)

```python
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

if __name__ == "__main__":
    asyncio.run(main())
```

## Auto-Detection

The client automatically detects whether it's being used in a synchronous or asynchronous context:

```python
import asyncio
from evrmore_rpc import EvrmoreClient

# Create a single client instance
client = EvrmoreClient()

# Use synchronously
def sync_function():
    info = client.getblockchaininfo()  # Runs synchronously
    print(f"Chain: {info['chain']}")

# Use asynchronously
async def async_function():
    # Reset client state when switching between sync and async
    client.reset()
    
    info = await client.getblockchaininfo()  # Runs asynchronously
    print(f"Chain: {info['chain']}")

# Run both with the same client instance
async def main():
    sync_function()
    await async_function()
    await client.close()  # Clean up when done

asyncio.run(main())
```

### Forcing Sync or Async Mode

You can also explicitly set the mode if needed:

```python
# Force synchronous mode
client = EvrmoreClient().force_sync()
info = client.getblockchaininfo()  # Always runs synchronously

# Force asynchronous mode
client = EvrmoreClient().force_async()
info = await client.getblockchaininfo()  # Always runs asynchronously

# Reset to auto-detect mode
client.reset()
```

## Configuration Options

```python
from evrmore_rpc import EvrmoreClient

# Explicit configuration
client = EvrmoreClient(
    url="http://username:password@localhost:8819/",  # Full RPC URL with credentials
    datadir="/path/to/evrmore",                      # Custom data directory
    rpcuser="username",                              # RPC username
    rpcpassword="password",                          # RPC password
    rpcport=8819,                                    # RPC port
    testnet=False,                                   # Use testnet
    timeout=30                                       # Request timeout in seconds
)

# Use the client
info = client.getblockchaininfo()
print(f"Chain: {info['chain']}")

# Clean up when done
client.close_sync()  # For sync usage
# or
await client.close()  # For async usage
```

## Performance Testing

The library includes built-in stress testing tools that work in both sync and async modes:

```bash
# Run auto-detected stress test
python -m evrmore_rpc.stress_test

# Run with custom parameters
python -m evrmore_rpc.stress_test --num-calls 1000 --command getbestblockhash --concurrency 20
```

You can also run stress tests programmatically:

```python
import asyncio
from evrmore_rpc import EvrmoreClient

async def main():
    client = EvrmoreClient()
    
    try:
        # Run stress test
        results = await client.stress_test(num_calls=100, command="getblockcount", concurrency=20)
        print(f"Requests per second: {results['requests_per_second']}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Response Models

The library includes Pydantic models for common RPC responses:

```python
import asyncio
from evrmore_rpc import EvrmoreClient, BlockchainInfo

async def main():
    client = EvrmoreClient()
    
    try:
        # Get typed response
        info_dict = await client.getblockchaininfo()
        info = BlockchainInfo.model_validate(info_dict)
        print(f"Chain: {info.chain}")
        print(f"Blocks: {info.blocks}")
    finally:
        await client.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## License

MIT License - See LICENSE file for details