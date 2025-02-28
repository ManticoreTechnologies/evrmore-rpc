# ZMQ Support

The `evrmore-rpc` package provides ZMQ (ZeroMQ) support for receiving real-time notifications from the Evrmore blockchain. This allows you to build applications that can react to new blocks, transactions, and other blockchain events as they happen.

## Installation

```bash
pip install evrmore-rpc
```

## Evrmore Node Configuration

To use ZMQ with Evrmore, you need to configure your Evrmore node to publish ZMQ notifications. Add the following to your `evrmore.conf` file:

```
# ZMQ notifications
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubsequence=tcp://127.0.0.1:28332
```

Then restart your Evrmore node for the changes to take effect.

## EvrmoreZMQClient

The `EvrmoreZMQClient` class provides a simple interface for receiving ZMQ notifications from an Evrmore node.

### Basic Usage

```python
import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

async def handle_block(notification):
    print(f"New block: {notification.hex}")

async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

async def main():
    # Create a ZMQ client
    client = EvrmoreZMQClient(
        address="tcp://127.0.0.1:28332",
        topics=[ZMQTopic.HASH_BLOCK, ZMQTopic.HASH_TX]
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

### Initialization

```python
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

# Create a client with default settings (localhost:28332)
client = EvrmoreZMQClient()

# Create a client with custom settings
client = EvrmoreZMQClient(
    address="tcp://127.0.0.1:28332",
    topics=[ZMQTopic.HASH_BLOCK, ZMQTopic.HASH_TX, ZMQTopic.RAW_BLOCK, ZMQTopic.RAW_TX, ZMQTopic.SEQUENCE]
)

# Create a client with a custom ZMQ context
import zmq.asyncio
context = zmq.asyncio.Context()
client = EvrmoreZMQClient(
    address="tcp://127.0.0.1:28332",
    context=context
)
```

### Parameters

- `address` (str): The ZMQ endpoint address (default: "tcp://127.0.0.1:28332")
- `context` (Optional[zmq.asyncio.Context]): A custom ZMQ context (default: None)
- `topics` (List[ZMQTopic]): The topics to subscribe to (default: all topics)

### ZMQTopic Enum

The `ZMQTopic` enum defines the available ZMQ notification topics:

- `HASH_TX`: Transaction hash notifications
- `HASH_BLOCK`: Block hash notifications
- `RAW_TX`: Raw transaction notifications
- `RAW_BLOCK`: Raw block notifications
- `SEQUENCE`: Sequence notifications

### Registering Handlers

You can register handlers for specific notification types using the following decorators:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient

client = EvrmoreZMQClient()

@client.on_block
async def handle_block(notification):
    print(f"New block: {notification.hex}")

@client.on_transaction
async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

@client.on_raw_block
async def handle_raw_block(notification):
    print(f"New raw block: {len(notification.body)} bytes")

@client.on_raw_transaction
async def handle_raw_transaction(notification):
    print(f"New raw transaction: {len(notification.body)} bytes")

@client.on_sequence
async def handle_sequence(notification):
    print(f"New sequence: {notification.hex}")
```

Alternatively, you can register handlers using the method syntax:

```python
async def handle_block(notification):
    print(f"New block: {notification.hex}")

async def handle_transaction(notification):
    print(f"New transaction: {notification.hex}")

client.on_block(handle_block)
client.on_transaction(handle_transaction)
```

### ZMQNotification Object

The `ZMQNotification` object passed to handlers has the following properties:

- `topic` (ZMQTopic): The notification topic
- `body` (bytes): The notification body (raw data)
- `sequence` (Optional[int]): The notification sequence number (if available)
- `hex` (str): The notification body as a hexadecimal string

### Starting and Stopping

The `EvrmoreZMQClient` class provides methods for starting and stopping the client:

```python
import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient

async def main():
    client = EvrmoreZMQClient()
    
    # Register handlers
    # ...
    
    # Start the client
    await client.start()
    
    # Keep running for a while
    await asyncio.sleep(60)
    
    # Stop the client
    await client.stop()

asyncio.run(main())
```

