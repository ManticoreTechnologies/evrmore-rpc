# Advanced Usage

This document covers advanced usage patterns for the `evrmore-rpc` package, including performance optimization, error handling, and integration with other libraries.

## Performance Optimization

### Connection Pooling

When making multiple RPC calls, it's more efficient to reuse the same client instance rather than creating a new one for each call:

```python
from evrmore_rpc import EvrmoreRPCClient

# Create a single client instance
client = EvrmoreRPCClient()

# Reuse the client for multiple calls
info = client.getblockchaininfo()
block_hash = client.getblockhash(1)
block = client.getblock(block_hash)
```

### Parallel Execution with Async API

For applications that need to make many RPC calls, the asynchronous API can significantly improve performance by executing calls concurrently:

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

async def main():
    async with EvrmoreAsyncRPCClient() as client:
        # Execute multiple commands concurrently
        info, block_hash, mempool_info = await asyncio.gather(
            client.getblockchaininfo(),
            client.getblockhash(1),
            client.getmempoolinfo()
        )
        
        # Get block details
        block = await client.getblock(block_hash)
        
        # Print results
        print(f"Current block height: {info.blocks}")
        print(f"Block #1 hash: {block.hash}")
        print(f"Mempool size: {mempool_info['size']}")

asyncio.run(main())
```

### Batch Processing

For processing large amounts of data, use batch processing to avoid memory issues:

```python
from evrmore_rpc import EvrmoreRPCClient

def process_blocks_in_batches(start_height, end_height, batch_size=100):
    client = EvrmoreRPCClient()
    
    for batch_start in range(start_height, end_height, batch_size):
        batch_end = min(batch_start + batch_size, end_height)
        print(f"Processing blocks {batch_start} to {batch_end}")
        
        for height in range(batch_start, batch_end):
            block_hash = client.getblockhash(height)
            block = client.getblock(block_hash)
            # Process block data
            print(f"Block {height}: {len(block.tx)} transactions")

# Process blocks 1 to 1000 in batches of 100
process_blocks_in_batches(1, 1000, 100)
```

## Error Handling

### Robust Error Handling

Implement robust error handling to deal with network issues, node downtime, and other potential problems:

```python
from evrmore_rpc import EvrmoreRPCClient, EvrmoreRPCError
import time

def get_block_with_retry(height, max_retries=3, retry_delay=1):
    client = EvrmoreRPCClient()
    
    for attempt in range(max_retries):
        try:
            block_hash = client.getblockhash(height)
            block = client.getblock(block_hash)
            return block
        except EvrmoreRPCError as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
                retry_delay *= 2  # Exponential backoff
            else:
                print("Max retries reached, giving up.")
                raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

# Try to get block 100 with retries
try:
    block = get_block_with_retry(100)
    print(f"Block 100 has {len(block.tx)} transactions")
except Exception as e:
    print(f"Failed to get block: {e}")
```

### Async Error Handling

For asynchronous code, use proper async error handling:

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

async def get_block_with_retry_async(height, max_retries=3, retry_delay=1):
    async with EvrmoreAsyncRPCClient() as client:
        for attempt in range(max_retries):
            try:
                block_hash = await client.getblockhash(height)
                block = await client.getblock(block_hash)
                return block
            except EvrmoreRPCError as e:
                print(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    print("Max retries reached, giving up.")
                    raise
            except Exception as e:
                print(f"Unexpected error: {e}")
                raise

async def main():
    try:
        block = await get_block_with_retry_async(100)
        print(f"Block 100 has {len(block.tx)} transactions")
    except Exception as e:
        print(f"Failed to get block: {e}")

asyncio.run(main())
```

## Integration with Other Libraries

### Integration with FastAPI

Integrate with FastAPI to create a blockchain API:

