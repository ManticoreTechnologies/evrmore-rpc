"""
evrmore-rpc: A streamlined, high-performance Python wrapper for Evrmore blockchain
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details

This library provides a polymorphic client that can be used both synchronously and asynchronously
with the same API. The client automatically detects the context (sync or async) and adapts accordingly.
"""

__version__ = "3.2.1"

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