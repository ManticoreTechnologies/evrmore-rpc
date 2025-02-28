"""
WebSockets client for Evrmore RPC.

This module provides a WebSocket client for connecting to an Evrmore WebSocket server.
It allows for real-time updates on blockchain events like new blocks and transactions.
"""

import asyncio
import json
import logging
from typing import Any, AsyncIterator, Dict, List, Optional, Set, Union, cast

# Update imports to use the latest websockets API
import websockets
from websockets.exceptions import ConnectionClosed, WebSocketException

from evrmore_rpc.websockets.models import WebSocketMessage, WebSocketSubscription

logger = logging.getLogger(__name__)

class EvrmoreWebSocketClient:
    """
    A WebSocket client for connecting to an Evrmore WebSocket server.
    
    This client allows for real-time updates on blockchain events like new blocks and transactions.
    It provides a simple interface for subscribing to different types of events and handling them.
    
    Example:
        ```python
        import asyncio
        from evrmore_rpc.websockets import EvrmoreWebSocketClient
        
        async def main():
            async with EvrmoreWebSocketClient("ws://localhost:8820") as client:
                # Subscribe to new blocks
                await client.subscribe("blocks")
                
                # Handle incoming messages
                async for message in client:
                    if message.type == "block":
                        print(f"New block: {message.data.hash}")
                    elif message.type == "transaction":
                        print(f"New transaction: {message.data.txid}")
        
        asyncio.run(main())
        ```
    """
    
    def __init__(
        self,
        uri: str = "ws://localhost:8820",
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
        close_timeout: float = 10.0,
        max_size: int = 2**20,  # 1MB
        max_queue: int = 32,
        **kwargs: Any,
    ) -> None:
        """
        Initialize the WebSocket client.
        
        Args:
            uri: The WebSocket server URI
            ping_interval: Interval between pings in seconds
            ping_timeout: Timeout for ping responses in seconds
            close_timeout: Timeout for close handshake in seconds
            max_size: Maximum size of messages in bytes
            max_queue: Maximum number of messages to queue
            **kwargs: Additional arguments to pass to websockets.connect
        """
        self.uri = uri
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_size = max_size
        self.max_queue = max_queue
        self.kwargs = kwargs
        self.ws = None
        self.subscriptions: Set[str] = set()
        self.connected = False
        self.queue: asyncio.Queue[WebSocketMessage] = asyncio.Queue(maxsize=max_queue)
        self._listener_task: Optional[asyncio.Task] = None
    
    async def _connect_websocket(self):
        """
        Internal method to connect to the WebSocket server.
        This method is separated to make testing easier.
        """
        return await websockets.connect(
            self.uri,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            close_timeout=self.close_timeout,
            max_size=self.max_size,
            **self.kwargs,
        )
        
    async def connect(self) -> None:
        """
        Connect to the WebSocket server.
        
        Raises:
            ConnectionError: If the connection fails
        """
        if self.connected:
            return
            
        try:
            self.ws = await self._connect_websocket()
            self.connected = True
            self._listener_task = asyncio.create_task(self._listen())
            logger.info(f"Connected to WebSocket server at {self.uri}")
            
            # Resubscribe to previous subscriptions
            for subscription in self.subscriptions:
                await self._send_subscription(subscription, True)
                
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket server: {e}")
            raise ConnectionError(f"Failed to connect to WebSocket server: {e}")
            
    async def disconnect(self) -> None:
        """Disconnect from the WebSocket server."""
        if not self.connected or not self.ws:
            return
            
        try:
            # Cancel listener task
            if self._listener_task:
                self._listener_task.cancel()
                try:
                    await self._listener_task
                except asyncio.CancelledError:
                    pass
                self._listener_task = None
                
            # Close WebSocket connection
            await self.ws.close()
            self.connected = False
            self.ws = None
            logger.info("Disconnected from WebSocket server")
            
        except Exception as e:
            logger.error(f"Error disconnecting from WebSocket server: {e}")
            # Force disconnection state even if there was an error
            self.connected = False
            self.ws = None
            
    async def subscribe(self, topic: str) -> None:
        """
        Subscribe to a topic.
        
        Args:
            topic: The topic to subscribe to (e.g., "blocks", "transactions")
            
        Raises:
            ConnectionError: If not connected to the server
        """
        if not self.connected:
            await self.connect()
            
        await self._send_subscription(topic, True)
        self.subscriptions.add(topic)
        logger.info(f"Subscribed to topic: {topic}")
        
    async def unsubscribe(self, topic: str) -> None:
        """
        Unsubscribe from a topic.
        
        Args:
            topic: The topic to unsubscribe from
            
        Raises:
            ConnectionError: If not connected to the server
        """
        if not self.connected or topic not in self.subscriptions:
            return
            
        await self._send_subscription(topic, False)
        self.subscriptions.remove(topic)
        logger.info(f"Unsubscribed from topic: {topic}")
        
    async def _send_subscription(self, topic: str, subscribe: bool) -> None:
        """
        Send a subscription message to the server.
        
        Args:
            topic: The topic to subscribe to or unsubscribe from
            subscribe: True to subscribe, False to unsubscribe
            
        Raises:
            ConnectionError: If not connected to the server
        """
        if not self.connected or not self.ws:
            raise ConnectionError("Not connected to WebSocket server")
            
        subscription = WebSocketSubscription(
            action="subscribe" if subscribe else "unsubscribe",
            topic=topic,
        )
        
        try:
            await self.ws.send(subscription.model_dump_json())
        except Exception as e:
            logger.error(f"Failed to send subscription: {e}")
            raise ConnectionError(f"Failed to send subscription: {e}")
            
    async def _listen(self) -> None:
        """
        Listen for messages from the WebSocket server.
        
        This method runs in a background task and puts received messages into the queue.
        """
        if not self.ws:
            return
            
        try:
            async for message in self.ws:
                try:
                    # Parse the message
                    if isinstance(message, str):
                        data = json.loads(message)
                    else:
                        data = json.loads(message.decode("utf-8"))
                        
                    # Create a WebSocketMessage object
                    ws_message = WebSocketMessage.model_validate(data)
                    
                    # Put the message in the queue
                    await self.queue.put(ws_message)
                    
                except Exception as e:
                    logger.error(f"Failed to process message: {e}")
                    
        except asyncio.CancelledError:
            # Task was cancelled, exit gracefully
            return
            
        except ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.connected = False
            
        except Exception as e:
            logger.error(f"WebSocket listener error: {e}")
            
            # Try to reconnect
            self.connected = False
            try:
                await self.connect()
            except Exception as reconnect_error:
                logger.error(f"Failed to reconnect: {reconnect_error}")
            
    async def __aiter__(self) -> AsyncIterator[WebSocketMessage]:
        """
        Iterate over messages from the WebSocket server.
        
        Yields:
            WebSocketMessage: The next message from the server
            
        Raises:
            ConnectionError: If not connected to the server
        """
        if not self.connected:
            await self.connect()
            
        while self.connected:
            try:
                message = await self.queue.get()
                yield message
                self.queue.task_done()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error getting message from queue: {e}")
                # Small delay to prevent tight loop in case of persistent errors
                await asyncio.sleep(0.1)
                
    async def __aenter__(self) -> "EvrmoreWebSocketClient":
        """Enter the async context manager."""
        await self.connect()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        await self.disconnect() 