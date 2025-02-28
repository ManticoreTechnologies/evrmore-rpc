# Asynchronous API

The `evrmore-rpc` package provides an asynchronous API for interacting with the Evrmore blockchain through the `EvrmoreAsyncRPCClient` class.

## Installation

```bash
pip install evrmore-rpc
```

## EvrmoreAsyncRPCClient

The `EvrmoreAsyncRPCClient` class provides an asynchronous, typed interface to the Evrmore RPC API. It allows you to execute multiple RPC commands concurrently, improving performance for applications that need to make many RPC calls.

### Initialization

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

# Create a client with default settings
client = EvrmoreAsyncRPCClient()

# Create a client with custom settings
client = EvrmoreAsyncRPCClient(
    datadir="/path/to/evrmore/data",
    rpcuser="username",
    rpcpassword="password",
    rpcport=8819,
    testnet=False
)
```

### Parameters

- `datadir` (Optional[Path]): Path to Evrmore data directory
- `rpcuser` (Optional[str]): RPC username
- `rpcpassword` (Optional[str]): RPC password
- `rpcport` (Optional[int]): RPC port number
- `testnet` (bool): Use testnet (default: False)

### Async Context Manager

The `EvrmoreAsyncRPCClient` class supports the async context manager protocol, which ensures proper cleanup of resources:

```python
async def main():
    async with EvrmoreAsyncRPCClient() as client:
        # Use the client here
        info = await client.getblockchaininfo()
        print(f"Current block height: {info.blocks}")

asyncio.run(main())
```

### Methods

The `EvrmoreAsyncRPCClient` class provides asynchronous methods for all Evrmore RPC commands. These methods are dynamically generated based on the available RPC commands.

#### Blockchain Commands

```python
async def main():
    async with EvrmoreAsyncRPCClient() as client:
        # Get blockchain info
        info = await client.getblockchaininfo()
        print(f"Current block height: {info.blocks}")
        print(f"Chain: {info.chain}")
        print(f"Difficulty: {info.difficulty}")
        
        # Get a block
        block_hash = await client.getblockhash(1)
        block = await client.getblock(block_hash)
        print(f"Block #1 hash: {block.hash}")
        print(f"Block #1 time: {block.time}")
        print(f"Block #1 transactions: {len(block.tx)}")
        
        # Get mempool info
        mempool_info = await client.getmempoolinfo()
        print(f"Mempool size: {mempool_info['size']}")
        print(f"Mempool bytes: {mempool_info['bytes']}")

asyncio.run(main())
```

#### Asset Commands

```python
async def main():
    async with EvrmoreAsyncRPCClient() as client:
        # List assets
        assets = await client.listassets()
        print(f"Found {len(assets)} assets")
        
        # Get asset data
        asset_info = await client.getassetdata("ASSET_NAME")
        print(f"Asset name: {asset_info.name}")
        print(f"Asset amount: {asset_info.amount}")
        print(f"Asset units: {asset_info.units}")
        print(f"Asset reissuable: {asset_info.reissuable}")
        
        # Issue a new asset
        txid = await client.issue(
            asset_name="NEW_ASSET",
            qty=1000,
            to_address="EVR_ADDRESS",
            change_address="EVR_ADDRESS",
            units=0,
            reissuable=True,
            has_ipfs=False
        )
        print(f"Asset issued with transaction ID: {txid}")
        
        # Transfer an asset
        txid = await client.transfer(
            asset_name="ASSET_NAME",
            qty=100,
            to_address="EVR_ADDRESS"
        )
        print(f"Asset transferred with transaction ID: {txid}")

asyncio.run(main())
```

#### Concurrent Execution

One of the main advantages of the asynchronous API is the ability to execute multiple RPC commands concurrently:

```python
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

### Error Handling

The `EvrmoreAsyncRPCClient` class raises `EvrmoreRPCError` exceptions when an error occurs:

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

async def main():
    async with EvrmoreAsyncRPCClient() as client:
        try:
            result = await client.getblock("invalid_hash")
        except EvrmoreRPCError as e:
            print(f"Error: {e}")

asyncio.run(main())
```

## Direct Command Execution

You can also execute commands directly using the `execute_command` method:

```python
async def main():
    async with EvrmoreAsyncRPCClient() as client:
        # Execute a command with arguments
        result = await client.execute_command("getblock", "blockhash", 1)
        print(result)

asyncio.run(main())
```

## Integration with Other Async Frameworks

The `EvrmoreAsyncRPCClient` class can be integrated with other async frameworks like FastAPI, aiohttp, or asyncio-based applications:

### FastAPI Example

```python
from fastapi import FastAPI, HTTPException
from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

app = FastAPI()
client = EvrmoreAsyncRPCClient()

@app.get("/blockchain/info")
async def get_blockchain_info():
    try:
        info = await client.getblockchaininfo()
        return {
            "blocks": info.blocks,
            "chain": info.chain,
            "difficulty": info.difficulty
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
            "transactions": len(block.tx)
        }
    except EvrmoreRPCError as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### aiohttp Example

```python
import aiohttp
from aiohttp import web
from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

async def get_blockchain_info(request):
    try:
        async with EvrmoreAsyncRPCClient() as client:
            info = await client.getblockchaininfo()
            return web.json_response({
                "blocks": info.blocks,
                "chain": info.chain,
                "difficulty": info.difficulty
            })
    except EvrmoreRPCError as e:
        return web.json_response({"error": str(e)}, status=500)

app = web.Application()
app.router.add_get('/blockchain/info', get_blockchain_info)

if __name__ == '__main__':
    web.run_app(app) 