"""
evrmore-rpc: Models for Evrmore RPC responses

Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details

This module provides Pydantic models for all Evrmore RPC response data structures.
These models provide:
- Type safety with comprehensive type hints
- Automatic validation of response data
- Consistent access patterns for all response types
- Built-in serialization and deserialization
- Clear documentation of all fields and their purposes

For each RPC command, a corresponding model is provided that matches
the structure of the response data. This ensures that all data returned
from the RPC is properly typed and validated.

The models are organized into categories matching the Evrmore RPC command groups:
- Base: Common types used across multiple command groups
- Blockchain: Block, transaction, and chain information
- Assets: Asset data and operations
- Network: Network connection and peer information
- Mining: Mining status and control
- Address Index: Address-based indexing and queries
- Raw Transactions: Low-level transaction handling
- Wallet: Wallet management and transactions
"""

# Base models
from evrmore_rpc.models.base import (
    Amount,
    Address,
    Asset,
    Transaction,
    Block as BaseBlock,
    RPCResponse
)

# Blockchain models
from evrmore_rpc.models.blockchain import (
    BlockchainInfo,
    Block,
    BlockHeader,
    ChainTip,
    MempoolInfo,
    TxOut,
    TxOutSetInfo
)

# Asset models
from evrmore_rpc.models.assets import (
    AssetInfo,
    AssetData,
    CacheInfo,
    ListAssetResult
)

# Network models
from evrmore_rpc.models.network import (
    NetworkInfo,
    PeerInfo,
    LocalAddress,
    Network
)

# Mining models
from evrmore_rpc.models.mining import (
    MiningInfo,
    MiningStats
)

# Address index models
from evrmore_rpc.models.addressindex import (
    AddressBalance,
    AddressDelta,
    AddressUtxo,
    AddressMempool
)

# Raw transaction models
from evrmore_rpc.models.rawtransactions import (
    DecodedTransaction,
    DecodedScript,
    TransactionInput,
    TransactionOutput
)

# Wallet models
from evrmore_rpc.models.wallet import (
    WalletInfo,
    WalletTransaction,
    UnspentOutput
)

__all__ = [
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
    "WalletInfo", "WalletTransaction", "UnspentOutput"
] 