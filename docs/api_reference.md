# API Reference

This page documents the main classes and methods of the Evrmore RPC library.

## Overview

The Evrmore RPC library provides a comprehensive API for interacting with the Evrmore blockchain. The main components are:

- **Synchronous API**: For standard synchronous programming
- **Asynchronous API**: For async/await programming model
- **ZMQ Support**: For real-time blockchain notifications
- **WebSockets Support**: For real-time web applications
- **Models**: Type-safe data structures for blockchain data

## Main Classes

The library provides several client classes to interact with the Evrmore blockchain:

| Class | Description | Import Path |
|-------|-------------|-------------|
| `EvrmoreClient` | Main synchronous client | `from evrmore_rpc import EvrmoreClient` |
| `EvrmoreAsyncRPCClient` | Asynchronous RPC client | `from evrmore_rpc import EvrmoreAsyncRPCClient` |
| `EvrmoreZMQClient` | ZMQ notifications client | `from evrmore_rpc.zmq import EvrmoreZMQClient` |
| `EvrmoreWebSocketClient` | WebSocket client | `from evrmore_rpc.websockets import EvrmoreWebSocketClient` |
| `EvrmoreWebSocketServer` | WebSocket server | `from evrmore_rpc.websockets import EvrmoreWebSocketServer` |

## Quick Example

```python
from evrmore_rpc import EvrmoreClient

# Create a client
client = EvrmoreClient()

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
```

## API Design

The API is designed with several key principles in mind:

1. **Type Safety**: All methods and responses are fully typed with proper type hints.
2. **Consistency**: Methods follow a consistent naming and parameter pattern.
3. **Pythonic**: API feels natural to Python developers.
4. **Performance**: Optimized for efficient blockchain interactions.

## Further Reading

Explore the specific sections for more detailed information:

- [Synchronous API](sync_api.md): For traditional synchronous programming
- [Asynchronous API](async_api.md): For async/await programming model
- [ZMQ Support](zmq.md): For real-time blockchain notifications
- [WebSockets Support](websockets.md): For real-time web applications
- [Models](models.md): Type-safe data structures for blockchain data 