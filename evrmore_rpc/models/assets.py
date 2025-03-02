"""
evrmore-rpc: Asset models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class AssetInfo(BaseModel):
    """Model for 'getassetdata' response"""
    name: str = Field(..., description="Asset name")
    amount: Decimal = Field(..., description="Asset amount")
    units: int = Field(..., description="Asset units/precision")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS data")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if has_ipfs is true")
    txid: Optional[str] = Field(None, description="Transaction ID of issuance")
    blockhash: Optional[str] = Field(None, description="Block hash of issuance")

class AssetData(BaseModel):
    """Model for asset data in various responses"""
    name: str = Field(..., description="Asset name")
    amount: Decimal = Field(..., description="Asset amount")
    units: int = Field(..., description="Asset units/precision")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS data")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if has_ipfs is true")
    
class CacheInfo(BaseModel):
    """Model for 'getcacheinfo' response"""
    size: int = Field(..., description="Size of the cache")
    asset_cache: Dict[str, int] = Field(..., description="Asset cache statistics")
    asset_db_cache: Dict[str, int] = Field(..., description="Asset database cache statistics")
    my_asset_cache: Dict[str, int] = Field(..., description="My asset cache statistics")
    restricted_cache: Dict[str, int] = Field(..., description="Restricted asset cache statistics")
    restricted_db_cache: Dict[str, int] = Field(..., description="Restricted asset database cache statistics")
    restricted_global_cache: Dict[str, int] = Field(..., description="Restricted global cache statistics")
    restricted_global_db_cache: Dict[str, int] = Field(..., description="Restricted global database cache statistics")
    restricted_verifier_cache: Dict[str, int] = Field(..., description="Restricted verifier cache statistics")
    restricted_verifier_db_cache: Dict[str, int] = Field(..., description="Restricted verifier database cache statistics")
    qualifier_cache: Dict[str, int] = Field(..., description="Qualifier cache statistics")
    qualifier_db_cache: Dict[str, int] = Field(..., description="Qualifier database cache statistics")
    
class ListAssetResult(BaseModel):
    """Model for items in 'listassets' response"""
    name: str = Field(..., description="Asset name")
    amount: Decimal = Field(..., description="Asset amount")
    units: int = Field(..., description="Asset units/precision")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS data")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if has_ipfs is true")
    block_height: Optional[int] = Field(None, description="Block height of issuance")
    blockhash: Optional[str] = Field(None, description="Block hash of issuance")
    txid: Optional[str] = Field(None, description="Transaction ID of issuance")
    
class RestrictedAssetData(BaseModel):
    """Model for restricted asset data"""
    name: str = Field(..., description="Asset name")
    amount: Decimal = Field(..., description="Asset amount")
    units: int = Field(..., description="Asset units/precision")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS data")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if has_ipfs is true")
    verifier_string: str = Field(..., description="Verifier string for the restricted asset")
    
class QualifierAssetData(BaseModel):
    """Model for qualifier asset data"""
    name: str = Field(..., description="Asset name")
    amount: Decimal = Field(..., description="Asset amount")
    units: int = Field(..., description="Asset units/precision")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS data")
    ipfs_hash: Optional[str] = Field(None, description="IPFS hash if has_ipfs is true") 