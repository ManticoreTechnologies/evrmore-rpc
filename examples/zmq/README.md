# ZMQ Examples

This directory contains examples demonstrating the ZMQ functionality of the `evrmore-rpc` package for real-time blockchain notifications.

## Examples

- `zmq_monitor.py`: A comprehensive example showing how to monitor blockchain events using ZMQ.
- `zmq_quick_test.py`: A simple example for quickly testing ZMQ functionality.

## Running the Examples

To run an example, use the following command:

```bash
python examples/zmq/zmq_monitor.py
```

## ZMQ Configuration

Make sure your Evrmore node is configured to publish ZMQ notifications by adding the following to your `evrmore.conf` file:

```
# ZMQ notifications
zmqpubhashblock=tcp://127.0.0.1:28332
zmqpubhashtx=tcp://127.0.0.1:28332
zmqpubsequence=tcp://127.0.0.1:28332
``` 