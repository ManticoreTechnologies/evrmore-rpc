# Evrmore WebSockets Examples

This directory contains examples demonstrating how to use the WebSockets functionality in the Evrmore RPC library.

## Overview

The Evrmore RPC library provides WebSockets support for real-time blockchain event notifications. This allows applications to receive immediate updates when new blocks are mined or new transactions are added to the mempool.

## Examples

### Simple Client (`simple_client.py`)

A basic example showing how to connect to a WebSocket server, subscribe to blockchain events, and process incoming messages.

```bash
python simple_client.py
```

### WebSocket Client Example (`websocket_client_example.py`)

A more comprehensive example demonstrating various features of the WebSocket client, including:
- Connecting to a WebSocket server
- Subscribing to multiple topics
- Handling different message types
- Graceful error handling and reconnection

```bash
python websocket_client_example.py
```

### WebSocket Simulator (`websocket_simulator.py`)

A simulator that creates a WebSocket server without requiring an actual Evrmore node. Useful for testing and development.

```bash
python websocket_simulator.py
```

### Interactive Dashboard (`interactive_dashboard.py`)

An interactive dashboard that displays real-time blockchain data using the WebSocket client.

```bash
python interactive_dashboard.py
```

## Setting Up a WebSocket Server

To use these examples, you need a WebSocket server that broadcasts Evrmore blockchain events. You can:

1. Use the `EvrmoreWebSocketServer` class provided by the library:

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient
from evrmore_rpc.websockets.server import EvrmoreWebSocketServer

async def main():
    # Initialize RPC client
    rpc = EvrmoreAsyncRPCClient()
    
    # Initialize ZMQ client
    zmq = EvrmoreZMQClient()
    
    # Initialize WebSocket server
    server = EvrmoreWebSocketServer(
        rpc_client=rpc,
        zmq_client=zmq,
        host="localhost",
        port=8820
    )
    
    # Start the server
    await server.start()
    
asyncio.run(main())
```

2. Or use the WebSocket simulator for testing:

```bash
python websocket_simulator.py
```

## WebSocket Client API

The `EvrmoreWebSocketClient` class provides the following key methods:

- `connect()`: Connect to the WebSocket server
- `disconnect()`: Disconnect from the server
- `subscribe(topic)`: Subscribe to a topic (e.g., "blocks", "transactions")
- `unsubscribe(topic)`: Unsubscribe from a topic

The client can be used as an async iterator to process incoming messages:

```python
async with EvrmoreWebSocketClient("ws://localhost:8820") as client:
    await client.subscribe("blocks")
    
    async for message in client:
        if message.type == "block":
            print(f"New block: {message.data.hash}")
```

## Message Types

The WebSocket API supports the following message types:

- `block`: New block notifications
- `transaction`: New transaction notifications
- `sequence`: Sequence notifications for synchronization
- `error`: Error messages

Each message type has a corresponding data model with specific fields.

## Error Handling

The WebSocket client includes robust error handling:

- Automatic reconnection on connection loss
- Graceful handling of server errors
- Timeout handling for unresponsive servers

## Requirements

- Python 3.8 or higher
- websockets library
- rich library (for some examples)
- An Evrmore node with ZMQ enabled (for the server)

## Prerequisites

To run these examples, you need to install the WebSockets dependencies:

```bash
pip install evrmore-rpc[websockets]
```

Or install the full package with all dependencies:

```bash
pip install evrmore-rpc[full]
```

You also need a running Evrmore node with ZMQ enabled. Add the following to your `evrmore.conf` file:

```
# ZMQ notifications
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubsequence=tcp://127.0.0.1:28332
```

## WebSocket Topics

The WebSocket server supports the following subscription topics:

- `blocks`: Notifications about new blocks
- `transactions`: Notifications about new transactions
- `sequence`: Notifications about sequence updates

## Message Format

WebSocket messages have the following format:

```json
{
  "type": "block|transaction|sequence|error",
  "data": {
    // Message-specific data
  }
}
```

### Block Message

```json
{
  "type": "block",
  "data": {
    "hash": "block_hash",
    "height": 123456,
    "time": 1234567890,
    "tx": ["txid1", "txid2", ...],
    "size": 1234,
    "weight": 4936,
    "version": 536870912,
    "merkleroot": "merkle_root_hash",
    "nonce": 1234567890,
    "bits": "1d00ffff",
    "difficulty": 1.23456789,
    "chainwork": "0000000000000000000000000000000000000000000000000000000000123456",
    "previousblockhash": "previous_block_hash",
    "nextblockhash": "next_block_hash"
  }
}
```

### Transaction Message

```json
{
  "type": "transaction",
  "data": {
    "txid": "transaction_id",
    "hash": "transaction_hash",
    "size": 225,
    "vsize": 225,
    "version": 1,
    "locktime": 0,
    "vin": [...],
    "vout": [...],
    "hex": "raw_transaction_hex",
    "blockhash": "block_hash",
    "confirmations": 1,
    "time": 1234567890,
    "blocktime": 1234567890
  }
}
```

### Sequence Message

```json
{
  "type": "sequence",
  "data": {
    "sequence": 123456,
    "hash": "sequence_hash"
  }
}
```

### Error Message

```json
{
  "type": "error",
  "data": {
    "code": 1001,
    "message": "Error message"
  }
}
``` 