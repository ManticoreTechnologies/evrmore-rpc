"""
evrmore-rpc: A comprehensive, typed Python wrapper for Evrmore blockchain with ZMQ and WebSockets support
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

__version__ = "1.2.0"
__author__ = "Manticore Technologies"
__email__ = "dev@manticore.tech"

from evrmore_rpc.client import EvrmoreRPCClient, EvrmoreRPCError
from evrmore_rpc.async_client import EvrmoreAsyncRPCClient
from evrmore_rpc.models.base import (
    Amount,
    Address,
    Asset,
    Transaction,
    Block,
    RPCResponse
)
from evrmore_rpc.utils import (
    format_amount,
    validate_response,
    validate_list_response,
    validate_dict_response,
    format_command_args
)
from evrmore_rpc.zmq.client import EvrmoreZMQClient

# Import WebSockets support if available
try:
    from evrmore_rpc.websockets.client import EvrmoreWebSocketClient
    from evrmore_rpc.websockets.server import EvrmoreWebSocketServer
    from evrmore_rpc.websockets.models import WebSocketMessage
    __has_websockets__ = True
except ImportError:
    __has_websockets__ = False

__all__ = [
    # Core clients
    "EvrmoreRPCClient",
    "EvrmoreRPCError",
    "EvrmoreAsyncRPCClient",
    
    # Models
    "Amount",
    "Address",
    "Asset",
    "Transaction",
    "Block",
    "RPCResponse",
    
    # Utilities
    "format_amount",
    "validate_response",
    "validate_list_response",
    "validate_dict_response",
    "format_command_args",
    
    # ZMQ support
    "EvrmoreZMQClient",
    
    # Version info
    "__version__",
    "__author__",
    "__email__",
    "__has_websockets__",
]

# Add WebSockets exports if available
if __has_websockets__:
    __all__.extend([
        "EvrmoreWebSocketClient",
        "EvrmoreWebSocketServer",
        "WebSocketMessage",
    ]) 