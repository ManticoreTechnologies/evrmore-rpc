"""
evrmore-rpc: Wallet models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class WalletInfo(BaseModel):
    """Model for 'getwalletinfo' response"""
    walletname: str = Field(..., description="The wallet name")
    walletversion: int = Field(..., description="The wallet version")
    balance: Decimal = Field(..., description="The total confirmed balance of the wallet")
    unconfirmed_balance: Decimal = Field(..., description="The total unconfirmed balance of the wallet")
    immature_balance: Decimal = Field(..., description="The total immature balance of the wallet")
    txcount: int = Field(..., description="The total number of transactions in the wallet")
    keypoololdest: int = Field(..., description="The timestamp (seconds since Unix epoch) of the oldest pre-generated key in the key pool")
    keypoolsize: int = Field(..., description="How many new keys are pre-generated")
    unlocked_until: Optional[int] = Field(None, description="The timestamp in seconds since epoch (midnight Jan 1 1970 GMT) that the wallet is unlocked for transfers, or 0 if the wallet is locked")
    paytxfee: Decimal = Field(..., description="The transaction fee configuration, set in EVR/kB")
    hdmasterkeyid: Optional[str] = Field(None, description="The Hash160 of the HD master pubkey")
    
class WalletTransaction(BaseModel):
    """Model for wallet transaction information"""
    amount: Decimal = Field(..., description="The amount in EVR")
    confirmations: int = Field(..., description="The number of confirmations")
    blockhash: Optional[str] = Field(None, description="The block hash")
    blockindex: Optional[int] = Field(None, description="The block index")
    blocktime: Optional[int] = Field(None, description="The time in seconds since epoch (1 Jan 1970 GMT)")
    txid: str = Field(..., description="The transaction id")
    time: int = Field(..., description="The transaction time in seconds since epoch (1 Jan 1970 GMT)")
    timereceived: int = Field(..., description="The time received in seconds since epoch (1 Jan 1970 GMT)")
    comment: Optional[str] = Field(None, description="Comment")
    to: Optional[str] = Field(None, description="Comment to")
    
class UnspentOutput(BaseModel):
    """Model for items in 'listunspent' response"""
    txid: str = Field(..., description="The transaction id")
    vout: int = Field(..., description="The output number")
    address: str = Field(..., description="The address")
    account: Optional[str] = Field(None, description="The associated account, or '' for the default account")
    scriptPubKey: str = Field(..., description="The script key")
    amount: Decimal = Field(..., description="The transaction amount in EVR")
    confirmations: int = Field(..., description="The number of confirmations")
    redeemScript: Optional[str] = Field(None, description="The redeem script if scriptPubKey is P2SH")
    spendable: bool = Field(..., description="Whether we have the private keys to spend this output")
    solvable: bool = Field(..., description="Whether we know how to spend this output, ignoring the lack of keys")
    safe: bool = Field(..., description="Whether this output is considered safe to spend")
    
class ReceivedByAddress(BaseModel):
    """Model for items in 'listreceivedbyaddress' response"""
    address: str = Field(..., description="The receiving address")
    account: str = Field(..., description="The account of the receiving address")
    amount: Decimal = Field(..., description="The total amount in EVR received by the address")
    confirmations: int = Field(..., description="The number of confirmations of the most recent transaction included")
    label: str = Field(..., description="The label of the receiving address")
    txids: List[str] = Field(..., description="The ids of transactions received with the address")
    
class AddressGrouping(BaseModel):
    """Model for items in 'listaddressgroupings' response"""
    address: str = Field(..., description="The address")
    amount: Decimal = Field(..., description="The amount in EVR")
    account: Optional[str] = Field(None, description="The account") 