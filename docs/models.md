# Data Models

The `evrmore-rpc` package provides a set of data models for working with Evrmore blockchain data. These models are implemented using [Pydantic](https://pydantic-docs.helpmanual.io/), which provides data validation, serialization, and documentation features.

## Base Models

The base models are defined in the `evrmore_rpc.models.base` module.

### Amount

The `Amount` model represents a monetary amount in the Evrmore blockchain.

```python
from evrmore_rpc.models.base import Amount

# Create an amount
amount = Amount(value=1.23456789)

# Access properties
print(amount.value)  # 1.23456789
print(float(amount))  # 1.23456789
print(str(amount))  # "1.23456789"
```

### Address

The `Address` model represents an Evrmore address.

```python
from evrmore_rpc.models.base import Address

# Create an address
address = Address(value="EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

# Access properties
print(address.value)  # "EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
print(str(address))  # "EVRxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### Asset

The `Asset` model represents an Evrmore asset.

```python
from evrmore_rpc.models.base import Asset

# Create an asset
asset = Asset(
    name="ASSET_NAME",
    amount=1000,
    units=0,
    reissuable=True,
    has_ipfs=False
)

# Access properties
print(asset.name)  # "ASSET_NAME"
print(asset.amount)  # 1000
print(asset.units)  # 0
print(asset.reissuable)  # True
print(asset.has_ipfs)  # False
```

### Transaction

The `Transaction` model represents a transaction in the Evrmore blockchain.

```python
from evrmore_rpc.models.base import Transaction

# Create a transaction
transaction = Transaction(
    txid="txid",
    hash="hash",
    version=1,
    size=225,
    vsize=225,
    weight=900,
    locktime=0,
    vin=[...],
    vout=[...],
    hex="hex",
    blockhash="blockhash",
    confirmations=1,
    time=1234567890,
    blocktime=1234567890
)

# Access properties
print(transaction.txid)  # "txid"
print(transaction.hash)  # "hash"
print(transaction.confirmations)  # 1
```

### Block

The `Block` model represents a block in the Evrmore blockchain.

```python
from evrmore_rpc.models.base import Block

# Create a block
block = Block(
    hash="hash",
    confirmations=1,
    size=1234,
    strippedsize=1234,
    weight=4936,
    height=123456,
    version=536870912,
    versionHex="20000000",
    merkleroot="merkleroot",
    tx=["txid1", "txid2"],
    time=1234567890,
    mediantime=1234567890,
    nonce=1234567890,
    bits="1d00ffff",
    difficulty=1.23456789,
    chainwork="chainwork",
    previousblockhash="previousblockhash",
    nextblockhash="nextblockhash"
)

# Access properties
print(block.hash)  # "hash"
print(block.height)  # 123456
print(block.time)  # 1234567890
print(len(block.tx))  # 2
```

### RPCResponse

The `RPCResponse` model represents a response from the Evrmore RPC API.

```python
from evrmore_rpc.models.base import RPCResponse

# Create a response
response = RPCResponse(
    result={"key": "value"},
    error=None,
    id="1"
)

# Access properties
print(response.result)  # {"key": "value"}
print(response.error)  # None
print(response.id)  # "1"
```

## Blockchain Models

The blockchain models are defined in the `evrmore_rpc.commands.blockchain` module.

### BlockchainInfo

The `BlockchainInfo` model represents information about the blockchain.

```python
from evrmore_rpc.commands.blockchain import BlockchainInfo

# Create blockchain info
info = BlockchainInfo(
    chain="main",
    blocks=123456,
    headers=123456,
    bestblockhash="hash",
    difficulty=1.23456789,
    mediantime=1234567890,
    verificationprogress=1.0,
    initialblockdownload=False,
    chainwork="chainwork",
    size_on_disk=1234567890,
    pruned=False,
    softforks={},
    bip9_softforks={}
)

# Access properties
print(info.chain)  # "main"
print(info.blocks)  # 123456
print(info.difficulty)  # 1.23456789
```

### BlockHeader

The `BlockHeader` model represents a block header.

```python
from evrmore_rpc.commands.blockchain import BlockHeader

# Create a block header
header = BlockHeader(
    hash="hash",
    confirmations=1,
    height=123456,
    version=536870912,
    versionHex="20000000",
    merkleroot="merkleroot",
    time=1234567890,
    mediantime=1234567890,
    nonce=1234567890,
    bits="1d00ffff",
    difficulty=1.23456789,
    chainwork="chainwork",
    previousblockhash="previousblockhash",
    nextblockhash="nextblockhash"
)

# Access properties
print(header.hash)  # "hash"
print(header.height)  # 123456
print(header.time)  # 1234567890
```

## Asset Models

The asset models are defined in the `evrmore_rpc.commands.assets` module.

### AssetInfo

The `AssetInfo` model represents information about an asset.

```python
from evrmore_rpc.commands.assets import AssetInfo

# Create asset info
info = AssetInfo(
    name="ASSET_NAME",
    amount=1000,
    units=0,
    reissuable=True,
    has_ipfs=False,
    block_height=123456,
    blockhash="blockhash",
    txid="txid",
    vout=0,
    divisibility=0,
    locked=False,
    ipfs_hash=""
)

# Access properties
print(info.name)  # "ASSET_NAME"
print(info.amount)  # 1000
print(info.units)  # 0
print(info.reissuable)  # True
```

### ListAssetsResult

The `ListAssetsResult` model represents the result of the `listassets` command.

```python
from evrmore_rpc.commands.assets import ListAssetsResult, AssetInfo

# Create a list assets result
result = ListAssetsResult(
    assets={
        "ASSET_1": AssetInfo(...),
        "ASSET_2": AssetInfo(...)
    },
    count=2
)

# Access properties
print(result.count)  # 2
print(len(result.assets))  # 2
print(result.assets["ASSET_1"].name)  # "ASSET_1"
```

## Network Models

The network models are defined in the `evrmore_rpc.commands.network` module.

### NetworkInfo

The `NetworkInfo` model represents information about the network.

```python
from evrmore_rpc.commands.network import NetworkInfo

# Create network info
info = NetworkInfo(
    version=1234567,
    subversion="/Evrmore:1.2.3/",
    protocolversion=70016,
    localservices="000000000000040d",
    localrelay=True,
    timeoffset=0,
    connections=8,
    networkactive=True,
    networks=[...],
    relayfee=0.00001,
    incrementalfee=0.00001,
    localaddresses=[...],
    warnings=""
)

# Access properties
print(info.version)  # 1234567
print(info.subversion)  # "/Evrmore:1.2.3/"
print(info.connections)  # 8
```

### PeerInfo

The `PeerInfo` model represents information about a peer.

```python
from evrmore_rpc.commands.network import PeerInfo

# Create peer info
info = PeerInfo(
    id=1,
    addr="127.0.0.1:8819",
    addrbind="127.0.0.1:8819",
    addrlocal="127.0.0.1:8819",
    services="000000000000040d",
    relaytxes=True,
    lastsend=1234567890,
    lastrecv=1234567890,
    bytessent=1234,
    bytesrecv=1234,
    conntime=1234567890,
    timeoffset=0,
    pingtime=0.123,
    minping=0.123,
    version=70016,
    subver="/Evrmore:1.2.3/",
    inbound=False,
    addnode=False,
    startingheight=123456,
    banscore=0,
    synced_headers=123456,
    synced_blocks=123456,
    inflight=[],
    whitelisted=False,
    permissions=[],
    minfeefilter=0.00001
)

# Access properties
print(info.id)  # 1
print(info.addr)  # "127.0.0.1:8819"
print(info.version)  # 70016
```

## Mining Models

The mining models are defined in the `evrmore_rpc.commands.mining` module.

### MiningInfo

The `MiningInfo` model represents information about mining.

```python
from evrmore_rpc.commands.mining import MiningInfo

# Create mining info
info = MiningInfo(
    blocks=123456,
    currentblockweight=4000,
    currentblocktx=100,
    difficulty=1.23456789,
    networkhashps=1234567890,
    pooledtx=100,
    chain="main",
    warnings=""
)

# Access properties
print(info.blocks)  # 123456
print(info.difficulty)  # 1.23456789
print(info.networkhashps)  # 1234567890
```

## Utility Models

The utility models are defined in the `evrmore_rpc.commands.util` module.

### UtilInfo

The `UtilInfo` model represents utility information.

```python
from evrmore_rpc.commands.util import UtilInfo

# Create utility info
info = UtilInfo(
    version=1234567,
    protocolversion=70016,
    walletversion=60000,
    balance=1.23456789,
    blocks=123456,
    timeoffset=0,
    connections=8,
    proxy="",
    difficulty=1.23456789,
    testnet=False,
    keypoololdest=1234567890,
    keypoolsize=1000,
    unlocked_until=0,
    paytxfee=0.00001,
    relayfee=0.00001,
    errors=""
)

# Access properties
print(info.version)  # 1234567
print(info.balance)  # 1.23456789
print(info.blocks)  # 123456
```

## WebSocket Models

The WebSocket models are defined in the `evrmore_rpc.websockets.models` module.

### WebSocketMessage

The `WebSocketMessage` model represents a WebSocket message.

```python
from evrmore_rpc.websockets.models import WebSocketMessage

# Create a WebSocket message
message = WebSocketMessage(
    type="block",
    data={
        "hash": "hash",
        "height": 123456,
        "time": 1234567890
    }
)

# Access properties
print(message.type)  # "block"
print(message.data["hash"])  # "hash"
print(message.data["height"])  # 123456
```

### WebSocketSubscription

The `WebSocketSubscription` model represents a WebSocket subscription.

```python
from evrmore_rpc.websockets.models import WebSocketSubscription

# Create a WebSocket subscription
subscription = WebSocketSubscription(
    topic="blocks",
    client_id="client_id"
)

# Access properties
print(subscription.topic)  # "blocks"
print(subscription.client_id)  # "client_id"
```

## ZMQ Models

The ZMQ models are defined in the `evrmore_rpc.zmq.models` module.

### ZMQNotification

The `ZMQNotification` model represents a ZMQ notification.

```python
from evrmore_rpc.zmq.models import ZMQNotification
from evrmore_rpc.zmq.client import ZMQTopic

# Create a ZMQ notification
notification = ZMQNotification(
    topic=ZMQTopic.HASH_BLOCK,
    body=b"block_hash",
    sequence=123456
)

# Access properties
print(notification.topic)  # ZMQTopic.HASH_BLOCK
print(notification.body)  # b"block_hash"
print(notification.sequence)  # 123456
print(notification.hex)  # "626c6f636b5f68617368" (hexadecimal representation of body)
``` 