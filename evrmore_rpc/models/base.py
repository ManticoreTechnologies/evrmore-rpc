from typing import Optional, List, Union, Dict
from pydantic import BaseModel, Field
from decimal import Decimal

class Amount(BaseModel):
    """Model for representing EVR amounts
       The maximum precision is 8 decimal places
    """
    value: Decimal = Field(..., description="Amount in EVR")
    
class Address(BaseModel):
    """Model for Evrmore addresses"""
    address: str = Field(..., description="Evrmore address")
    
class Asset(BaseModel):
    """Model for Evrmore assets"""
    name: str = Field(..., description="Asset name")
    amount: Optional[Decimal] = Field(None, description="Asset amount")
    
class Transaction(BaseModel):
    """Model for transaction identifiers"""
    txid: str = Field(..., description="Transaction ID")
    vout: Optional[int] = Field(None, description="Output index")
    
class Block(BaseModel):
    """Model for block identifiers"""
    hash: Optional[str] = Field(None, description="Block hash")
    height: Optional[int] = Field(None, description="Block height")
    
class RPCResponse(BaseModel):
    """Base model for RPC responses"""
    error: Optional[str] = None
    result: Optional[Union[Dict, List, str, int, float, bool]] = None 