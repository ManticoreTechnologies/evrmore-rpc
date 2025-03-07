# Evrmore RPC Client

A Python client for interacting with the Evrmore blockchain via RPC.

## Features

- Seamless API that works in both synchronous and asynchronous contexts
- Automatic detection of sync/async context
- Comprehensive type hints for better IDE integration
- Support for all Evrmore RPC commands
- ZMQ support for real-time blockchain notifications

## Installation

```bash
pip install evrmore-rpc
```

## Basic Usage

```python
from evrmore_rpc import EvrmoreClient

# Create a client
client = EvrmoreClient()

# Use synchronously
info = client.getblockchaininfo()
print(f"Chain: {info['chain']}, Blocks: {info['blocks']}")

# Use asynchronously
import asyncio

async def main():
    info = await client.getblockchaininfo()
    print(f"Chain: {info['chain']}, Blocks: {info['blocks']}")
    
    # Clean up when done
    await client.close()

asyncio.run(main())
```

## Running Examples

The repository includes several examples demonstrating different aspects of the library. You can run them using the `run_examples.py` script:

```bash
# List available examples
python run_examples.py --list

# Run a basic example
python run_examples.py super_simple.py

# Run an advanced example
python run_examples.py asset_monitor/monitor.py
```

### Basic Examples

- `super_simple.py`: The simplest example showing the core functionality of the seamless API.
- `seamless_api.py`: A more comprehensive example demonstrating the seamless API in various scenarios.
- `simple_auto_detect.py`: Shows how the client automatically detects whether it's being used in a synchronous or asynchronous context.

### Advanced Examples

- `asset_monitor/monitor.py`: Real-time monitoring of asset creation and transfers.
- `blockchain_explorer/explorer.py`: Simple blockchain explorer implementation.
- `network_monitor/monitor.py`: Monitor network health and peer connections.
- `wallet_tracker/tracker.py`: Track wallet balances and transactions.
- `asset_swap/simple_swap.py`: Simple asset swap platform.

## Configuration

The client can be configured in several ways:

```python
# Using constructor parameters
client = EvrmoreClient(
    rpcuser="your_username",
    rpcpassword="your_password",
    rpchost="localhost",
    rpcport=8819,
)

# Using environment variables
# EVRMORE_RPC_USER, EVRMORE_RPC_PASSWORD, EVRMORE_RPC_HOST, EVRMORE_RPC_PORT

# Using evrmore.conf
# The client will automatically look for evrmore.conf in the default location
```

## ZMQ Support

The library includes support for ZMQ notifications from the Evrmore node:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

# Create a ZMQ client
zmq_client = EvrmoreZMQClient()

# Register handlers for different topics
@zmq_client.on(ZMQTopic.HASH_BLOCK)
async def handle_block(notification):
    print(f"New block: {notification.hex}")

@zmq_client.on(ZMQTopic.HASH_TX)
async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

# Start the client
await zmq_client.start()

# Stop the client when done
await zmq_client.stop()
```

## License

This project is licensed under the MIT License - see the LICENSE file for details.