# WebSockets Support

The `evrmore-rpc` package provides WebSockets support for real-time communication with clients. This allows you to build applications that can push blockchain events to web clients as they happen.

## Installation

```bash
pip install evrmore-rpc
```

## WebSocket Server

The `EvrmoreWebSocketServer` class provides a WebSocket server that can broadcast blockchain events to connected clients.

### Basic Usage

```python
import asyncio
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

async def main():
    # Create RPC client
    rpc_client = EvrmoreRPCClient()
    
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient()
    
    # Create WebSocket server
    server = EvrmoreWebSocketServer(
        rpc_client=rpc_client,
        zmq_client=zmq_client,
        host="localhost",
        port=8765
    )
    
    # Start the server
    await server.start()
    print(f"WebSocket server started on ws://{server.host}:{server.port}")
    
    # Keep the server running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        # Stop the server
        await server.stop()
        print("WebSocket server stopped")

if __name__ == "__main__":
    asyncio.run(main())
```

### Initialization

```python
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

# Create clients
rpc_client = EvrmoreRPCClient()
zmq_client = EvrmoreZMQClient()

# Create server with default settings (localhost:8765)
server = EvrmoreWebSocketServer(
    rpc_client=rpc_client,
    zmq_client=zmq_client
)

# Create server with custom settings
server = EvrmoreWebSocketServer(
    rpc_client=rpc_client,
    zmq_client=zmq_client,
    host="0.0.0.0",  # Listen on all interfaces
    port=8765,
    ping_interval=30,  # Send ping every 30 seconds
    ping_timeout=10    # Wait 10 seconds for pong response
)
```

### Parameters

- `rpc_client` (EvrmoreRPCClient): The RPC client to use for blockchain queries
- `zmq_client` (EvrmoreZMQClient): The ZMQ client to use for real-time notifications
- `host` (str): The host to bind the WebSocket server to (default: "localhost")
- `port` (int): The port to bind the WebSocket server to (default: 8765)
- `ping_interval` (Optional[float]): How often to ping clients in seconds (default: 20)
- `ping_timeout` (Optional[float]): How long to wait for pong response in seconds (default: 20)

### Starting and Stopping

The `EvrmoreWebSocketServer` class provides methods for starting and stopping the server:

```python
import asyncio
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

async def main():
    # Create clients
    rpc_client = EvrmoreRPCClient()
    zmq_client = EvrmoreZMQClient()
    
    # Create server
    server = EvrmoreWebSocketServer(
        rpc_client=rpc_client,
        zmq_client=zmq_client
    )
    
    # Start the server
    await server.start()
    print(f"WebSocket server started on ws://{server.host}:{server.port}")
    
    # Keep running for a while
    await asyncio.sleep(60)
    
    # Stop the server
    await server.stop()
    print("WebSocket server stopped")

asyncio.run(main())
```

## WebSocket Client

The `EvrmoreWebSocketClient` class provides a WebSocket client that can connect to an `EvrmoreWebSocketServer` and receive real-time blockchain events.

### Basic Usage

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

### Initialization

```python
from evrmore_rpc.websockets import EvrmoreWebSocketClient

# Create a client with default settings
client = EvrmoreWebSocketClient()

# Create a client with custom settings
client = EvrmoreWebSocketClient(
    uri="ws://example.com:8765",
    ping_interval=30,  # Send ping every 30 seconds
    ping_timeout=10    # Wait 10 seconds for pong response
)
```

### Parameters

- `uri` (str): The WebSocket server URI (default: "ws://localhost:8765")
- `ping_interval` (Optional[float]): How often to ping the server in seconds (default: 20)
- `ping_timeout` (Optional[float]): How long to wait for pong response in seconds (default: 20)

### Connecting and Disconnecting

The `EvrmoreWebSocketClient` class provides methods for connecting to and disconnecting from a WebSocket server:

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Create a client
    client = EvrmoreWebSocketClient()
    
    # Connect to the server
    await client.connect()
    print("Connected to WebSocket server")
    
    # Keep connected for a while
    await asyncio.sleep(60)
    
    # Disconnect
    await client.disconnect()
    print("Disconnected from WebSocket server")

asyncio.run(main())
```

### Subscribing to Topics

The `EvrmoreWebSocketClient` class provides methods for subscribing to and unsubscribing from topics:

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Create a client
    client = EvrmoreWebSocketClient()
    
    # Connect to the server
    await client.connect()
    
    # Subscribe to topics
    await client.subscribe("blocks")
    await client.subscribe("transactions")
    await client.subscribe("assets")
    
    # Process messages for a while
    for _ in range(10):
        message = await client.receive()
        print(f"Received message: {message.type}")
    
    # Unsubscribe from a topic
    await client.unsubscribe("transactions")
    
    # Process more messages
    for _ in range(5):
        message = await client.receive()
        print(f"Received message: {message.type}")
    
    # Disconnect
    await client.disconnect()

asyncio.run(main())
```

### Receiving Messages

