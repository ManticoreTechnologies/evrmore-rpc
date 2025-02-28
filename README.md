# evrmore-rpc

A comprehensive, typed Python wrapper for Evrmore blockchain with ZMQ and WebSockets support.

[![PyPI version](https://badge.fury.io/py/evrmore-rpc.svg)](https://badge.fury.io/py/evrmore-rpc)
[![Python Versions](https://img.shields.io/pypi/pyversions/evrmore-rpc.svg)](https://pypi.org/project/evrmore-rpc/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.io/en/latest/?badge=latest)](https://evrmore-rpc.readthedocs.io/en/latest/?badge=latest)

## Overview

`evrmore-rpc` is a powerful Python library that provides a clean, typed interface to interact with the Evrmore blockchain. It offers both synchronous and asynchronous APIs, ZMQ support for real-time notifications, and WebSockets for building responsive applications.

## Features

- ✨ **Fully Typed API**: Complete type hints for all Evrmore commands with IDE autocomplete support
- 🚀 **Multiple APIs**: Choose between synchronous, asynchronous, or WebSockets interfaces
- 📡 **Real-time Updates**: ZMQ support for instant blockchain notifications
- 🔍 **Comprehensive Models**: Pydantic models for all blockchain data structures
- 🖥️ **CLI Tools**: Command-line interface for quick blockchain interactions
- 🎨 **Rich Output**: Beautiful terminal output with the Rich library
- 📚 **Extensive Documentation**: Detailed guides, API references, and examples
- 🧪 **Well-Tested**: Comprehensive test suite ensuring reliability

## Requirements

- Python 3.8 or higher
- evrmore-cli installed and accessible in your PATH
- ZMQ support in your Evrmore node (optional, for real-time notifications)

## Installation

```bash
# Basic installation
pip install evrmore-rpc

# With development tools
pip install evrmore-rpc[dev]

# With WebSockets support
pip install evrmore-rpc[websockets]

# Full installation with all features
pip install evrmore-rpc[full]
```

## Quick Start

```python
from evrmore_rpc import EvrmoreRPCClient

# Initialize client
client = EvrmoreRPCClient()

# Get blockchain info
info = client.getblockchaininfo()
print(f"Current block height: {info.blocks}")
print(f"Current difficulty: {info.difficulty}")

# List assets
assets = client.listassets()
print(f"Found {len(assets)} assets")

# Get a specific asset
asset_info = client.getassetdata("EVRMORE")
print(f"Asset details: {asset_info}")
```

## Usage Examples

### Synchronous API

```python
from evrmore_rpc import EvrmoreRPCClient

# Initialize with custom settings
client = EvrmoreRPCClient(
    datadir="~/.evrmore",
    rpcuser="myuser",
    rpcpassword="mypass",
    rpcport=8819,
    testnet=False
)

# Get block by hash
block = client.getblock(
    "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"
)
print(f"Block timestamp: {block.time}")
print(f"Block transactions: {len(block.tx)}")

# Issue an asset
result = client.issue(
    "MYASSET",
    1000,
    "EVRxxxxxxxxxxxxxxxxxxxxx",
    "EVRxxxxxxxxxxxxxxxxxxxxx"
)
print(f"Asset created with txid: {result}")
```

### Asynchronous API

```python
import asyncio
from evrmore_rpc import EvrmoreAsyncRPCClient

async def main():
    # Initialize the async client
    async with EvrmoreAsyncRPCClient() as client:
        # Get blockchain info
        info = await client.getblockchaininfo()
        print(f"Current block height: {info.blocks}")
        
        # Run multiple commands concurrently
        block_hash = await client.getblockhash(1)
        block, assets = await asyncio.gather(
            client.getblock(block_hash),
            client.listassets()
        )
        
        print(f"Block timestamp: {block.time}")
        print(f"Found {len(assets)} assets")

# Run the async function
asyncio.run(main())
```

### ZMQ Real-time Notifications

```python
import asyncio
from evrmore_rpc.zmq.client import EvrmoreZMQClient

async def main():
    # Create ZMQ client
    client = EvrmoreZMQClient()
    
    # Register transaction handler
    @client.on_transaction
    async def handle_transaction(notification):
        print(f"New transaction: {notification.hex}")
    
    # Register block handler
    @client.on_block
    async def handle_block(notification):
        print(f"New block: {notification.hex}")
    
    # Start client
    await client.start()

# Run the async function
asyncio.run(main())
```

### WebSockets API

```python
import asyncio
from evrmore_rpc.websockets import EvrmoreWebSocketClient

async def main():
    # Connect to WebSocket server
    async with EvrmoreWebSocketClient("ws://localhost:8820") as client:
        # Subscribe to new blocks
        await client.subscribe("blocks")
        
        # Handle incoming messages
        async for message in client:
            if message.type == "block":
                print(f"New block: {message.data.hash}")
            elif message.type == "transaction":
                print(f"New transaction: {message.data.txid}")

# Run the async function
asyncio.run(main())
```

### Command Line Interface

```bash
# Get blockchain info
evrmore-rpc getblockchaininfo

# Get block by hash
evrmore-rpc getblock "000000000019d6689c085ae165831e934ff763ae46a2a6c172b3f1b60a8ce26f"

# Get JSON output
evrmore-rpc --json getblockcount

# Start interactive mode
evrmore-rpc --interactive
```

## Example Applications

The package includes several example applications:

- **balance_tracker**: Track balances, transactions, and orders with a database backend
- **blockchain_explorer**: Real-time block and transaction viewer
- **asset_monitor**: Monitor asset issuance and transfers
- **wallet_tracker**: Track wallet balances and transactions
- **reward_distributor**: Distribute rewards to multiple addresses
- **network_monitor**: Monitor network statistics and peers

## Configuration

### Evrmore Node Configuration

To use ZMQ features, add these lines to your `evrmore.conf`:

```conf
# ZMQ configuration
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28332
zmqpubsequence=tcp://127.0.0.1:28332
```

### Library Configuration

Configure through command line:
```bash
evrmore-rpc --datadir ~/.evrmore --rpcuser myuser --rpcpassword mypass getinfo
```

Or in Python:
```python
# Synchronous client
client = EvrmoreRPCClient(
    datadir="~/.evrmore",
    rpcuser="myuser",
    rpcpassword="mypass",
    rpcport=8819
)

# Async client
async_client = EvrmoreAsyncRPCClient(
    datadir="~/.evrmore",
    rpcuser="myuser",
    rpcpassword="mypass",
    rpcport=8819
)
```

## Project Structure

```
evrmore-rpc/
├── evrmore_rpc/           # Main package
│   ├── __init__.py        # Package exports
│   ├── client.py          # Synchronous RPC client
│   ├── async_client.py    # Asynchronous RPC client
│   ├── cli.py             # Command-line interface
│   ├── interactive.py     # Interactive console
│   ├── utils.py           # Utility functions
│   ├── commands/          # RPC command wrappers
│   │   ├── __init__.py
│   │   ├── blockchain.py  # Blockchain commands
│   │   ├── assets.py      # Asset commands
│   │   └── ...
│   ├── models/            # Data models
│   │   ├── __init__.py
│   │   ├── base.py        # Base models
│   │   └── ...
│   ├── zmq/               # ZMQ support
│   │   ├── __init__.py
│   │   ├── client.py      # ZMQ client
│   │   ├── models.py      # ZMQ data models
│   │   └── utils.py       # ZMQ utilities
│   └── websockets/        # WebSockets support
│       ├── __init__.py
│       ├── client.py      # WebSocket client
│       ├── server.py      # WebSocket server
│       └── models.py      # WebSocket data models
├── examples/              # Example applications
│   ├── balance_tracker/   # Balance tracking example
│   ├── blockchain_explorer/ # Blockchain explorer example
│   └── ...
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── functional/        # Functional tests
├── docs/                  # Documentation
│   ├── api/               # API reference
│   ├── examples/          # Example documentation
│   └── tutorials/         # Tutorials
├── setup.py               # Package setup
├── pyproject.toml         # Project configuration
├── requirements.txt       # Dependencies
└── README.md              # This file
```

## Documentation

Full documentation is available at [https://evrmore-rpc.readthedocs.io/](https://evrmore-rpc.readthedocs.io/)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- The Evrmore development team for creating the blockchain
- All contributors to this project 