```python
from fastapi import FastAPI, HTTPException
from evrmore_rpc import EvrmoreRPCClient, EvrmoreRPCError

app = FastAPI(title="Evrmore API", description="API for Evrmore blockchain")
client = EvrmoreRPCClient()

@app.get("/blockchain/info")
def get_blockchain_info():
    try:
        info = client.getblockchaininfo()
        return {
            "blocks": info.blocks,
            "headers": info.headers,
            "bestblockhash": info.bestblockhash,
            "difficulty": float(info.difficulty),
            "chain": info.chain
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/block/{height}")
def get_block(height: int):
    try:
        block_hash = client.getblockhash(height)
        block = client.getblock(block_hash)
        return {
            "hash": block.hash,
            "height": block.height,
            "time": block.time,
            "tx_count": len(block.tx),
            "size": block.size
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/transaction/{txid}")
def get_transaction(txid: str):
    try:
        tx = client.getrawtransaction(txid, True)
        return {
            "txid": tx.txid,
            "size": tx.size,
            "vsize": tx.vsize,
            "version": tx.version,
            "locktime": tx.locktime,
            "vin_count": len(tx.vin),
            "vout_count": len(tx.vout)
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Integration with Async FastAPI

For better performance, integrate with FastAPI using the async client:

```python
from fastapi import FastAPI, HTTPException
from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

app = FastAPI(title="Evrmore Async API", description="Async API for Evrmore blockchain")
client = EvrmoreAsyncRPCClient()

@app.on_event("startup")
async def startup():
    await client.initialize()

@app.on_event("shutdown")
async def shutdown():
    pass  # No cleanup needed for EvrmoreAsyncRPCClient