The `EvrmoreWebSocketClient` class provides methods for receiving messages:

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Create a client
    client = EvrmoreWebSocketClient()
    
    # Connect to the server
    await client.connect()
    
    # Subscribe to topics
    await client.subscribe("blocks")
    await client.subscribe("transactions")
    
    # Receive a single message
    message = await client.receive()
    print(f"Received message: {message.type}")
    
    # Receive messages in a loop
    try:
        while True:
            message = await client.receive()
            print(f"Received message: {message.type}")
    except asyncio.CancelledError:
        # Handle cancellation
        pass
    finally:
        # Disconnect
        await client.disconnect()

asyncio.run(main())
```

### Async Iterator

The `EvrmoreWebSocketClient` class also supports the async iterator protocol, which makes it easy to process messages in a loop:

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Create a client
    client = EvrmoreWebSocketClient()
    
    # Connect to the server
    await client.connect()
    
    # Subscribe to topics
    await client.subscribe("blocks")
    await client.subscribe("transactions")
    
    # Process messages using async for
    try:
        async for message in client:
            print(f"Received message: {message.type}")
            
            # Process message based on type
            if message.type == "block":
                block_data = message.data
                print(f"New block: {block_data.hash} (height: {block_data.height})")
                
            elif message.type == "transaction":
                tx_data = message.data
                print(f"New transaction: {tx_data.txid}")
    except asyncio.CancelledError:
        # Handle cancellation
        pass
    finally:
        # Disconnect
        await client.disconnect()

asyncio.run(main())
```

## WebSocket Message Format

The WebSocket messages exchanged between the server and clients follow a specific format.

### Server to Client Messages

Messages sent from the server to clients have the following format:

```json
{
    "type": "block",
    "data": {
        "hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
        "height": 1,
        "time": 1231006505,
        "tx_count": 1,
        "size": 285
    }
}
```

The `type` field indicates the type of message, and the `data` field contains the message data.

#### Block Messages

Block messages have the following format:

```json
{
    "type": "block",
    "data": {
        "hash": "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f",
        "height": 1,
        "time": 1231006505,
        "tx_count": 1,
        "size": 285
    }
}
```

#### Transaction Messages

Transaction messages have the following format:

```json
{
    "type": "transaction",
    "data": {
        "txid": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
        "size": 285,
        "vsize": 285,
        "version": 1,
        "locktime": 0,
        "vin_count": 1,
        "vout_count": 1
    }
}
```

#### Asset Messages

Asset messages have the following format:

```json
{
    "type": "asset",
    "data": {
        "txid": "4a5e1e4baab89f3a32518a88c31bc87f618f76673e2cc77ab2127b7afdeda33b",
        "asset": "ASSET_NAME",
        "amount": 100,
        "type": "transfer"
    }
}
```

#### Mempool Messages

Mempool messages have the following format:

```json
{
    "type": "mempool",
    "data": {
        "size": 100,
        "bytes": 28500,
        "usage": 112000
    }
}
```

### Client to Server Messages

Messages sent from clients to the server have the following format:

#### Subscribe Messages

```json
{
    "action": "subscribe",
    "topic": "blocks"
}
```

#### Unsubscribe Messages

```json
{
    "action": "unsubscribe",
    "topic": "blocks"
}
```

#### Command Messages

```json
{
    "command": "getblockchaininfo",
    "params": []
}
```

## Advanced Usage

### Custom Message Handlers

You can create custom message handlers for the WebSocket client:

```python
import asyncio
import json
from evrmore_rpc.websockets import EvrmoreWebSocketClient

class CustomWebSocketClient(EvrmoreWebSocketClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.block_count = 0
        self.tx_count = 0
        
    async def handle_block(self, block_data):
        """Handle a block message."""
        self.block_count += 1
        print(f"New block: {block_data.hash} (height: {block_data.height})")
        print(f"Total blocks received: {self.block_count}")
        
    async def handle_transaction(self, tx_data):
        """Handle a transaction message."""
        self.tx_count += 1
        print(f"New transaction: {tx_data.txid}")
        print(f"Total transactions received: {self.tx_count}")
        
    async def process_messages(self):
        """Process messages from the server."""
        async for message in self:
            if message.type == "block":
                await self.handle_block(message.data)
            elif message.type == "transaction":
                await self.handle_transaction(message.data)

async def main():
    # Create a custom client
    client = CustomWebSocketClient()
    
    # Connect to the server
    await client.connect()
    
    # Subscribe to topics
    await client.subscribe("blocks")
    await client.subscribe("transactions")
    
    # Process messages
    try:
        await client.process_messages()
    except asyncio.CancelledError:
        pass
    finally:
        await client.disconnect()

asyncio.run(main())
```

### Integration with Web Frameworks

The WebSocket client can be integrated with web frameworks like FastAPI:

