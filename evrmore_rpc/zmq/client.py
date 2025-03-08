"""
ZMQ client for receiving Evrmore blockchain notifications in real-time.

This module provides a high-level, asynchronous interface to the Evrmore ZMQ notifications.
The Evrmore node can publish notifications about various blockchain events through ZMQ,
and this client allows subscribing to those events and handling them in real-time.

Features:
- Asynchronous API with asyncio integration
- Event-based handling with decorator-based registration
- Support for all standard Evrmore ZMQ notification topics
- Automatic reconnection on connection loss
- Clean shutdown and resource management
- Typed notification data with structured fields

Available notification topics:
- HASH_BLOCK: New block hash (lightweight notification of new blocks)
- HASH_TX: New transaction hash (lightweight notification of new transactions)
- RAW_BLOCK: Complete serialized block data
- RAW_TX: Complete serialized transaction data

Usage requires ZMQ to be enabled in the Evrmore node configuration (evrmore.conf):
    zmqpubhashtx=tcp://127.0.0.1:28332
    zmqpubhashblock=tcp://127.0.0.1:28332
    zmqpubrawtx=tcp://127.0.0.1:28332
    zmqpubrawblock=tcp://127.0.0.1:28332

Using with RPC client:
When using the ZMQ client alongside the EvrmoreClient for RPC calls, follow these best practices:

1. Always force async mode for the RPC client:
   ```
   from evrmore_rpc import EvrmoreClient
   rpc_client = EvrmoreClient()
   rpc_client.force_async()  # This is critical for correct operation
   ```

2. Always await all RPC calls inside ZMQ handlers:
   ```
   @zmq_client.on(ZMQTopic.HASH_BLOCK)
   async def handle_block(notification):
       block_data = await rpc_client.getblock(notification.hex)  # Note the await
   ```

3. Always properly close both clients when shutting down:
   ```
   await zmq_client.stop()
   await rpc_client.close()
   ```

4. Handle exceptions in your notification handlers to prevent crashes:
   ```
   @zmq_client.on(ZMQTopic.HASH_BLOCK)
   async def handle_block(notification):
       try:
           block_data = await rpc_client.getblock(notification.hex)
       except Exception as e:
           print(f"Error handling block: {e}")
   ```

Dependencies:
- pyzmq: Python bindings for ZeroMQ
"""

import asyncio
import binascii
import enum
import logging
import socket
from typing import Any, Callable, Dict, List, Optional, Set, Union

try:
    import zmq
    import zmq.asyncio
    HAS_ZMQ = True
except ImportError:
    HAS_ZMQ = False

from evrmore_rpc.zmq.models import ZMQNotification

# Set up logging
logger = logging.getLogger("evrmore_rpc.zmq")


class ZMQTopic(enum.Enum):
    """
    ZMQ notification topics published by Evrmore nodes.
    
    See https://github.com/EVR-git/EVR/blob/master/doc/zmq.md for more information.
    """
    HASH_BLOCK = b"hashblock"
    HASH_TX = b"hashtx"
    RAW_BLOCK = b"rawblock"
    RAW_TX = b"rawtx"


class EvrmoreZMQClient:
    """
    Client for receiving ZMQ notifications from an Evrmore node.
    
    This class provides a simple interface for subscribing to ZMQ notifications
    from an Evrmore node and handling them with callback functions.
    
    Attributes:
        zmq_host: The host of the Evrmore node's ZMQ interface.
        zmq_port: The port of the Evrmore node's ZMQ interface.
        topics: The ZMQ topics to subscribe to.
        context: The ZMQ context.
        socket: The ZMQ socket.
    """
    
    def __init__(self, zmq_host: str = "127.0.0.1", zmq_port: int = 28332, topics: Optional[List[ZMQTopic]] = None) -> None:
        """
        Initialize the ZMQ client.
        
        Args:
            zmq_host: The host of the Evrmore node's ZMQ interface.
            zmq_port: The port of the Evrmore node's ZMQ interface.
            topics: The ZMQ topics to subscribe to.
        """
        if not HAS_ZMQ:
            logger.warning("ZMQ is not installed. ZMQ functionality will not be available.")
            
        self.zmq_host = zmq_host
        self.zmq_port = zmq_port
        self.topics = topics or list(ZMQTopic)
        self.context = None
        self.socket = None
        self.handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._task = None
    
    def on(self, topic: ZMQTopic) -> Callable:
        """
        Decorator for registering a handler for a ZMQ topic.
        
        Args:
            topic: The ZMQ topic to handle.
            
        Returns:
            A decorator function that takes a handler function and registers it.
        """
        def decorator(handler: Callable) -> Callable:
            if topic.value not in self.handlers:
                self.handlers[topic.value] = []
            self.handlers[topic.value].append(handler)
            return handler
        return decorator
    
    async def start(self) -> None:
        """
        Start the ZMQ client.
        
        This method creates a ZMQ socket, subscribes to the specified topics,
        and starts a background task to receive notifications.
        """
        if not HAS_ZMQ:
            logger.warning("ZMQ is not installed. ZMQ functionality will not be available.")
            return
            
        if self._running:
            return
            
        # Create ZMQ context and socket
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        
        # Set socket options
        # Note: We set a timeout to avoid blocking indefinitely
        self.socket.set(zmq.RCVTIMEO, 5000)  # 5 seconds
        
        # Connect to Evrmore node
        try:
            self.socket.connect(f"tcp://{self.zmq_host}:{self.zmq_port}")
            logger.info(f"Connected to ZMQ server at {self.zmq_host}:{self.zmq_port}")
        except zmq.error.ZMQError as e:
            logger.error(f"Failed to connect to ZMQ server: {e}")
            return
            
        # Subscribe to topics
        for topic in self.topics:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.value)
            logger.info(f"Subscribed to topic: {topic.name}")
            
        # Start background task
        self._running = True
        self._task = asyncio.create_task(self._receive_loop())
        
    async def stop(self) -> None:
        """
        Stop the ZMQ client.
        
        This method cancels the background task and closes the ZMQ socket.
        """
        if not self._running:
            return
            
        # Cancel background task
        self._running = False
        if self._task:
            try:
                self._task.cancel()
                await asyncio.gather(self._task, return_exceptions=True)
            except asyncio.CancelledError:
                pass
            
        # Close socket and context
        if self.socket:
            self.socket.close()
            self.socket = None
            
        if self.context:
            self.context.term()
            self.context = None
            
    async def _receive_loop(self) -> None:
        """
        Background task for receiving ZMQ notifications.
        
        This method continuously receives notifications from the ZMQ socket
        and dispatches them to the appropriate handlers.
        """
        while self._running:
            try:
                # Receive message
                msg = await self.socket.recv_multipart()
                
                # Parse message
                topic, body, sequence = msg
                sequence = int.from_bytes(sequence, byteorder="little")
                hex_data = binascii.hexlify(body).decode("utf-8")
                
                # Create notification
                notification = ZMQNotification(
                    topic=topic.decode("utf-8"),
                    body=body,
                    sequence=sequence,
                    hex=hex_data,
                )
                
                # Dispatch to handlers
                if topic in self.handlers:
                    for handler in self.handlers[topic]:
                        try:
                            await handler(notification)
                        except Exception as e:
                            logger.error(f"Error in handler: {e}")
                            
            except zmq.error.Again:
                # Timeout, just continue
                pass
            except asyncio.CancelledError:
                # Task was cancelled
                break
            except Exception as e:
                logger.error(f"Error receiving ZMQ message: {e}")
                # Short delay before retrying
                await asyncio.sleep(1)
                
        logger.info("ZMQ receive loop stopped") 