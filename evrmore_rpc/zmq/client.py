import zmq
import zmq.asyncio
import asyncio
import struct
import binascii
from typing import Dict, List, Optional, Callable, Any, Union, Coroutine
from dataclasses import dataclass
from enum import Enum

class ZMQTopic(Enum):
    """Evrmore ZMQ notification topics."""
    HASH_TX = b"hashtx"
    RAW_TX = b"rawtx"
    HASH_BLOCK = b"hashblock"
    RAW_BLOCK = b"rawblock"
    SEQUENCE = b"sequence"

@dataclass
class ZMQNotification:
    """Represents a ZMQ notification from Evrmore."""
    topic: ZMQTopic
    body: bytes
    sequence: Optional[int] = None

    @property
    def hex(self) -> str:
        """Get the notification body as hex string."""
        return binascii.hexlify(self.body).decode('utf-8')

class EvrmoreZMQClient:
    """
    Client for receiving Evrmore ZMQ notifications.
    
    This client can subscribe to various Evrmore notifications including:
    - New transactions (hash or raw)
    - New blocks (hash or raw)
    - Sequence updates
    
    Example:
        ```python
        client = EvrmoreZMQClient("tcp://127.0.0.1:28332")
        
        @client.on_transaction
        async def handle_tx(notification):
            print(f"New transaction: {notification.hex}")
            
        @client.on_block
        async def handle_block(notification):
            print(f"New block: {notification.hex}")
            
        await client.start()
        ```
    """
    
    def __init__(
        self,
        address: str = "tcp://127.0.0.1:28332",
        context: Optional[zmq.asyncio.Context] = None,
        topics: Optional[List[ZMQTopic]] = None
    ):
        """
        Initialize the ZMQ client.
        
        Args:
            address: ZMQ endpoint address
            context: Optional ZMQ context
            topics: List of topics to subscribe to (defaults to all)
        """
        self.address = address
        self.context = context or zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.topics = topics or list(ZMQTopic)
        self.callbacks: Dict[ZMQTopic, List[Callable[[ZMQNotification], Coroutine]]] = {
            topic: [] for topic in ZMQTopic
        }
        self._running = False
        self._task: Optional[asyncio.Task] = None
        
    def on_transaction(self, func: Callable[[ZMQNotification], Coroutine]) -> Callable:
        """Decorator to register a transaction notification handler."""
        self.callbacks[ZMQTopic.HASH_TX].append(func)
        self.callbacks[ZMQTopic.RAW_TX].append(func)
        return func
        
    def on_block(self, func: Callable[[ZMQNotification], Coroutine]) -> Callable:
        """Decorator to register a block notification handler."""
        self.callbacks[ZMQTopic.HASH_BLOCK].append(func)
        self.callbacks[ZMQTopic.RAW_BLOCK].append(func)
        return func
        
    def on_sequence(self, func: Callable[[ZMQNotification], Coroutine]) -> Callable:
        """Decorator to register a sequence notification handler."""
        self.callbacks[ZMQTopic.SEQUENCE].append(func)
        return func
        
    def on(self, topic: Union[ZMQTopic, str]) -> Callable:
        """Decorator to register a handler for a specific topic."""
        if isinstance(topic, str):
            topic = ZMQTopic(topic.encode())
            
        def decorator(func: Callable[[ZMQNotification], Coroutine]) -> Callable:
            self.callbacks[topic].append(func)
            return func
            
        return decorator
        
    async def _handle_notification(self, topic: bytes, body: bytes, sequence: Optional[bytes] = None) -> None:
        """Handle an incoming ZMQ notification."""
        try:
            topic_enum = ZMQTopic(topic)
            notification = ZMQNotification(
                topic=topic_enum,
                body=body,
                sequence=int.from_bytes(sequence, 'little') if sequence else None
            )
            
            for callback in self.callbacks[topic_enum]:
                try:
                    await callback(notification)
                except Exception as e:
                    print(f"Error in callback {callback.__name__}: {e}")
                    
        except ValueError:
            print(f"Unknown topic: {topic}")
            
    async def _receive_loop(self) -> None:
        """Main receive loop for ZMQ notifications."""
        while self._running:
            try:
                multipart = await self.socket.recv_multipart()
                
                if len(multipart) == 3:
                    topic, body, sequence = multipart
                    await self._handle_notification(topic, body, sequence)
                elif len(multipart) == 2:
                    topic, body = multipart
                    await self._handle_notification(topic, body)
                    
            except Exception as e:
                print(f"Error receiving ZMQ message: {e}")
                if not self._running:
                    break
                await asyncio.sleep(1)
                
    async def start(self) -> None:
        """Start receiving ZMQ notifications."""
        self.socket.connect(self.address)
        
        for topic in self.topics:
            self.socket.setsockopt(zmq.SUBSCRIBE, topic.value)
            
        self._running = True
        self._task = asyncio.create_task(self._receive_loop())
        await self._task
        
    async def stop(self) -> None:
        """Stop receiving ZMQ notifications."""
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.socket.close()
        self.context.term()
        
    async def __aenter__(self) -> 'EvrmoreZMQClient':
        await self.start()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.stop() 