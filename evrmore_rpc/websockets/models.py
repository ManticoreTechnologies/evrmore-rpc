"""
WebSockets models for Evrmore RPC.

This module provides data models for WebSocket messages and subscriptions.
"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field

class WebSocketSubscription(BaseModel):
    """
    Model for WebSocket subscription requests.
    
    Attributes:
        action: The subscription action ("subscribe" or "unsubscribe")
        topic: The topic to subscribe to or unsubscribe from
    """
    action: str = Field(..., description="The subscription action ('subscribe' or 'unsubscribe')")
    topic: str = Field(..., description="The topic to subscribe to or unsubscribe from")

class WebSocketMessage(BaseModel):
    """
    Model for WebSocket messages.
    
    Attributes:
        type: The message type (e.g., "block", "transaction", "sequence")
        data: The message data
    """
    type: str = Field(..., description="The message type")
    data: Any = Field(..., description="The message data")

class WebSocketError(BaseModel):
    """
    Model for WebSocket error messages.
    
    Attributes:
        code: The error code
        message: The error message
    """
    code: int = Field(..., description="The error code")
    message: str = Field(..., description="The error message")

class WebSocketBlockData(BaseModel):
    """
    Model for block data in WebSocket messages.
    
    Attributes:
        hash: The block hash
        height: The block height
        time: The block timestamp
        tx: The list of transaction IDs in the block
    """
    hash: str = Field(..., description="The block hash")
    height: int = Field(..., description="The block height")
    time: int = Field(..., description="The block timestamp")
    tx: List[str] = Field(default_factory=list, description="The list of transaction IDs in the block")
    size: int = Field(..., description="The block size in bytes")
    weight: int = Field(..., description="The block weight")
    version: int = Field(..., description="The block version")
    merkleroot: str = Field(..., description="The merkle root hash")
    nonce: int = Field(..., description="The block nonce")
    bits: str = Field(..., description="The block bits")
    difficulty: float = Field(..., description="The block difficulty")
    chainwork: str = Field(..., description="The chainwork")
    previousblockhash: Optional[str] = Field(None, description="The previous block hash")
    nextblockhash: Optional[str] = Field(None, description="The next block hash")

class WebSocketTransactionData(BaseModel):
    """
    Model for transaction data in WebSocket messages.
    
    Attributes:
        txid: The transaction ID
        hash: The transaction hash
        size: The transaction size in bytes
        vsize: The virtual transaction size
        version: The transaction version
        locktime: The transaction locktime
        vin: The transaction inputs
        vout: The transaction outputs
    """
    txid: str = Field(..., description="The transaction ID")
    hash: str = Field(..., description="The transaction hash")
    size: int = Field(..., description="The transaction size in bytes")
    vsize: int = Field(..., description="The virtual transaction size")
    version: int = Field(..., description="The transaction version")
    locktime: int = Field(..., description="The transaction locktime")
    vin: List[Dict[str, Any]] = Field(default_factory=list, description="The transaction inputs")
    vout: List[Dict[str, Any]] = Field(default_factory=list, description="The transaction outputs")
    hex: Optional[str] = Field(None, description="The raw transaction data in hexadecimal")
    blockhash: Optional[str] = Field(None, description="The block hash containing this transaction")
    confirmations: Optional[int] = Field(None, description="The number of confirmations")
    time: Optional[int] = Field(None, description="The transaction time")
    blocktime: Optional[int] = Field(None, description="The block time")

class WebSocketSequenceData(BaseModel):
    """
    Model for sequence data in WebSocket messages.
    
    Attributes:
        sequence: The sequence number
        hash: The hash associated with the sequence
    """
    sequence: int = Field(..., description="The sequence number")
    hash: str = Field(..., description="The hash associated with the sequence") 