### Async Context Manager

The `EvrmoreZMQClient` class supports the async context manager protocol, which ensures proper cleanup of resources:

```python
import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient

async def main():
    async with EvrmoreZMQClient() as client:
        # Register handlers
        @client.on_block
        async def handle_block(notification):
            print(f"New block: {notification.hex}")
        
        # Keep running for a while
        await asyncio.sleep(60)

asyncio.run(main())
```

## Advanced Usage

### Custom ZMQ Context

You can provide a custom ZMQ context to the `EvrmoreZMQClient` constructor:

```python
import zmq.asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient

# Create a custom ZMQ context
context = zmq.asyncio.Context()

# Create a ZMQ client with the custom context
client = EvrmoreZMQClient(
    address="tcp://127.0.0.1:28332",
    context=context
)
```

### Multiple Handlers

You can register multiple handlers for the same notification type:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient

client = EvrmoreZMQClient()

@client.on_block
async def log_block(notification):
    print(f"New block: {notification.hex}")

@client.on_block
async def save_block(notification):
    # Save the block to a database
    pass

@client.on_block
async def notify_users(notification):
    # Notify users about the new block
    pass
```

### Error Handling

Handlers can raise exceptions, which will be caught and logged by the `EvrmoreZMQClient`:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient

client = EvrmoreZMQClient()

@client.on_block
async def handle_block(notification):
    # This will raise an exception
    raise ValueError("Something went wrong")
```

### Integration with WebSockets

The `EvrmoreZMQClient` can be integrated with WebSockets to broadcast blockchain events to web clients:

```python
import asyncio
import websockets
import json
from evrmore_rpc.zmq import EvrmoreZMQClient

# Connected WebSocket clients
clients = set()

async def register(websocket):
    clients.add(websocket)
    try:
        await websocket.wait_closed()
    finally:
        clients.remove(websocket)

async def broadcast(message):
    if clients:
        await asyncio.gather(
            *[client.send(message) for client in clients]
        )

async def zmq_handler():
    client = EvrmoreZMQClient()
    
    @client.on_block
    async def handle_block(notification):
        message = json.dumps({
            "type": "block",
            "hash": notification.hex
        })
        await broadcast(message)
    
    @client.on_transaction
    async def handle_transaction(notification):
        message = json.dumps({
            "type": "transaction",
            "hash": notification.hex
        })
        await broadcast(message)
    
    await client.start()
    
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await client.stop()

async def websocket_server(websocket, path):
    await register(websocket)

async def main():
    # Start ZMQ handler
    asyncio.create_task(zmq_handler())
    
    # Start WebSocket server
    async with websockets.serve(websocket_server, "localhost", 8765):
        await asyncio.Future()  # Run forever

asyncio.run(main())
```

## ZMQ Utilities

The `evrmore_rpc.zmq.utils` module provides utility functions for working with ZMQ notifications:

### Transaction Utilities

```python
from evrmore_rpc.zmq.utils import (
    get_transaction_hash,
    get_transaction_inputs,
    get_transaction_outputs,
    parse_transaction
)

# Get transaction hash from raw transaction
tx_hash = get_transaction_hash(raw_tx_bytes)

# Get transaction inputs from raw transaction
inputs = get_transaction_inputs(raw_tx_bytes)

# Get transaction outputs from raw transaction
outputs = get_transaction_outputs(raw_tx_bytes)

# Parse raw transaction into a structured object
tx = parse_transaction(raw_tx_bytes)
```

### Block Utilities

```python
from evrmore_rpc.zmq.utils import (
    get_block_hash,
    get_block_header,
    get_block_transactions,
    parse_block
)

# Get block hash from raw block
block_hash = get_block_hash(raw_block_bytes)

# Get block header from raw block
header = get_block_header(raw_block_bytes)

# Get block transactions from raw block
transactions = get_block_transactions(raw_block_bytes)

# Parse raw block into a structured object
block = parse_block(raw_block_bytes)
``` 