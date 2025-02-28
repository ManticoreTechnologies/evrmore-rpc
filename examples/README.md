# Evrmore RPC Examples

This directory contains examples demonstrating the functionality of the `evrmore-rpc` package.

## Example Categories

- [Asynchronous API](async/): Examples demonstrating the asynchronous API.
- [ZMQ](zmq/): Examples demonstrating ZMQ functionality for real-time blockchain notifications.
- [WebSockets](websockets/): Examples demonstrating WebSockets functionality for real-time blockchain events.
- [Balance Tracker](balance_tracker/): Example implementation of a balance tracker for NFT exchange integration.
- [Blockchain Explorer](blockchain_explorer/): Example implementation of a blockchain explorer.
- [Asset Monitor](asset_monitor/): Example implementation of an asset monitor.
- [Wallet Tracker](wallet_tracker/): Example implementation of a wallet tracker.
- [Network Monitor](network_monitor/): Example implementation of a network monitor.
- [Reward Distributor](reward_distributor/): Example implementation of a reward distributor.

## Running the Examples

Each example directory contains its own README with specific instructions for running the examples.

## Requirements

Basic examples require only the core `evrmore-rpc` package:

```bash
pip install evrmore-rpc
```

Advanced examples may require additional dependencies:

```bash
pip install evrmore-rpc[websockets]  # For WebSockets support
pip install evrmore-rpc[full]        # For all features
```

## Configuration

Most examples require a running Evrmore node. Make sure your node is properly configured in `evrmore.conf`:

```
# RPC settings
rpcuser=your_username
rpcpassword=your_password
rpcport=8819
server=1

# ZMQ notifications (for ZMQ and WebSockets examples)
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubsequence=tcp://127.0.0.1:28332
``` 