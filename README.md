# Evrmore RPC Client

A Python client for interacting with the Evrmore blockchain via RPC. This library supports both synchronous and asynchronous usage patterns with the same clean API.

## Features

- **Seamless API**: Works identically in both synchronous and asynchronous contexts
- **Auto-detection**: Automatically detects sync/async context without manual configuration
- **Type Safety**: Comprehensive type hints and Pydantic models for better IDE integration
- **Performance**: Optimized for high-performance with connection pooling and efficient request handling
- **Error Handling**: Clear and informative error messages with proper exception handling
- **Full API Coverage**: Support for all Evrmore RPC commands with proper parameter typing
- **Data Models**: Pydantic models for structured, validated responses
- **ZMQ Support**: Asynchronous ZMQ interface for real-time blockchain notifications
- **Configuration**: Automatic configuration from evrmore.conf or environment variables

## Installation

```bash
pip3 install evrmore-rpc
```

## Quick Start

```python
from evrmore_rpc import EvrmoreClient

# Create a client (auto-configures from evrmore.conf or environment variables)
client = EvrmoreClient()

# Use synchronously
info = client.getblockchaininfo()
print(f"Chain: {info.chain}, Blocks: {info.blocks}")

# Use asynchronously
import asyncio

async def main():
    # Same client works in async context
    info = await client.getblockchaininfo()
    print(f"Chain: {info.chain}, Blocks: {info.blocks}")
    
    # Clean up resources when done
    await client.close()

asyncio.run(main())
```

## Client Configuration

The client can be configured in multiple ways:

```python
# Using constructor parameters
client = EvrmoreClient(
    rpcuser="your_username",
    rpcpassword="your_password",
    rpchost="localhost",
    rpcport=8819,  # Mainnet default
    testnet=False,
    timeout=30
)

# Using environment variables:
# - EVRMORE_RPC_USER
# - EVRMORE_RPC_PASSWORD
# - EVRMORE_RPC_HOST
# - EVRMORE_RPC_PORT
# - EVRMORE_TESTNET (set to "1" for testnet)

# Using evrmore.conf
# The client automatically reads evrmore.conf from the default location:
# - Linux: ~/.evrmore/evrmore.conf
# - macOS: ~/Library/Application Support/Evrmore/evrmore.conf
# - Windows: %APPDATA%\Evrmore\evrmore.conf
```

## Connection Management

The client handles connections automatically, but you can also manage them explicitly:

```python
# Using context managers (recommended)
with EvrmoreClient() as client:
    # Connection is automatically established
    info = client.getblockchaininfo()
    # Connection is automatically closed

# Async context manager
async with EvrmoreClient() as client:
    info = await client.getblockchaininfo()
    # Connection is automatically closed

# Explicit connection management
client = EvrmoreClient()
# For sync
client.initialize_sync()
# ... use client ...
client.close_sync()

# For async
await client.initialize_async()
# ... use client ...
await client.close()
```

## Data Models

The library includes Pydantic models for structured, validated responses:

```python
from evrmore_rpc import EvrmoreClient, BlockchainInfo, Block, AssetInfo

client = EvrmoreClient()

# Response is automatically validated and converted to proper model
info: BlockchainInfo = client.getblockchaininfo()
print(f"Chain: {info.chain}")
print(f"Difficulty: {info.difficulty}")

# Models include proper typing
block: Block = client.getblock("000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f", 2)
for tx in block.tx:
    print(f"Transaction: {tx.txid}")

# Asset models
asset: AssetInfo = client.getassetdata("ASSET_NAME")
print(f"Asset: {asset.name}, Supply: {asset.amount}")
```

## ZMQ Interface

The library provides a clean interface for ZMQ notifications from the Evrmore blockchain:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc import EvrmoreClient

# Create an RPC client for additional queries
# Important: Force async mode for use with ZMQ
rpc_client = EvrmoreClient()
rpc_client.force_async()

# Create a ZMQ client
zmq_client = EvrmoreZMQClient(
    zmq_host="127.0.0.1",
    zmq_port=28332
)

# Register handlers with decorators
@zmq_client.on(ZMQTopic.HASH_BLOCK)
async def handle_block(notification):
    print(f"New block: {notification.hex}")
    
    # Use RPC client to get more information
    try:
        block_data = await rpc_client.getblock(notification.hex)
        print(f"Block height: {block_data['height']}")
    except Exception as e:
        print(f"Error getting block details: {e}")

@zmq_client.on(ZMQTopic.HASH_TX)
async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

# Start the client
await zmq_client.start()

# Run indefinitely
try:
    await asyncio.Future()  # Never completes
except asyncio.CancelledError:
    pass

# Clean shutdown - stop both clients
await zmq_client.stop()
await rpc_client.close()
```

### ZMQ Configuration

To use ZMQ notifications, your Evrmore node must be configured with ZMQ support. Add these lines to your `evrmore.conf` file:

```
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28332
```

### Available Notification Types

- `ZMQTopic.HASH_BLOCK`: Lightweight notification of new blocks (just the block hash)
- `ZMQTopic.HASH_TX`: Lightweight notification of new transactions (just the transaction hash)
- `ZMQTopic.RAW_BLOCK`: Complete serialized block data
- `ZMQTopic.RAW_TX`: Complete serialized transaction data

### Best Practices for ZMQ

1. **Always force async mode** for the RPC client when using with ZMQ
2. **Always use await** on all RPC methods in ZMQ handlers
3. **Properly clean up resources** by stopping the ZMQ client and closing the RPC client
4. **Handle exceptions** in your notification handlers to prevent crashes

## Advanced Usage

### Stress Testing

The library includes built-in stress testing capabilities:

```python
from evrmore_rpc import EvrmoreClient, stress_test

client = EvrmoreClient()

# Run stress test
results = stress_test(
    num_calls=100,
    command="getblockcount",
    concurrency=10
)

print(f"Average time: {results['avg_time']} ms")
print(f"Requests per second: {results['requests_per_second']}")
```

### Custom RPC Commands

You can call any RPC command, even custom ones:

```python
# Call any RPC command directly
result = client.execute_command("customcommand", arg1, arg2)

# For async
result = await client.execute_command_async("customcommand", arg1, arg2)
```

## Examples

The repository includes several examples demonstrating various aspects of the library:

### Basic Examples
- `super_simple.py`: The simplest demonstration of the seamless API
- `seamless_api.py`: More comprehensive example of the seamless API
- `simple_auto_detect.py`: Demonstrates auto-detection of sync/async context

### Advanced Examples
- `asset_monitor`: Real-time tracking of asset creation and transfers
- `blockchain_explorer`: Simple blockchain explorer implementation
- `network_monitor`: Monitor network health and peer connections
- `wallet_tracker`: Track wallet balances and transactions
- `asset_swap`: Simple asset swap implementation
- `balance_tracker`: Track address balances in real-time
- `reward_distributor`: Distribute mining rewards automatically

## License

This project is licensed under the MIT License - see the LICENSE file for details.