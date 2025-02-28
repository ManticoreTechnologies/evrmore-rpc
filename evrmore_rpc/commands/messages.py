from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class MessageChannel(BaseModel):
    """Model for message channel information"""
    name: str = Field(..., description="The name of the channel")
    time: int = Field(..., description="The timestamp of the last message")
    message_count: int = Field(..., description="The number of messages in the channel")

class Message(BaseModel):
    """Model for message information"""
    channel: str = Field(..., description="The channel name")
    ipfs_hash: str = Field(..., description="The IPFS hash of the message")
    timestamp: int = Field(..., description="The timestamp of the message")
    expire_time: Optional[int] = Field(None, description="The expiration timestamp of the message")
    txid: str = Field(..., description="The transaction ID of the message")

def wrap_message_commands(client):
    """Add typed message commands to the client."""
    
    def clearmessages() -> None:
        """Clear all locally stored messages."""
        return client.execute_command("clearmessages")
    
    def sendmessage(channel_name: str, ipfs_hash: str, expire_time: Optional[int] = None) -> str:
        """Send a message to a channel."""
        if expire_time is not None:
            return client.execute_command("sendmessage", channel_name, ipfs_hash, expire_time)
        return client.execute_command("sendmessage", channel_name, ipfs_hash)
    
    def subscribetochannel(channel_name: str) -> bool:
        """Subscribe to a message channel."""
        return client.execute_command("subscribetochannel", channel_name)
    
    def unsubscribefromchannel(channel_name: str) -> bool:
        """Unsubscribe from a message channel."""
        return client.execute_command("unsubscribefromchannel", channel_name)
    
    def viewallmessagechannels() -> List[MessageChannel]:
        """View all message channels."""
        result = client.execute_command("viewallmessagechannels")
        return [MessageChannel.model_validate(channel) for channel in result]
    
    def viewallmessages() -> List[Message]:
        """View all messages."""
        result = client.execute_command("viewallmessages")
        return [Message.model_validate(message) for message in result]
    
    # Add methods to client
    client.clearmessages = clearmessages
    client.sendmessage = sendmessage
    client.subscribetochannel = subscribetochannel
    client.unsubscribefromchannel = unsubscribefromchannel
    client.viewallmessagechannels = viewallmessagechannels
    client.viewallmessages = viewallmessages
    
    return client 