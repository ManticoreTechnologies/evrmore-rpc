"""
evrmore-rpc: Address index models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class AddressBalance(BaseModel):
    """Model for 'getaddressbalance' response"""
    balance: int = Field(..., description="Balance in satoshis")
    received: int = Field(..., description="Total received in satoshis")
    
class AddressDelta(BaseModel):
    """Model for items in 'getaddressdeltas' response"""
    satoshis: int = Field(..., description="The difference of satoshis")
    txid: str = Field(..., description="The related transaction id")
    index: int = Field(..., description="The related input or output index")
    blockindex: int = Field(..., description="The related block index")
    height: int = Field(..., description="The block height")
    address: str = Field(..., description="The address")
    
class AddressUtxo(BaseModel):
    """Model for items in 'getaddressutxos' response"""
    address: str = Field(..., description="The address")
    txid: str = Field(..., description="The output txid")
    outputIndex: int = Field(..., description="The output index")
    script: str = Field(..., description="The script hex")
    satoshis: int = Field(..., description="The number of satoshis of the output")
    height: int = Field(..., description="The block height")
    
class AddressMempool(BaseModel):
    """Model for items in 'getaddressmempool' response"""
    address: str = Field(..., description="The address")
    txid: str = Field(..., description="The related txid")
    index: int = Field(..., description="The related input or output index")
    satoshis: int = Field(..., description="The difference of satoshis")
    timestamp: int = Field(..., description="The time the transaction entered the mempool (seconds)")
    prevtxid: Optional[str] = Field(None, description="The previous txid (if spending)")
    prevout: Optional[int] = Field(None, description="The previous transaction output index (if spending)")
    
class SpentInfo(BaseModel):
    """Model for 'getspentinfo' response"""
    txid: str = Field(..., description="The transaction id")
    index: int = Field(..., description="The spending input index")
    height: int = Field(..., description="The height of the block containing the spending transaction") 