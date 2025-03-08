"""
Models for ZMQ notifications from the Evrmore blockchain.

This module provides data structures for the ZMQ notifications sent by Evrmore nodes.
These models ensure properly typed and structured data when working with ZMQ notifications.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class ZMQNotification:
    """
    Represents a ZMQ notification from an Evrmore node.
    
    ZMQ notifications contain the following information:
    - topic: The type of notification (e.g., 'hashblock', 'hashtx')
    - body: The binary data of the notification (e.g., block or transaction hash)
    - sequence: A sequence number for the notification
    - hex: The hexadecimal representation of the binary data
    
    The exact format of the body depends on the notification type:
    - HASH_BLOCK: 32-byte block hash
    - HASH_TX: 32-byte transaction hash
    - RAW_BLOCK: Full serialized block
    - RAW_TX: Full serialized transaction
    
    Attributes:
        topic (str): The notification topic (e.g., 'hashblock', 'hashtx')
        body (bytes): The binary data of the notification
        sequence (int): A sequence number for the notification
        hex (str): Hexadecimal representation of the binary data
    """
    topic: str
    body: bytes
    sequence: int
    hex: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def __repr__(self) -> str:
        """String representation of the notification."""
        return f"ZMQNotification(topic='{self.topic}', hex='{self.hex[:16]}{'...' if len(self.hex) > 16 else ''}', sequence={self.sequence})" 