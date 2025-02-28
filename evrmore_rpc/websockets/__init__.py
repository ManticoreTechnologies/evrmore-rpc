"""
WebSockets support for Evrmore RPC.

This package provides WebSocket client and server implementations for Evrmore blockchain.
It allows for real-time updates on blockchain events like new blocks and transactions.
"""

from evrmore_rpc.websockets.client import EvrmoreWebSocketClient
from evrmore_rpc.websockets.server import EvrmoreWebSocketServer
from evrmore_rpc.websockets.models import (
    WebSocketMessage,
    WebSocketSubscription,
    WebSocketError,
    WebSocketBlockData,
    WebSocketTransactionData,
    WebSocketSequenceData,
)

__all__ = [
    "EvrmoreWebSocketClient",
    "EvrmoreWebSocketServer",
    "WebSocketMessage",
    "WebSocketSubscription",
    "WebSocketError",
    "WebSocketBlockData",
    "WebSocketTransactionData",
    "WebSocketSequenceData",
] 