```python
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from evrmore_rpc.websockets import EvrmoreWebSocketClient

app = FastAPI()

# HTML for a simple WebSocket client
html = """
<!DOCTYPE html>
<html>
    <head>
        <title>Evrmore WebSocket Client</title>
    </head>
    <body>
        <h1>Evrmore WebSocket Client</h1>
        <div id="messages"></div>
        <script>
            var ws = new WebSocket("ws://localhost:8000/ws");
            ws.onmessage = function(event) {
                var messages = document.getElementById('messages');
                var message = document.createElement('p');
                message.textContent = event.data;
                messages.appendChild(message);
            };
        </script>
    </body>
</html>
"""

@app.get("/")
async def get():
    return HTMLResponse(html)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    
    # Create a WebSocket client to connect to the Evrmore WebSocket server
    client = EvrmoreWebSocketClient()
    
    try:
        # Connect to the Evrmore WebSocket server
        await client.connect()
        
        # Subscribe to topics
        await client.subscribe("blocks")
        await client.subscribe("transactions")
        
        # Forward messages from the Evrmore WebSocket server to the web client
        async for message in client:
            await websocket.send_text(f"{message.type}: {message.data}")
    
    except WebSocketDisconnect:
        # Web client disconnected
        pass
    except Exception as e:
        # Handle other exceptions
        print(f"Error: {e}")
    finally:
        # Disconnect from the Evrmore WebSocket server
        await client.disconnect()
```

### Custom WebSocket Server

You can create a custom WebSocket server that extends the functionality of `EvrmoreWebSocketServer`:

```python
import asyncio
import json
import logging
from typing import Dict, Set, Any

from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("custom-websocket-server")

class CustomWebSocketServer(EvrmoreWebSocketServer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.custom_topics = {
            "large_blocks": set(),
            "asset_transfers": set()
        }
        
    async def handle_block(self, notification):
        """Handle a block notification."""
        # Call the parent method to handle the notification
        await super().handle_block(notification)
        
        # Get block details
        block_hash = notification.hex
        block = self.rpc_client.getblock(block_hash)
        
        # Check if this is a large block
        if len(block.tx) > 100:
            # Prepare message
            message = {
                "type": "large_block",
                "data": {
                    "hash": block.hash,
                    "height": block.height,
                    "time": block.time,
                    "tx_count": len(block.tx),
                    "size": block.size
                }
            }
            
            # Broadcast to subscribers
            await self.broadcast("large_blocks", message)
            
    async def handle_transaction(self, notification):
        """Handle a transaction notification."""
        # Call the parent method to handle the notification
        await super().handle_transaction(notification)
        
        # Get transaction details
        txid = notification.hex
        
        try:
            tx = self.rpc_client.getrawtransaction(txid, True)
            
            # Check for asset transfers
            for vout in tx.vout:
                if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                    asset = vout["scriptPubKey"]["asset"]
                    
                    # Prepare asset message
                    asset_message = {
                        "type": "asset_transfer",
                        "data": {
                            "txid": tx.txid,
                            "asset": asset["name"],
                            "amount": asset["amount"],
                            "from": "unknown",  # Would need to look up the input address
                            "to": vout["scriptPubKey"].get("addresses", ["unknown"])[0]
                        }
                    }
                    
                    # Broadcast to asset transfer subscribers
                    await self.broadcast("asset_transfers", asset_message)
        except Exception as e:
            logger.error(f"Error handling transaction: {e}")
            
    async def handle_client_message(self, websocket, message):
        """Handle a message from a client."""
        try:
            data = json.loads(message)
            
            # Handle custom subscriptions
            if "action" in data and "topic" in data:
                action = data["action"]
                topic = data["topic"]
                
                if topic in self.custom_topics:
                    if action == "subscribe":
                        self.custom_topics[topic].add(websocket)
                        await websocket.send(json.dumps({
                            "type": "subscription",
                            "status": "success",
                            "topic": topic
                        }))
                        logger.info(f"Client subscribed to custom topic: {topic}")
                    elif action == "unsubscribe":
                        if websocket in self.custom_topics[topic]:
                            self.custom_topics[topic].remove(websocket)
                            await websocket.send(json.dumps({
                                "type": "subscription",
                                "status": "success",
                                "topic": topic,
                                "action": "unsubscribe"
                            }))
                            logger.info(f"Client unsubscribed from custom topic: {topic}")
                    return True
            
            # If not handled, let the parent class handle it
            return await super().handle_client_message(websocket, message)
            
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "type": "error",
                "message": "Invalid JSON"
            }))
            return True
            
    async def broadcast(self, topic, message):
        """Broadcast a message to subscribers of a topic."""
        if topic in self.subscriptions:
            # Use the parent method for standard topics
            await super().broadcast(topic, message)
        elif topic in self.custom_topics:
            # Handle custom topics
            subscribers = self.custom_topics[topic]
            if subscribers:
                message_str = json.dumps(message)
                await asyncio.gather(
                    *[client.send(message_str) for client in subscribers],
                    return_exceptions=True
                )

async def main():
    # Create clients
    rpc_client = EvrmoreRPCClient()
    zmq_client = EvrmoreZMQClient()
    
    # Create custom server
    server = CustomWebSocketServer(
        rpc_client=rpc_client,
        zmq_client=zmq_client
    )
    
    # Start the server
    await server.start()
    print(f"Custom WebSocket server started on ws://{server.host}:{server.port}")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await server.stop()
        print("Custom WebSocket server stopped")

if __name__ == "__main__":
    asyncio.run(main()) 