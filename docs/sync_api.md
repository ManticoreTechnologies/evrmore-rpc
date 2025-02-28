# Synchronous API

The `evrmore-rpc` package provides a synchronous API for interacting with the Evrmore blockchain.

## Installation

```bash
pip install evrmore-rpc
```

## EvrmoreRPCClient Class

The `EvrmoreRPCClient` class is the main entry point for the synchronous API. It provides a clean interface with autocomplete support for all Evrmore RPC commands.

### Initialization

```python
from evrmore_rpc import EvrmoreRPCClient

# Create a client with default settings
client = EvrmoreRPCClient()

# Create a client with custom settings
client = EvrmoreRPCClient(
    datadir="/path/to/evrmore/data",
    rpcuser="username",
    rpcpassword="password",
    rpcport=8819,
    testnet=False
)
```

### Parameters

- `datadir` (Optional[Path]): Path to the Evrmore data directory
- `rpcuser` (Optional[str]): RPC username
- `rpcpassword` (Optional[str]): RPC password
- `rpcport` (Optional[int]): RPC port
- `testnet` (bool): Whether to use testnet (default: False)

### Blockchain Commands

```python
from evrmore_rpc import EvrmoreRPCClient

client = EvrmoreRPCClient()

# Get blockchain info
info = client.getblockchaininfo()
print(f"Current block height: {info.blocks}")
print(f"Chain: {info.chain}")
print(f"Difficulty: {info.difficulty}")

# Get a block by height
height = 100
block_hash = client.getblockhash(height)
block = client.getblock(block_hash)
print(f"Block hash: {block.hash}")
print(f"Block time: {block.time}")
print(f"Transactions: {len(block.tx)}")
```

### Asset Commands

```python
from evrmore_rpc import EvrmoreRPCClient

client = EvrmoreRPCClient()

# List assets
assets = client.listassets()
for name, amount in assets.items():
    print(f"Asset: {name}, Supply: {amount}")

# Get asset data
asset_data = client.getassetdata("ASSET_NAME")
print(f"Asset: {asset_data.name}")
print(f"Amount: {asset_data.amount}")
print(f"Units: {asset_data.units}")
print(f"Reissuable: {asset_data.reissuable}")

# Issue a new asset
txid = client.issue(
    asset_name="NEW_ASSET",
    qty=1000,
    to_address="EVRaddress",
    units=0,
    reissuable=True,
    has_ipfs=False
)
print(f"Asset issued with transaction ID: {txid}")

# Transfer an asset
txid = client.transfer(
    asset_name="ASSET_NAME",
    qty=100,
    to_address="EVRaddress"
)
print(f"Asset transferred with transaction ID: {txid}")
```

### Wallet Commands

```python
from evrmore_rpc import EvrmoreRPCClient

client = EvrmoreRPCClient()

# Get wallet info
wallet_info = client.getwalletinfo()
print(f"Balance: {wallet_info.balance}")
print(f"Unconfirmed balance: {wallet_info.unconfirmed_balance}")
print(f"Immature balance: {wallet_info.immature_balance}")

# Send to address
txid = client.sendtoaddress("EVRaddress", 1.0, "payment", "from", False)
print(f"Transaction ID: {txid}")

# List transactions
transactions = client.listtransactions()
for tx in transactions:
    print(f"Transaction: {tx.txid}")
    print(f"Amount: {tx.amount}")
    print(f"Confirmations: {tx.confirmations}")
```

### Raw Transaction Commands

```python
from evrmore_rpc import EvrmoreRPCClient

client = EvrmoreRPCClient()

# Create a raw transaction
inputs = [{"txid": "txid", "vout": 0}]
outputs = {"EVRaddress": 1.0}
raw_tx = client.createrawtransaction(inputs, outputs)

# Sign the raw transaction
signed_tx = client.signrawtransaction(raw_tx)

# Send the raw transaction
txid = client.sendrawtransaction(signed_tx.hex)
print(f"Transaction ID: {txid}")
```

## Error Handling

The `EvrmoreRPCClient` class raises `EvrmoreRPCError` exceptions when an error occurs.

```python
from evrmore_rpc import EvrmoreRPCClient, EvrmoreRPCError

client = EvrmoreRPCClient()

try:
    # Try to get a non-existent block
    block = client.getblock("invalid_hash")
except EvrmoreRPCError as e:
    print(f"Error: {e}")
```

## Direct Command Execution

The `EvrmoreRPCClient` class also provides a `execute_command` method for executing commands directly.

```python
from evrmore_rpc import EvrmoreRPCClient

client = EvrmoreRPCClient()

# Execute a command directly
result = client.execute_command("getblockchaininfo")
print(f"Chain: {result['chain']}")
```

## Command Line Interface

The `evrmore-rpc` package also provides a command-line interface for executing RPC commands.

```bash
# Get blockchain info
evrmore-rpc getblockchaininfo

# Get a block by height
evrmore-rpc getblockhash 100 | evrmore-rpc getblock -

# List assets
evrmore-rpc listassets
```

For more information on the command-line interface, see the [CLI documentation](index.md#command-line-interface). 