# Examples

The `evrmore-rpc` package includes several examples demonstrating its functionality. These examples are available in the [examples directory](https://github.com/ManticoreTechnology/evrmore-rpc/tree/main/examples) of the repository.

## Basic RPC Usage

The basic RPC usage examples demonstrate how to use the synchronous RPC client to interact with the Evrmore blockchain.

### Get Blockchain Info

```python
from evrmore_rpc import EvrmoreRPCClient

# Create a client
client = EvrmoreRPCClient()

# Get blockchain info
info = client.getblockchaininfo()
print(f"Current block height: {info.blocks}")
print(f"Chain: {info.chain}")
print(f"Difficulty: {info.difficulty}")
```

### Get Block Data

```python
from evrmore_rpc import EvrmoreRPCClient

# Create a client
client = EvrmoreRPCClient()

# Get a block
block_hash = client.getblockhash(1)
block = client.getblock(block_hash)
print(f"Block #1 hash: {block.hash}")
print(f"Block #1 time: {block.time}")
print(f"Block #1 transactions: {len(block.tx)}")
```

### List Assets

```python
from evrmore_rpc import EvrmoreRPCClient

# Create a client
client = EvrmoreRPCClient()

# List assets
assets = client.listassets()
print(f"Found {len(assets)} assets")

# List my assets
my_assets = client.listmyassets()
print(f"Found {len(my_assets)} assets in my wallet")
```

## Asynchronous RPC Usage

The asynchronous RPC usage examples demonstrate how to use the asynchronous RPC client to interact with the Evrmore blockchain.

### Get Blockchain Info

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

async def main():
    # Create a client
    async with EvrmoreAsyncRPCClient() as client:
        # Get blockchain info
        info = await client.getblockchaininfo()
        print(f"Current block height: {info.blocks}")
        print(f"Chain: {info.chain}")
        print(f"Difficulty: {info.difficulty}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Concurrent Execution

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

async def main():
    # Create a client
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

if __name__ == "__main__":
    asyncio.run(main())
```

## ZMQ Notifications

The ZMQ notifications examples demonstrate how to use the ZMQ client to receive real-time notifications from the Evrmore blockchain.

### Block and Transaction Notifications

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

### Transaction Analysis

```python
import asyncio
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

async def handle_transaction(notification):
    txid = notification.hex
    print(f"New transaction: {txid}")
    
    # Get transaction details
    client = EvrmoreRPCClient()
    tx = client.getrawtransaction(txid, True)
    
    # Analyze transaction
    print(f"Transaction size: {tx.size} bytes")
    print(f"Transaction inputs: {len(tx.vin)}")
    print(f"Transaction outputs: {len(tx.vout)}")
    
    # Check for asset transfers
    for vout in tx.vout:
        if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
            asset = vout["scriptPubKey"]["asset"]
            print(f"Asset transfer: {asset['name']} ({asset['amount']})")

async def main():
    # Create a ZMQ client
    client = EvrmoreZMQClient(
        address="tcp://127.0.0.1:28332",
        topics=[ZMQTopic.HASH_TX]
    )
    
    # Register handler
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

## WebSockets Support

The WebSockets examples demonstrate how to use the WebSockets client and server to receive real-time notifications from the Evrmore blockchain.

### WebSocket Client

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

### WebSocket Server

```python
import asyncio
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient
from evrmore_rpc.websockets import EvrmoreWebSocketServer

async def main():
    # Create RPC client
    rpc_client = EvrmoreRPCClient()
    
    # Create ZMQ client
    zmq_client = EvrmoreZMQClient(
        address="tcp://127.0.0.1:28332"
    )
    
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

## Asset Swap Platform

The asset swap platform example demonstrates how to build a decentralized exchange for Evrmore assets using the `evrmore-rpc` package.

### Simple Swap

```python
import asyncio
from decimal import Decimal
from evrmore_rpc import EvrmoreRPCClient

class AssetSwap:
    def __init__(self):
        self.client = EvrmoreRPCClient()
        
    def list_my_assets(self):
        """List assets in my wallet."""
        assets = self.client.listmyassets()
        return assets
        
    def create_swap_offer(self, asset_offered, amount_offered, asset_wanted, amount_wanted):
        """Create a swap offer."""
        # In a real implementation, this would create a transaction or smart contract
        print(f"Creating swap offer: {amount_offered} {asset_offered} for {amount_wanted} {asset_wanted}")
        
    def execute_swap(self, offer_id):
        """Execute a swap offer."""
        # In a real implementation, this would execute the transaction or smart contract
        print(f"Executing swap offer {offer_id}")

async def main():
    swap = AssetSwap()
    
    # List my assets
    assets = swap.list_my_assets()
    print("My assets:")
    for asset, amount in assets.items():
        print(f"  {asset}: {amount}")
    
    # Create a swap offer
    swap.create_swap_offer("ASSET_A", Decimal("10"), "ASSET_B", Decimal("20"))
    
    # Execute a swap offer
    swap.execute_swap("offer_id")

if __name__ == "__main__":
    asyncio.run(main())
```

### Real-time Swap

```python
import asyncio
import json
from decimal import Decimal
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient

class RealTimeAssetSwap:
    def __init__(self):
        self.rpc_client = EvrmoreRPCClient()
        self.zmq_client = EvrmoreZMQClient()
        self.offers = []
        
    async def start(self):
        """Start the swap platform."""
        # Register ZMQ handlers
        self.zmq_client.on_transaction(self.handle_transaction)
        
        # Start ZMQ client
        await self.zmq_client.start()
        
    async def stop(self):
        """Stop the swap platform."""
        await self.zmq_client.stop()
        
    async def handle_transaction(self, notification):
        """Handle a new transaction."""
        txid = notification.hex
        print(f"New transaction: {txid}")
        
        # Get transaction details
        tx = self.rpc_client.getrawtransaction(txid, True)
        
        # Check for asset transfers
        for vout in tx.vout:
            if "asset" in vout.get("scriptPubKey", {}).get("asset", {}):
                asset = vout["scriptPubKey"]["asset"]
                print(f"Asset transfer: {asset['name']} ({asset['amount']})")
                
                # Check if this transfer matches any of our offers
                self.check_for_matching_offers(asset["name"], Decimal(str(asset["amount"])))
    
    def check_for_matching_offers(self, asset_name, amount):
        """Check if an asset transfer matches any of our offers."""
        for offer in self.offers:
            if offer["status"] == "open" and offer["asset_wanted"] == asset_name and offer["amount_wanted"] == amount:
                print(f"Found matching offer: {offer['id']}")
                
                # Execute the swap
                self.execute_swap(offer["id"])
    
    def create_swap_offer(self, asset_offered, amount_offered, asset_wanted, amount_wanted):
        """Create a swap offer."""
        offer_id = f"offer_{len(self.offers)}"
        offer = {
            "id": offer_id,
            "asset_offered": asset_offered,
            "amount_offered": amount_offered,
            "asset_wanted": asset_wanted,
            "amount_wanted": amount_wanted,
            "status": "open"
        }
        self.offers.append(offer)
        print(f"Created swap offer: {offer_id}")
        return offer_id
    
    def execute_swap(self, offer_id):
        """Execute a swap offer."""
        for offer in self.offers:
            if offer["id"] == offer_id and offer["status"] == "open":
                print(f"Executing swap offer: {offer_id}")
                
                # In a real implementation, this would execute the transaction
                offer["status"] = "completed"
                print(f"Swap offer {offer_id} completed")
                return True
        
        print(f"Swap offer {offer_id} not found or not open")
        return False

async def main():
    swap = RealTimeAssetSwap()
    
    # Start the swap platform
    await swap.start()
    
    # Create a swap offer
    offer_id = swap.create_swap_offer("ASSET_A", Decimal("10"), "ASSET_B", Decimal("20"))
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await swap.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Balance Tracker

The balance tracker example demonstrates how to track asset balances in real-time using the `evrmore-rpc` package.

```python
import asyncio
from decimal import Decimal
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient

class BalanceTracker:
    def __init__(self):
        self.rpc_client = EvrmoreRPCClient()
        self.zmq_client = EvrmoreZMQClient()
        self.balances = {}
        self.addresses = []
        
    async def start(self):
        """Start the balance tracker."""
        # Register ZMQ handlers
        self.zmq_client.on_transaction(self.handle_transaction)
        
        # Start ZMQ client
        await self.zmq_client.start()
        
    async def stop(self):
        """Stop the balance tracker."""
        await self.zmq_client.stop()
        
    def add_address(self, address):
        """Add an address to track."""
        self.addresses.append(address)
        
        # Get current balances
        balances = self.rpc_client.getaddressbalance({"addresses": [address]})
        
        # Store balances
        self.balances[address] = {
            "EVR": Decimal(str(balances["balance"] / 100000000)),
            "assets": {}
        }
        
        # Get asset balances
        assets = self.rpc_client.getaddressutxos({"addresses": [address]})
        for utxo in assets:
            if "asset" in utxo:
                asset_name = utxo["asset"]["name"]
                asset_amount = Decimal(str(utxo["asset"]["amount"]))
                
                if asset_name in self.balances[address]["assets"]:
                    self.balances[address]["assets"][asset_name] += asset_amount
                else:
                    self.balances[address]["assets"][asset_name] = asset_amount
        
        print(f"Added address: {address}")
        print(f"  EVR balance: {self.balances[address]['EVR']}")
        print(f"  Asset balances: {self.balances[address]['assets']}")
        
    async def handle_transaction(self, notification):
        """Handle a new transaction."""
        txid = notification.hex
        
        # Get transaction details
        tx = self.rpc_client.getrawtransaction(txid, True)
        
        # Check for transfers to/from tracked addresses
        for vout in tx.vout:
            if "addresses" in vout.get("scriptPubKey", {}):
                for address in vout["scriptPubKey"]["addresses"]:
                    if address in self.addresses:
                        # Update EVR balance
                        amount = Decimal(str(vout["value"]))
                        self.balances[address]["EVR"] += amount
                        print(f"Updated EVR balance for {address}: {self.balances[address]['EVR']}")
                        
                        # Update asset balance
                        if "asset" in vout.get("scriptPubKey", {}):
                            asset = vout["scriptPubKey"]["asset"]
                            asset_name = asset["name"]
                            asset_amount = Decimal(str(asset["amount"]))
                            
                            if asset_name in self.balances[address]["assets"]:
                                self.balances[address]["assets"][asset_name] += asset_amount
                            else:
                                self.balances[address]["assets"][asset_name] = asset_amount
                                
                            print(f"Updated asset balance for {address}: {asset_name} = {self.balances[address]['assets'][asset_name]}")
        
        # Check for transfers from tracked addresses
        for vin in tx.vin:
            if "txid" in vin and "vout" in vin:
                prev_tx = self.rpc_client.getrawtransaction(vin["txid"], True)
                prev_vout = prev_tx.vout[vin["vout"]]
                
                if "addresses" in prev_vout.get("scriptPubKey", {}):
                    for address in prev_vout["scriptPubKey"]["addresses"]:
                        if address in self.addresses:
                            # Update EVR balance
                            amount = Decimal(str(prev_vout["value"]))
                            self.balances[address]["EVR"] -= amount
                            print(f"Updated EVR balance for {address}: {self.balances[address]['EVR']}")
                            
                            # Update asset balance
                            if "asset" in prev_vout.get("scriptPubKey", {}):
                                asset = prev_vout["scriptPubKey"]["asset"]
                                asset_name = asset["name"]
                                asset_amount = Decimal(str(asset["amount"]))
                                
                                if asset_name in self.balances[address]["assets"]:
                                    self.balances[address]["assets"][asset_name] -= asset_amount
                                    print(f"Updated asset balance for {address}: {asset_name} = {self.balances[address]['assets'][asset_name]}")

async def main():
    tracker = BalanceTracker()
    
    # Start the balance tracker
    await tracker.start()
    
    # Add addresses to track
    tracker.add_address("EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    tracker.add_address("EVRyyyyyyyyyyyyyyyyyyyyyyyyyyyyy")
    
    # Keep running until interrupted
    try:
        while True:
            await asyncio.sleep(1)
    finally:
        await tracker.stop()

if __name__ == "__main__":
    asyncio.run(main())
```

## Interactive Dashboard

The interactive dashboard example demonstrates how to build a real-time dashboard for monitoring the Evrmore blockchain using the `evrmore-rpc` package.

```python
import asyncio
import datetime
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.live import Live
from evrmore_rpc import EvrmoreRPCClient
from evrmore_rpc.zmq import EvrmoreZMQClient

class EvrmoreMonitor:
    def __init__(self):
        self.rpc_client = EvrmoreRPCClient()
        self.zmq_client = EvrmoreZMQClient()
        self.console = Console()
        self.layout = Layout()
        self.recent_blocks = []
        self.recent_transactions = []
        self.mempool_stats = {"size": 0, "bytes": 0, "usage": 0}
        self.network_stats = {"connections": 0, "version": "", "subversion": "", "protocolversion": 0}
        self.blockchain_stats = {"blocks": 0, "headers": 0, "difficulty": 0, "chain": ""}
        
    async def start(self):
        """Start the monitor."""
        # Register ZMQ handlers
        self.zmq_client.on_block(self.handle_block)
        self.zmq_client.on_transaction(self.handle_transaction)
        
        # Start ZMQ client
        await self.zmq_client.start()
        
        # Initialize data
        await self.update_blockchain_stats()
        await self.update_network_stats()
        await self.update_mempool_stats()
        await self.update_recent_blocks()
        
    async def stop(self):
        """Stop the monitor."""
        await self.zmq_client.stop()
        
    async def handle_block(self, notification):
        """Handle a new block."""
        block_hash = notification.hex
        
        # Get block details
        block = self.rpc_client.getblock(block_hash)
        
        # Add to recent blocks
        self.recent_blocks.insert(0, {
            "hash": block.hash,
            "height": block.height,
            "time": datetime.datetime.fromtimestamp(block.time),
            "txs": len(block.tx),
            "size": block.size
        })
        
        # Keep only the 10 most recent blocks
        self.recent_blocks = self.recent_blocks[:10]
        
        # Update stats
        await self.update_blockchain_stats()
        await self.update_mempool_stats()
        
    async def handle_transaction(self, notification):
        """Handle a new transaction."""
        txid = notification.hex
        
        # Get transaction details
        try:
            tx = self.rpc_client.getrawtransaction(txid, True)
            
            # Add to recent transactions
            self.recent_transactions.insert(0, {
                "txid": tx.txid,
                "size": tx.size,
                "vsize": tx.vsize,
                "time": datetime.datetime.now(),
                "inputs": len(tx.vin),
                "outputs": len(tx.vout)
            })
            
            # Keep only the 10 most recent transactions
            self.recent_transactions = self.recent_transactions[:10]
            
            # Update mempool stats
            await self.update_mempool_stats()
        except:
            # Transaction might not be in mempool yet
            pass
        
    async def update_blockchain_stats(self):
        """Update blockchain statistics."""
        info = self.rpc_client.getblockchaininfo()
        self.blockchain_stats = {
            "blocks": info.blocks,
            "headers": info.headers,
            "difficulty": info.difficulty,
            "chain": info.chain
        }
        
    async def update_network_stats(self):
        """Update network statistics."""
        info = self.rpc_client.getnetworkinfo()
        self.network_stats = {
            "connections": info.connections,
            "version": info.version,
            "subversion": info.subversion,
            "protocolversion": info.protocolversion
        }
        
    async def update_mempool_stats(self):
        """Update mempool statistics."""
        info = self.rpc_client.getmempoolinfo()
        self.mempool_stats = {
            "size": info["size"],
            "bytes": info["bytes"],
            "usage": info["usage"]
        }
        
    async def update_recent_blocks(self):
        """Update recent blocks."""
        # Get current block height
        height = self.rpc_client.getblockcount()
        
        # Get the 10 most recent blocks
        for i in range(height, max(0, height - 10), -1):
            block_hash = self.rpc_client.getblockhash(i)
            block = self.rpc_client.getblock(block_hash)
            
            self.recent_blocks.append({
                "hash": block.hash,
                "height": block.height,
                "time": datetime.datetime.fromtimestamp(block.time),
                "txs": len(block.tx),
                "size": block.size
            })
        
    def render_dashboard(self):
        """Render the dashboard."""
        self.layout.split(
            Layout(name="header", size=3),
            Layout(name="main"),
            Layout(name="footer", size=3)
        )
        
        self.layout["main"].split_row(
            Layout(name="left"),
            Layout(name="right")
        )
        
        self.layout["left"].split(
            Layout(name="blockchain", size=10),
            Layout(name="blocks")
        )
        
        self.layout["right"].split(
            Layout(name="network", size=10),
            Layout(name="mempool", size=10),
            Layout(name="transactions")
        )
        
        # Header
        self.layout["header"].update(
            Panel(
                f"Evrmore Blockchain Monitor - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style="bold white on blue"
            )
        )
        
        # Blockchain stats
        blockchain_table = Table(title="Blockchain Stats")
        blockchain_table.add_column("Stat")
        blockchain_table.add_column("Value")
        blockchain_table.add_row("Chain", self.blockchain_stats["chain"])
        blockchain_table.add_row("Blocks", str(self.blockchain_stats["blocks"]))
        blockchain_table.add_row("Headers", str(self.blockchain_stats["headers"]))
        blockchain_table.add_row("Difficulty", f"{self.blockchain_stats['difficulty']:.8f}")
        self.layout["blockchain"].update(blockchain_table)
        
        # Network stats
        network_table = Table(title="Network Stats")
        network_table.add_column("Stat")
        network_table.add_column("Value")
        network_table.add_row("Connections", str(self.network_stats["connections"]))
        network_table.add_row("Version", str(self.network_stats["version"]))
        network_table.add_row("Subversion", self.network_stats["subversion"])
        network_table.add_row("Protocol", str(self.network_stats["protocolversion"]))
        self.layout["network"].update(network_table)
        
        # Mempool stats
        mempool_table = Table(title="Mempool Stats")
        mempool_table.add_column("Stat")
        mempool_table.add_column("Value")
        mempool_table.add_row("Transactions", str(self.mempool_stats["size"]))
        mempool_table.add_row("Size", f"{self.mempool_stats['bytes'] / 1024 / 1024:.2f} MB")
        mempool_table.add_row("Memory Usage", f"{self.mempool_stats['usage'] / 1024 / 1024:.2f} MB")
        self.layout["mempool"].update(mempool_table)
        
        # Recent blocks
        blocks_table = Table(title="Recent Blocks")
        blocks_table.add_column("Height")
        blocks_table.add_column("Hash")
        blocks_table.add_column("Time")
        blocks_table.add_column("Txs")
        blocks_table.add_column("Size")
        
        for block in self.recent_blocks:
            blocks_table.add_row(
                str(block["height"]),
                block["hash"][:10] + "...",
                block["time"].strftime("%H:%M:%S"),
                str(block["txs"]),
                f"{block['size'] / 1024:.2f} KB"
            )
            
        self.layout["blocks"].update(blocks_table)
        
        # Recent transactions
        txs_table = Table(title="Recent Transactions")
        txs_table.add_column("TxID")
        txs_table.add_column("Time")
        txs_table.add_column("Size")
        txs_table.add_column("Inputs")
        txs_table.add_column("Outputs")
        
        for tx in self.recent_transactions:
            txs_table.add_row(
                tx["txid"][:10] + "...",
                tx["time"].strftime("%H:%M:%S"),
                f"{tx['size']} bytes",
                str(tx["inputs"]),
                str(tx["outputs"])
            )
            
        self.layout["transactions"].update(txs_table)
        
        # Footer
        self.layout["footer"].update(
            Panel(
                "Press Ctrl+C to exit",
                style="bold white on blue"
            )
        )
        
        return self.layout

async def main():
    monitor = EvrmoreMonitor()
    
    # Start the monitor
    await monitor.start()
    
    # Create a live display
    with Live(monitor.render_dashboard(), refresh_per_second=1) as live:
        try:
            while True:
                # Update the display
                live.update(monitor.render_dashboard())
                
                # Wait a bit
                await asyncio.sleep(1)
        finally:
            await monitor.stop()

if __name__ == "__main__":
    asyncio.run(main()) 