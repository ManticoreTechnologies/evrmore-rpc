"""
WebSockets server for Evrmore RPC.

This module provides a WebSocket server for broadcasting Evrmore blockchain events.
It integrates with the ZMQ client to receive real-time updates and broadcasts them to connected clients.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional, Set, cast

# Update imports to use the latest websockets API
import websockets
from websockets.exceptions import ConnectionClosed
from websockets.server import WebSocketServer

from evrmore_rpc import EvrmoreAsyncRPCClient
from evrmore_rpc.zmq.client import EvrmoreZMQClient, ZMQNotification, ZMQTopic
from evrmore_rpc.websockets.models import WebSocketMessage, WebSocketSubscription

logger = logging.getLogger(__name__)

class EvrmoreWebSocketServer:
    """
    A WebSocket server for broadcasting Evrmore blockchain events.
    
    This server integrates with the ZMQ client to receive real-time updates from the Evrmore node
    and broadcasts them to connected WebSocket clients. It supports subscribing to different types
    of events like new blocks and transactions.
    
    Example:
        ```python
        import asyncio
        from evrmore_rpc import EvrmoreAsyncRPCClient
        from evrmore_rpc.zmq.client import EvrmoreZMQClient
        from evrmore_rpc.websockets.server import EvrmoreWebSocketServer
        
        async def main():
            # Initialize RPC client
            rpc = EvrmoreAsyncRPCClient()
            
            # Initialize ZMQ client
            zmq = EvrmoreZMQClient()
            
            # Initialize WebSocket server
            server = EvrmoreWebSocketServer(
                rpc_client=rpc,
                zmq_client=zmq,
                host="localhost",
                port=8820
            )
            
            # Start the server
            await server.start()
            
        asyncio.run(main())
        ```
    """
    
    def __init__(
        self,
        rpc_client: EvrmoreAsyncRPCClient,
        zmq_client: EvrmoreZMQClient,
        host: str = "localhost",
        port: int = 8820,
        ping_interval: float = 30.0,
        ping_timeout: float = 10.0,
        close_timeout: float = 10.0,
        max_size: int = 2**20,  # 1MB
        **kwargs: Any,
    ) -> None:
        """
        Initialize the WebSocket server.
        
        Args:
            rpc_client: The Evrmore RPC client
            zmq_client: The Evrmore ZMQ client
            host: The host to bind to
            port: The port to bind to
            ping_interval: Interval between pings in seconds
            ping_timeout: Timeout for ping responses in seconds
            close_timeout: Timeout for close handshake in seconds
            max_size: Maximum size of messages in bytes
            **kwargs: Additional arguments to pass to websockets.serve
        """
        self.rpc_client = rpc_client
        self.zmq_client = zmq_client
        self.host = host
        self.port = port
        self.ping_interval = ping_interval
        self.ping_timeout = ping_timeout
        self.close_timeout = close_timeout
        self.max_size = max_size
        self.kwargs = kwargs
        self.clients: Dict[websockets.WebSocketServerProtocol, Set[str]] = {}
        self.server: Optional[WebSocketServer] = None
        self.running = False
        
    async def start(self) -> None:
        """
        Start the WebSocket server.
        
        This method starts the WebSocket server and sets up the ZMQ client to receive
        real-time updates from the Evrmore node.
        
        Raises:
            RuntimeError: If the server is already running
        """
        if self.running:
            raise RuntimeError("Server is already running")
            
        # Initialize RPC client
        await self.rpc_client.initialize()
        
        # Set up ZMQ handlers
        self.zmq_client.on_block(self._handle_block)
        self.zmq_client.on_transaction(self._handle_transaction)
        self.zmq_client.on_sequence(self._handle_sequence)
        
        # Start ZMQ client
        zmq_task = asyncio.create_task(self.zmq_client.start())
        
        # Start WebSocket server
        async def handler(websocket):
            await self._handle_client(websocket)
            
        self.server = await websockets.serve(
            handler,
            self.host,
            self.port,
            ping_interval=self.ping_interval,
            ping_timeout=self.ping_timeout,
            close_timeout=self.close_timeout,
            max_size=self.max_size,
            **self.kwargs,
        )
        
        self.running = True
        logger.info(f"WebSocket server started on {self.host}:{self.port}")
        
        # Keep the server running
        await self.server.wait_closed()
        
    async def stop(self) -> None:
        """Stop the WebSocket server."""
        if not self.running:
            return
            
        # Close all client connections
        close_tasks = [client.close() for client in self.clients]
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        # Stop the server
        if self.server:
            self.server.close()
            await self.server.wait_closed()
            
        # Stop the ZMQ client
        await self.zmq_client.stop()
        
        self.running = False
        logger.info("WebSocket server stopped")
        
    async def _handle_client(self, websocket: websockets.WebSocketServerProtocol) -> None:
        """
        Handle a new WebSocket client connection.
        
        Args:
            websocket: The WebSocket connection
        """
        # Register the client
        self.clients[websocket] = set()
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"New client connected: {client_info}")
        
        try:
            async for message in websocket:
                try:
                    # Parse the message
                    if isinstance(message, str):
                        data = json.loads(message)
                    else:
                        data = json.loads(message.decode("utf-8"))
                        
                    # Handle subscription requests
                    if "action" in data and "topic" in data:
                        subscription = WebSocketSubscription.model_validate(data)
                        await self._handle_subscription(websocket, subscription)
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from client {client_info}: {message}")
                except Exception as e:
                    logger.error(f"Error handling message from client {client_info}: {e}")
                    
        except ConnectionClosed:
            logger.info(f"Client disconnected: {client_info}")
        except Exception as e:
            logger.error(f"Error with client {client_info}: {e}")
        finally:
            # Unregister the client
            if websocket in self.clients:
                del self.clients[websocket]
                
    async def _handle_subscription(self, websocket: websockets.WebSocketServerProtocol, subscription: WebSocketSubscription) -> None:
        """
        Handle a subscription request from a client.
        
        Args:
            websocket: The WebSocket connection
            subscription: The subscription request
        """
        if subscription.action == "subscribe":
            self.clients[websocket].add(subscription.topic)
            logger.info(f"Client {websocket.remote_address[0]}:{websocket.remote_address[1]} subscribed to {subscription.topic}")
        elif subscription.action == "unsubscribe":
            if subscription.topic in self.clients[websocket]:
                self.clients[websocket].remove(subscription.topic)
                logger.info(f"Client {websocket.remote_address[0]}:{websocket.remote_address[1]} unsubscribed from {subscription.topic}")
                
    async def _broadcast(self, message: WebSocketMessage) -> None:
        """
        Broadcast a message to all subscribed clients.
        
        Args:
            message: The message to broadcast
        """
        if not self.clients:
            return
            
        # Convert message to JSON
        json_message = message.model_dump_json()
        
        # Send to all subscribed clients
        for websocket, topics in list(self.clients.items()):
            if message.type in topics or "all" in topics:
                try:
                    await websocket.send(json_message)
                except Exception as e:
                    logger.error(f"Error sending message to client: {e}")
                    # Remove client if we can't send messages to it
                    if websocket in self.clients:
                        del self.clients[websocket]
                    
    async def _handle_block(self, notification: ZMQNotification) -> None:
        """
        Handle a block notification from ZMQ.
        
        Args:
            notification: The ZMQ notification
        """
        try:
            # Get block details from RPC
            if notification.topic == ZMQTopic.HASH_BLOCK:
                block_hash = notification.hex
                block = await self.rpc_client.getblock(block_hash)
                
                # Create and broadcast message
                message = WebSocketMessage(
                    type="block",
                    data=block,
                )
                await self._broadcast(message)
                
        except Exception as e:
            logger.error(f"Error handling block notification: {e}")
            
    async def _handle_transaction(self, notification: ZMQNotification) -> None:
        """
        Handle a transaction notification from ZMQ.
        
        Args:
            notification: The ZMQ notification
        """
        try:
            # Get transaction details from RPC
            if notification.topic == ZMQTopic.HASH_TX:
                txid = notification.hex
                tx = await self.rpc_client.getrawtransaction(txid, True)
                
                # Create and broadcast message
                message = WebSocketMessage(
                    type="transaction",
                    data=tx,
                )
                await self._broadcast(message)
                
        except Exception as e:
            logger.error(f"Error handling transaction notification: {e}")
            
    async def _handle_sequence(self, notification: ZMQNotification) -> None:
        """
        Handle a sequence notification from ZMQ.
        
        Args:
            notification: The ZMQ notification
        """
        try:
            # Create and broadcast message
            message = WebSocketMessage(
                type="sequence",
                data={
                    "sequence": notification.sequence,
                    "hash": notification.hex,
                },
            )
            await self._broadcast(message)
            
        except Exception as e:
            logger.error(f"Error handling sequence notification: {e}")
            
    async def __aenter__(self) -> "EvrmoreWebSocketServer":
        """Enter the async context manager."""
        await self.start()
        return self
        
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit the async context manager."""
        await self.stop() 