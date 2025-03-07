"""
Models for the ZMQ client.
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class ZMQNotification:
    """
    A notification from the Evrmore ZMQ interface.
    
    Attributes:
        topic: The ZMQ topic.
        body: The body of the notification.
        sequence: The sequence number of the notification.
        hex: The hexadecimal representation of the body.
        timestamp: The timestamp of the notification.
    """
    topic: str
    body: bytes
    sequence: int
    hex: str
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now() 