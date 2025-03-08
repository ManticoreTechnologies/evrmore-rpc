# EvrmoreClient Examples

This directory contains examples demonstrating how to use the EvrmoreClient library.

## Basic Examples

- **super_simple.py**: The simplest example showing the core functionality of the seamless API.
- **seamless_api.py**: A more comprehensive example demonstrating the seamless API in various scenarios.
- **simple_auto_detect.py**: Shows how the client automatically detects whether it's being used in a synchronous or asynchronous context.
- **simple_zmq.py**: Simple example demonstrating ZMQ notifications from the Evrmore blockchain.

## Advanced Examples

- **zmq_notifications.py**: Comprehensive example of receiving real-time blockchain notifications via ZMQ.
- **asset_monitor/monitor.py**: Real-time monitoring of asset transactions
- **blockchain_explorer/explorer.py**: Simple blockchain explorer implementation
- **wallet_tracker/tracker.py**: Track wallet balances and transactions.
- **network_monitor/monitor.py**: Monitor network health and peer connections.
- **asset_swap/simple_swap.py**: Simple asset swap platform.
- **balance_tracker/tracker.py**: Real-time balance tracking system.
- **reward_distributor/distributor.py**: Distribute rewards from mining or staking.

## Running the Examples

To run an example, simply execute it with Python:

```bash
python3 examples/super_simple.py
```

## Key Concepts

### Seamless API

The EvrmoreClient provides a seamless API that works in both synchronous and asynchronous contexts without requiring context managers:

```python
# Create a single client instance
client = EvrmoreClient()

# Use synchronously
info = client.getblockchaininfo()

# Use asynchronously
info = await client.getblockchaininfo()

# Clean up when done
await client.close()
```

### Resource Management

When using the client without context managers, it's important to clean up resources when you're done:

```python
# In async code
await client.close()

# In sync code
client.close_sync()
```

### Context Switching

When switching between sync and async contexts with the same client instance, reset the client state:

```python
# Use synchronously
info = client.getblockchaininfo()

# Reset before async usage
client.reset()

# Use asynchronously
info = await client.getblockchaininfo()
```

### ZMQ Notifications

The ZMQ client allows receiving real-time notifications from the Evrmore blockchain:

```python
from evrmore_rpc.zmq import EvrmoreZMQClient, ZMQTopic

# Create ZMQ client
zmq_client = EvrmoreZMQClient()

# Register handlers with decorators
@zmq_client.on(ZMQTopic.HASH_BLOCK)
async def on_new_block(notification):
    print(f"New block: {notification.hex}")

# Start client
await zmq_client.start()

# When done
await zmq_client.stop()
```

## Requirements

Basic examples require only the core `evrmore-rpc` package:

```bash
pip3 install evrmore-rpc
```

The ZMQ examples additionally require the `pyzmq` package, which is installed automatically when installing `evrmore-rpc` with the zmq extra:

```bash
pip3 install "evrmore-rpc[zmq]"
```

## Configuration

Most examples require a running Evrmore node. Make sure your node is properly configured in `evrmore.conf`:

```
# RPC settings
rpcuser=your_username
rpcpassword=your_password
rpcport=8819
server=1

# ZMQ settings (for ZMQ examples)
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
``` 