# Evrmore RPC Documentation

Welcome to the documentation for the `evrmore-rpc` package, a comprehensive, typed Python wrapper for the Evrmore blockchain with ZMQ and WebSockets support.

## Overview

The `evrmore-rpc` package provides a clean, typed interface to interact with the Evrmore blockchain. It supports:

- Synchronous RPC calls via `EvrmoreClient`
- Asynchronous RPC calls via `EvrmoreAsyncRPCClient`
- Real-time blockchain notifications via ZMQ with `EvrmoreZMQClient`
- WebSockets support for real-time updates with `EvrmoreWebSocketClient` and `EvrmoreWebSocketServer`

## Installation

### Basic Installation

```bash
pip install evrmore-rpc
```

### With WebSockets Support

```bash
pip install evrmore-rpc[websockets]
```

### Full Installation (including development tools)

```bash
pip install evrmore-rpc[full]
```

## Quick Start

### Synchronous API

```python
from evrmore_rpc import EvrmoreClient

# Create a client
client = EvrmoreClient(
    rpcuser="user",
    rpcpassword="password",
    rpchost="localhost",
    rpcport=8819,
)

# Get blockchain info
info = client.getblockchaininfo()
print(f"Current block height: {info.blocks}")
print(f"Chain: {info.chain}")
print(f"Difficulty: {info.difficulty}")

# Get a block
block_hash = client.getblockhash(1)
block = client.getblock(block_hash)
print(f"Block #1 hash: {block.hash}")
print(f"Block #1 time: {block.time}")
print(f"Block #1 transactions: {len(block.tx)}")

# List assets
assets = client.listassets()
print(f"Found {len(assets)} assets")
```

### Asynchronous API

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

async def main():
    # Create a client
    async with EvrmoreAsyncRPCClient() as client:
        # Get blockchain info and block in parallel
        info, block_hash = await asyncio.gather(
            client.getblockchaininfo(),
            client.getblockhash(1)
        )
        
        # Get block details
        block = await client.getblock(block_hash)
        
        # Print results
        print(f"Current block height: {info.blocks}")
        print(f"Block #1 hash: {block.hash}")
        print(f"Block #1 transactions: {len(block.tx)}")

if __name__ == "__main__":
    asyncio.run(main())
```

### ZMQ Notifications

```python
import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient

async def handle_block(notification):
    print(f"New block: {notification.hex}")

async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

async def main():
    # Create a ZMQ client
    client = EvrmoreZMQClient(
        host="localhost",
        port=28332,
    )
    
    # Register handlers
    client.on_block(handle_block)
    client.on_transaction(handle_transaction)
    
    # Start the client
    await client.start()
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await client.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

### WebSockets

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Create a WebSocket client
    client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
    
    # Connect to the WebSocket server
    await client.connect()
    
    # Subscribe to block and transaction notifications
    await client.subscribe("blocks")
    await client.subscribe("transactions")
    
    # Process incoming messages
    async for message in client:
        if message.type == "block":
            block_data = message.data
            print(f"New block: {block_data.hash} (height: {block_data.height})")
            
        elif message.type == "transaction":
            tx_data = message.data
            print(f"New transaction: {tx_data.txid}")
    
    # Disconnect
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
```

## Command Line Interface

The `evrmore-rpc` package provides a command-line interface for executing RPC commands directly from the terminal.

```bash
# Get blockchain info
evrmore-rpc getblockchaininfo

# Get a block by height
evrmore-rpc getblockhash 100 | evrmore-rpc getblock -

# List assets
evrmore-rpc listassets

# Start interactive mode
evrmore-rpc -i
```

### Configuration

You can configure the CLI using command-line options or environment variables:

```bash
# Using command-line options
evrmore-rpc --rpcuser=user --rpcpassword=password getblockchaininfo

# Using environment variables
export EVRMORE_RPC_USER=user
export EVRMORE_RPC_PASSWORD=password
evrmore-rpc getblockchaininfo
```

### Interactive Mode

The CLI also supports an interactive mode for executing multiple commands:

```bash
evrmore-rpc -i
> getblockchaininfo
> getblockhash 100
> getblock <result_from_previous_command>
> exit
```

## Documentation

- [Synchronous API](sync_api.md)
- [Asynchronous API](async_api.md)
- [ZMQ Support](zmq.md)
- [WebSockets Support](websockets.md)
- [Models](models.md)
- [Examples](examples.md)
- [Advanced Usage](advanced.md)

## Examples

The `evrmore-rpc` package includes several examples demonstrating its functionality:

- Basic RPC usage
- Asynchronous RPC usage
- ZMQ notifications
- WebSockets support
- Balance tracker for NFT exchange integration
- Interactive dashboards
- Blockchain analytics

See the [examples directory](https://github.com/ManticoreTechnology/evrmore-rpc/tree/main/examples) for more information.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/ManticoreTechnology/evrmore-rpc/blob/main/LICENSE) file for details.