"""
ZMQ client for receiving Evrmore blockchain notifications.
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