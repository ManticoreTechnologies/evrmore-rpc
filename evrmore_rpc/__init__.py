"""
evrmore-rpc: A comprehensive Python wrapper for Evrmore blockchain RPC

Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details

Features:
- Polymorphic client that works identically in both synchronous and asynchronous contexts
- Automatic detection of execution context (sync/async) with seamless adaptation
- Comprehensive type hints and Pydantic models for strong type safety
- High-performance connection handling with both HTTP and ZMQ interfaces
- Complete coverage of all Evrmore RPC commands with proper parameter typing
- Structured response models with automatic validation
- Flexible configuration via constructor parameters, environment variables, or evrmore.conf
- ZMQ support for real-time blockchain notifications
- Built-in stress testing and performance analysis capabilities

For documentation and examples, visit:
https://github.com/manticore-tech/evrmore-rpc

For issues and contributions:
https://github.com/manticore-tech/evrmore-rpc/issues
"""

__version__ = "3.2.2"

from evrmore_rpc.client import (
    EvrmoreClient,
    EvrmoreConfig,
    EvrmoreRPCError
)

# Import common models
from evrmore_rpc.models import (
    # Base models
    Amount, Address, Asset, Transaction, BaseBlock, RPCResponse,
    
    # Blockchain models
    BlockchainInfo, Block, BlockHeader, ChainTip, MempoolInfo, 
    TxOut, TxOutSetInfo,
    
    # Asset models
    AssetInfo, AssetData, CacheInfo, ListAssetResult,
    
    # Network models
    NetworkInfo, PeerInfo, LocalAddress, Network,
    
    # Mining models
    MiningInfo, MiningStats,
    
    # Address index models
    AddressBalance, AddressDelta, AddressUtxo, AddressMempool,
    
    # Raw transaction models
    DecodedTransaction, DecodedScript, TransactionInput, TransactionOutput,
    
    # Wallet models
    WalletInfo, WalletTransaction, UnspentOutput
)

# Import stress_test function directly for easy access
from evrmore_rpc.stress_test import run_stress_test as stress_test

# Default Evrmore data directory
from pathlib import Path
DEFAULT_DATADIR = Path.home() / ".evrmore"

__all__ = [
    # Client classes
    "EvrmoreClient",
    "EvrmoreConfig",
    "EvrmoreRPCError",
    
    # Base models
    "Amount", "Address", "Asset", "Transaction", "BaseBlock", "RPCResponse",
    
    # Blockchain models
    "BlockchainInfo", "Block", "BlockHeader", "ChainTip", "MempoolInfo", 
    "TxOut", "TxOutSetInfo",
    
    # Asset models
    "AssetInfo", "AssetData", "CacheInfo", "ListAssetResult",
    
    # Network models
    "NetworkInfo", "PeerInfo", "LocalAddress", "Network",
    
    # Mining models
    "MiningInfo", "MiningStats",
    
    # Address index models
    "AddressBalance", "AddressDelta", "AddressUtxo", "AddressMempool",
    
    # Raw transaction models
    "DecodedTransaction", "DecodedScript", "TransactionInput", "TransactionOutput",
    
    # Wallet models
    "WalletInfo", "WalletTransaction", "UnspentOutput",
    
    # Utility functions
    "DEFAULT_DATADIR",
    "stress_test",
] 