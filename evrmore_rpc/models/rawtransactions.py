"""
evrmore-rpc: Raw transaction models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class ScriptSig(BaseModel):
    """Model for scriptsig in transaction inputs"""
    asm: str = Field(..., description="The asm")
    hex: str = Field(..., description="The hex")
    
class ScriptPubKey(BaseModel):
    """Model for scriptpubkey in transaction outputs"""
    asm: str = Field(..., description="The asm")
    hex: str = Field(..., description="The hex")
    reqSigs: Optional[int] = Field(None, description="The required sigs")
    type: str = Field(..., description="The type, eg 'pubkeyhash'")
    addresses: Optional[List[str]] = Field(None, description="The addresses")
    
class TransactionInput(BaseModel):
    """Model for transaction inputs in 'decoderawtransaction' response"""
    txid: str = Field(..., description="The transaction id")
    vout: int = Field(..., description="The output number")
    scriptSig: ScriptSig = Field(..., description="The script")
    sequence: int = Field(..., description="The script sequence number")
    
class TransactionOutput(BaseModel):
    """Model for transaction outputs in 'decoderawtransaction' response"""
    value: Decimal = Field(..., description="The value in EVR")
    n: int = Field(..., description="The index")
    scriptPubKey: ScriptPubKey = Field(..., description="The script key")
    
class DecodedTransaction(BaseModel):
    """Model for 'decoderawtransaction' response"""
    txid: str = Field(..., description="The transaction id")
    hash: str = Field(..., description="The transaction hash")
    size: int = Field(..., description="The transaction size")
    vsize: int = Field(..., description="The virtual transaction size")
    weight: int = Field(..., description="The transaction's weight")
    version: int = Field(..., description="The version")
    locktime: int = Field(..., description="The lock time")
    vin: List[TransactionInput] = Field(..., description="The transaction inputs")
    vout: List[TransactionOutput] = Field(..., description="The transaction outputs")
    
class DecodedScript(BaseModel):
    """Model for 'decodescript' response"""
    asm: str = Field(..., description="Script public key")
    hex: str = Field(..., description="Hex encoded public key")
    type: str = Field(..., description="The output type")
    reqSigs: Optional[int] = Field(None, description="The required signatures")
    addresses: Optional[List[str]] = Field(None, description="The addresses")
    p2sh: Optional[str] = Field(None, description="address of P2SH script wrapping this redeem script")
    
class SignRawTransactionResult(BaseModel):
    """Model for 'signrawtransaction' response"""
    hex: str = Field(..., description="The hex-encoded raw transaction with signature(s)")
    complete: bool = Field(..., description="If the transaction has a complete set of signatures")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Script verification errors (if there are any)")
    
class FundRawTransactionResult(BaseModel):
    """Model for 'fundrawtransaction' response"""
    hex: str = Field(..., description="The resulting raw transaction (hex-encoded string)")
    fee: Decimal = Field(..., description="Fee in EVR the resulting transaction pays")
    changepos: int = Field(..., description="The position of the added change output, or -1") 