@app.get("/blockchain/info")
async def get_blockchain_info():
    try:
        info = await client.getblockchaininfo()
        return {
            "blocks": info.blocks,
            "headers": info.headers,
            "bestblockhash": info.bestblockhash,
            "difficulty": float(info.difficulty),
            "chain": info.chain
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/block/{height}")
async def get_block(height: int):
    try:
        block_hash = await client.getblockhash(height)
        block = await client.getblock(block_hash)
        return {
            "hash": block.hash,
            "height": block.height,
            "time": block.time,
            "tx_count": len(block.tx),
            "size": block.size
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Integration with SQLAlchemy

Store blockchain data in a database using SQLAlchemy:

```python
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from evrmore_rpc import EvrmoreRPCClient

# Set up SQLAlchemy
Base = declarative_base()
engine = create_engine("sqlite:///blockchain.db")
Session = sessionmaker(bind=engine)

# Define models
class Block(Base):
    __tablename__ = "blocks"
    
    height = Column(Integer, primary_key=True)
    hash = Column(String, unique=True, nullable=False)
    time = Column(Integer, nullable=False)
    size = Column(Integer, nullable=False)
    tx_count = Column(Integer, nullable=False)
    transactions = relationship("Transaction", back_populates="block")

class Transaction(Base):
    __tablename__ = "transactions"
    
    txid = Column(String, primary_key=True)
    block_height = Column(Integer, ForeignKey("blocks.height"), nullable=False)
    size = Column(Integer, nullable=False)
    time = Column(Integer, nullable=False)
    block = relationship("Block", back_populates="transactions")

# Create tables
Base.metadata.create_all(engine)

# Function to sync blockchain data
def sync_blockchain_data(start_height, end_height):
    client = EvrmoreRPCClient()
    session = Session()
    
    try:
        for height in range(start_height, end_height + 1):
            # Check if block already exists
            existing_block = session.query(Block).filter_by(height=height).first()
            if existing_block:
                print(f"Block {height} already exists, skipping")
                continue
            
            # Get block data
            block_hash = client.getblockhash(height)
            block_data = client.getblock(block_hash)
            
            # Create block record
            block = Block(
                height=height,
                hash=block_data.hash,
                time=block_data.time,
                size=block_data.size,
                tx_count=len(block_data.tx)
            )
            session.add(block)
            
            # Create transaction records
            for txid in block_data.tx:
                tx_data = client.getrawtransaction(txid, True)
                tx = Transaction(
                    txid=txid,
                    block_height=height,
                    size=tx_data.size,
                    time=block_data.time
                )
                session.add(tx)
            
            # Commit after each block
            session.commit()
            print(f"Synced block {height} with {len(block_data.tx)} transactions")
    
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

# Sync blocks 1 to 100
sync_blockchain_data(1, 100)
```

## Advanced ZMQ Usage

### Custom ZMQ Message Processing

Process ZMQ messages with custom logic:

```python
import asyncio
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic
from evrmore_rpc import EvrmoreRPCClient

class BlockchainMonitor:
    def __init__(self):
        self.zmq_client = EvrmoreZMQClient()
        self.rpc_client = EvrmoreRPCClient()
        self.blocks_processed = 0
        self.transactions_processed = 0
        self.asset_transfers = []
        
    async def start(self):
        # Register handlers
        self.zmq_client.on_block(self.handle_block)
        self.zmq_client.on_transaction(self.handle_transaction)
        
        # Start the ZMQ client
        await self.zmq_client.start()
        print("Blockchain monitor started")
        
    async def stop(self):
        await self.zmq_client.stop()
        print("Blockchain monitor stopped")
        
    async def handle_block(self, notification):
        block_hash = notification.hex
        block = self.rpc_client.getblock(block_hash)
        
        self.blocks_processed += 1
        print(f"New block: {block.hash} (height: {block.height})")
        print(f"Block contains {len(block.tx)} transactions")
        
        # Analyze block data
        if len(block.tx) > 100:
            print(f"Large block detected: {len(block.tx)} transactions")
        
    async def handle_transaction(self, notification):
        txid = notification.hex
        
        try:
            tx = self.rpc_client.getrawtransaction(txid, True)
            self.transactions_processed += 1
            
            # Check for asset transfers
            for vout in tx.vout:
                if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                    asset = vout["scriptPubKey"]["asset"]
                    print(f"Asset transfer detected: {asset['name']} ({asset['amount']})")
                    
                    self.asset_transfers.append({
                        "txid": txid,
                        "asset": asset["name"],
                        "amount": asset["amount"],
                        "time": tx.time if hasattr(tx, "time") else None
                    })
        except Exception as e:
            print(f"Error processing transaction {txid}: {e}")

async def main():
    monitor = BlockchainMonitor()
    
    try:
        await monitor.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await monitor.stop()
        
        # Print summary
        print(f"Processed {monitor.blocks_processed} blocks")
        print(f"Processed {monitor.transactions_processed} transactions")
        print(f"Detected {len(monitor.asset_transfers)} asset transfers")

asyncio.run(main())
```

## Advanced WebSockets Usage

### Custom WebSocket Server

Create a custom WebSocket server with additional functionality:

```python
import asyncio
import json
import logging
from typing import Dict, Set, Any

import websockets
from websockets.server import WebSocketServerProtocol

from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("custom-websocket-server")

class CustomWebSocketServer:
    def __init__(self, host="localhost", port=8765):
        self.host = host
        self.port = port
        self.clients: Set[WebSocketServerProtocol] = set()
        self.subscriptions: Dict[str, Set[WebSocketServerProtocol]] = {
            "blocks": set(),
            "transactions": set(),
            "assets": set(),
            "mempool": set()
        }
        self.rpc_client = EvrmoreRPCClient()
        self.zmq_client = EvrmoreZMQClient()
        self.server = None
        
    async def start(self):
        # Register ZMQ handlers
        self.zmq_client.on_block(self.handle_block)
        self.zmq_client.on_transaction(self.handle_transaction)
        
        # Start ZMQ client
        await self.zmq_client.start()
        
        # Start WebSocket server
        self.server = await websockets.serve(
            self.handle_client,
            self.host,
            self.port
        )
        
        logger.info(f"WebSocket server started on ws://{self.host}:{self.port}")
        
    async def stop(self):
        # Stop WebSocket server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        # Stop ZMQ client
        await self.zmq_client.stop()
        
        logger.info("WebSocket server stopped")
        
    async def handle_client(self, websocket: WebSocketServerProtocol, path: str):
        # Register client
        self.clients.add(websocket)
        logger.info(f"Client connected: {websocket.remote_address}")
        
        try:
            async for message in websocket:
                try:
                    data = json.loads(message)
                    
                    if "action" in data and "topic" in data:
                        action = data["action"]
                        topic = data["topic"]
                        
                        if action == "subscribe":
                            if topic in self.subscriptions:
                                self.subscriptions[topic].add(websocket)
                                await websocket.send(json.dumps({
                                    "type": "subscription",
                                    "status": "success",
                                    "topic": topic
                                }))
                                logger.info(f"Client subscribed to {topic}")
                            else:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": f"Invalid topic: {topic}"
                                }))
                        
                        elif action == "unsubscribe":
                            if topic in self.subscriptions and websocket in self.subscriptions[topic]:
                                self.subscriptions[topic].remove(websocket)
                                await websocket.send(json.dumps({
                                    "type": "subscription",
                                    "status": "success",
                                    "topic": topic,
                                    "action": "unsubscribe"
                                }))
                                logger.info(f"Client unsubscribed from {topic}")
                            else:
                                await websocket.send(json.dumps({
                                    "type": "error",
                                    "message": f"Not subscribed to topic: {topic}"
                                }))
                        
                        else:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": f"Invalid action: {action}"
                            }))
                    
                    elif "command" in data:
                        # Handle RPC commands
                        command = data["command"]
                        params = data.get("params", [])
                        
                        try:
                            result = getattr(self.rpc_client, command)(*params)
                            await websocket.send(json.dumps({
                                "type": "command",
                                "command": command,
                                "result": result
                            }))
                        except Exception as e:
                            await websocket.send(json.dumps({
                                "type": "error",
                                "message": f"Command failed: {str(e)}"
                            }))
                    
                    else:
                        await websocket.send(json.dumps({
                            "type": "error",
                            "message": "Invalid message format"
                        }))
                
                except json.JSONDecodeError:
                    await websocket.send(json.dumps({
                        "type": "error",
                        "message": "Invalid JSON"
                    }))
        
        except websockets.exceptions.ConnectionClosed:
            logger.info(f"Client disconnected: {websocket.remote_address}")
        finally:
            # Unregister client
            self.clients.remove(websocket)
            for subscribers in self.subscriptions.values():
                if websocket in subscribers:
                    subscribers.remove(websocket)
    
    async def handle_block(self, notification):
        block_hash = notification.hex
        
        try:
            # Get block details
            block = self.rpc_client.getblock(block_hash)
            
            # Prepare message
            message = {
                "type": "block",
                "data": {
                    "hash": block.hash,
                    "height": block.height,
                    "time": block.time,
                    "tx_count": len(block.tx),
                    "size": block.size
                }
            }
            
            # Broadcast to subscribers
            await self.broadcast("blocks", message)
            
            # Update mempool info
            await self.update_mempool()
            
        except Exception as e:
            logger.error(f"Error handling block: {e}")
    
    async def handle_transaction(self, notification):
        txid = notification.hex
        
        try:
            # Get transaction details
            tx = self.rpc_client.getrawtransaction(txid, True)
            
            # Prepare message
            message = {
                "type": "transaction",
                "data": {
                    "txid": tx.txid,
                    "size": tx.size,
                    "vsize": tx.vsize,
                    "version": tx.version,
                    "locktime": tx.locktime,
                    "vin_count": len(tx.vin),
                    "vout_count": len(tx.vout)
                }
            }
            
            # Broadcast to subscribers
            await self.broadcast("transactions", message)
            
            # Check for asset transfers
            for vout in tx.vout:
                if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                    asset = vout["scriptPubKey"]["asset"]
                    
                    # Prepare asset message
                    asset_message = {
                        "type": "asset",
                        "data": {
                            "txid": tx.txid,
                            "asset": asset["name"],
                            "amount": asset["amount"],
                            "type": "transfer"
                        }
                    }
                    
                    # Broadcast to asset subscribers
                    await self.broadcast("assets", asset_message)
            
        except Exception as e:
            logger.error(f"Error handling transaction: {e}")
    
    async def update_mempool(self):
        try:
            # Get mempool info
            mempool = self.rpc_client.getmempoolinfo()
            
            # Prepare message
            message = {
                "type": "mempool",
                "data": {
                    "size": mempool["size"],
                    "bytes": mempool["bytes"],
                    "usage": mempool["usage"]
                }
            }
            
            # Broadcast to subscribers
            await self.broadcast("mempool", message)
            
        except Exception as e:
            logger.error(f"Error updating mempool: {e}")
    
    async def broadcast(self, topic: str, message: Dict[str, Any]):
        if topic in self.subscriptions:
            subscribers = self.subscriptions[topic]
            if subscribers:
                message_str = json.dumps(message)
                await asyncio.gather(
                    *[client.send(message_str) for client in subscribers],
                    return_exceptions=True
                )

async def main():
    server = CustomWebSocketServer()
    
    try:
        await server.start()
        
        # Keep running until interrupted
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("Interrupted by user")
    finally:
        await server.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Security Considerations

### Secure RPC Configuration

Ensure your Evrmore node's RPC configuration is secure:

```
# evrmore.conf
rpcuser=your_username
rpcpassword=your_strong_password
rpcport=8819
rpcallowip=127.0.0.1
```

### Environment Variables for Credentials

Use environment variables for RPC credentials instead of hardcoding them:

```python
import os
from evrmore_rpc import EvrmoreRPCClient

# Get credentials from environment variables
rpcuser = os.environ.get("EVRMORE_RPC_USER")
rpcpassword = os.environ.get("EVRMORE_RPC_PASSWORD")

# Create client with credentials
client = EvrmoreRPCClient(rpcuser=rpcuser, rpcpassword=rpcpassword)
```

### Rate Limiting

Implement rate limiting to prevent overloading the node:

```python
import time
from evrmore_rpc import EvrmoreRPCClient

class RateLimitedClient:
    def __init__(self, max_calls_per_second=5):
        self.client = EvrmoreRPCClient()
        self.max_calls_per_second = max_calls_per_second
        self.call_times = []
        
    def _check_rate_limit(self):
        """Check if we're exceeding the rate limit and wait if necessary."""
        now = time.time()
        
        # Remove old calls from the list
        self.call_times = [t for t in self.call_times if now - t < 1.0]
        
        # If we've made too many calls in the last second, wait
        if len(self.call_times) >= self.max_calls_per_second:
            wait_time = 1.0 - (now - self.call_times[0])
            if wait_time > 0:
                time.sleep(wait_time)
                now = time.time()  # Update current time
        
        # Record this call
        self.call_times.append(now)
        
    def __getattr__(self, name):
        """Forward method calls to the underlying client with rate limiting."""
        method = getattr(self.client, name)
        
        def wrapper(*args, **kwargs):
            self._check_rate_limit()
            return method(*args, **kwargs)
        
        return wrapper

# Use the rate-limited client
client = RateLimitedClient(max_calls_per_second=5)
info = client.getblockchaininfo()
```

## Debugging and Troubleshooting

### Logging

Set up logging to help with debugging:

```python
import logging
from evrmore_rpc import EvrmoreRPCClient, EvrmoreRPCError

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    filename="evrmore_rpc.log"
)
logger = logging.getLogger("evrmore_rpc")

# Create client
client = EvrmoreRPCClient()

# Use client with logging
try:
    logger.info("Getting blockchain info")
    info = client.getblockchaininfo()
    logger.info(f"Current block height: {info.blocks}")
    
    logger.info(f"Getting block at height 1")
    block_hash = client.getblockhash(1)
    block = client.getblock(block_hash)
    logger.info(f"Block #1 hash: {block.hash}")
    
except EvrmoreRPCError as e:
    logger.error(f"RPC error: {e}")
except Exception as e:
    logger.exception(f"Unexpected error: {e}")
```

### Verbose Mode

Enable verbose mode to see more details about RPC calls:

```python
import logging
from evrmore_rpc import EvrmoreRPCClient

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("evrmore_rpc")

# Create client with verbose mode
client = EvrmoreRPCClient(verbose=True)

# Make RPC calls
info = client.getblockchaininfo()
```

### Common Issues and Solutions

#### Connection Refused

If you get a "Connection refused" error:

1. Check if the Evrmore node is running
2. Verify the RPC port is correct
3. Check if the node is configured to accept RPC connections
4. Ensure the firewall allows connections to the RPC port

#### Authentication Failed

If you get an authentication error:

1. Check if the RPC username and password are correct
2. Verify the RPC credentials in the Evrmore configuration file
3. Restart the Evrmore node after changing the configuration

#### Timeout

If RPC calls time out:

1. Check if the node is syncing or processing a large number of transactions
2. Increase the timeout value when creating the client
3. Consider using a more powerful machine for the node

```python
from evrmore_rpc import EvrmoreRPCClient

# Create client with increased timeout
client = EvrmoreRPCClient(timeout=60)  # 60 seconds timeout
``` 