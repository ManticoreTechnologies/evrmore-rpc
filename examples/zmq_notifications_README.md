# Evrmore ZMQ Notifications Example

This example demonstrates how to use the `EvrmoreZMQClient` to receive real-time notifications from the Evrmore blockchain. It showcases:

- Setting up the ZMQ client with various notification topics
- Registering handlers for different notification types
- Starting and stopping the client correctly
- Processing block and transaction notifications
- Using the RPC client alongside ZMQ for additional data lookups

## Prerequisites

1. A running Evrmore node with ZMQ enabled
2. Python 3.7 or higher
3. `evrmore-rpc` package installed

## Configuring Your Evrmore Node

For this example to work, you must enable ZMQ in your Evrmore node configuration. Add the following lines to your `evrmore.conf` file:

```
# ZMQ settings
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubrawtx=tcp://127.0.0.1:28332
zmqpubrawblock=tcp://127.0.0.1:28332
```

Then restart your Evrmore node.

## Running the Example

```bash
python3 examples/zmq_notifications.py
```

## Expected Output

When running the example, you should see output similar to the following:

```
Starting ZMQ notification monitor...
Press Ctrl+C to exit
ZMQ client started

=== ZMQ Notification Monitor ===
Uptime: 10.1 seconds
Blocks seen: 0 (last: never)
Transactions seen: 0 (last: never)
Asset transactions: 0
================================

New transaction: 6a39ee543e465e2a5b6a1322f06145c49717283eb39d60976c316d5880db6227
Raw transaction received: 246 bytes

New block: 00000000000000128255f2d16af430d9b73aa8fd7bf9981c0c6fa34af5a4acb0
Raw block received: 3285 bytes
Block height: 1234567, Transactions: 12

=== ZMQ Notification Monitor ===
Uptime: 20.2 seconds
Blocks seen: 1 (last: 10.1 seconds ago)
Transactions seen: 1 (last: 10.1 seconds ago)
Latest block: 00000000000000128255f2d16af430d9b73aa8fd7bf9981c0c6fa34af5a4acb0
Latest transaction: 6a39ee543e465e2a5b6a1322f06145c49717283eb39d60976c316d5880db6227
Asset transactions: 0
================================
```

## Understanding the Example

The example code:

1. Creates a ZMQ client that connects to the Evrmore node's ZMQ interface
2. Registers handlers for different notification types using decorators
3. Tracks statistics about blocks and transactions
4. Detects transactions involving assets
5. Periodically displays statistics
6. Handles graceful shutdown when Ctrl+C is pressed

## Important: RPC Client with ZMQ

When using the RPC client alongside ZMQ notifications, it's **critical** to ensure the RPC client is properly initialized for async use:

```python
# Create and configure RPC client for async use
rpc_client = EvrmoreClient()
rpc_client.force_async()  # Explicitly set async mode

# Use with await
block_data = await rpc_client.getblock(block_hash)
```

### Common Mistakes to Avoid

1. **Not forcing async mode**: ZMQ handlers are async functions, so any RPC calls inside them must use the async API
2. **Forgetting to await RPC calls**: All RPC calls in async context must be awaited
3. **Not closing the RPC client**: Remember to call `await rpc_client.close()` during shutdown

## Customization

You can customize the example by:

1. Changing the ZMQ host and port to match your node's configuration
2. Modifying which notification topics you want to subscribe to
3. Adding additional processing logic in the notification handlers
4. Extending the statistics tracking with additional metrics

## Notification Types

The example subscribes to four types of notifications:

- `HASH_BLOCK`: Lightweight notification of new blocks (just the block hash)
- `HASH_TX`: Lightweight notification of new transactions (just the transaction hash)
- `RAW_BLOCK`: Complete serialized block data
- `RAW_TX`: Complete serialized transaction data

The lightweight notifications are generally recommended for most use cases, as they're more efficient and provide the hash which can be used to fetch additional data via RPC if needed.

## Error Handling

The example includes basic error handling for RPC calls. In a production application, you would want to implement more robust error handling and retry logic.

## Resource Management

The example demonstrates proper resource management:
- Starting the ZMQ client explicitly
- Stopping the ZMQ client during shutdown
- Closing the RPC client during shutdown

This ensures that all resources are properly released when the application exits. 