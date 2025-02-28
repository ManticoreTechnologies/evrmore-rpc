from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class AddressBalance(BaseModel):
    """Model for 'getaddressbalance' response"""
    balance: Decimal = Field(..., description="The current balance in satoshis")
    received: Decimal = Field(..., description="The total number of satoshis received")

class AddressDelta(BaseModel):
    """Model for items in 'getaddressdeltas' response"""
    satoshis: Decimal = Field(..., description="The difference in satoshis")
    txid: str = Field(..., description="The related txid")
    index: int = Field(..., description="The related input or output index")
    blockindex: int = Field(..., description="The related block index")
    height: int = Field(..., description="The block height")
    address: str = Field(..., description="The address")

class MempoolEntry(BaseModel):
    """Model for items in 'getaddressmempool' response"""
    address: str = Field(..., description="The address")
    txid: str = Field(..., description="The transaction id")
    index: int = Field(..., description="The index")
    satoshis: Decimal = Field(..., description="The difference in satoshis")
    timestamp: int = Field(..., description="The time the entry was added to the mempool")
    prevtxid: Optional[str] = Field(None, description="The previous txid (if spending)")
    prevout: Optional[int] = Field(None, description="The previous transaction output index (if spending)")

class AddressUtxo(BaseModel):
    """Model for items in 'getaddressutxos' response"""
    address: str = Field(..., description="The address")
    txid: str = Field(..., description="The output txid")
    outputIndex: int = Field(..., description="The output index")
    script: str = Field(..., description="The script hex")
    satoshis: Decimal = Field(..., description="The number of satoshis")
    height: int = Field(..., description="The block height")

def wrap_addressindex_commands(client):
    """Add typed addressindex commands to the client."""
    
    def getaddressbalance(addresses: Union[str, List[str]]) -> AddressBalance:
        """Get the balance for address(es)."""
        if isinstance(addresses, str):
            addresses = [addresses]
        result = client.execute_command("getaddressbalance", {"addresses": addresses})
        return AddressBalance.model_validate(result)
    
    def getaddressdeltas(addresses: Union[str, List[str]], start: Optional[int] = None, end: Optional[int] = None) -> List[AddressDelta]:
        """Get all changes for address(es)."""
        if isinstance(addresses, str):
            addresses = [addresses]
        params = {"addresses": addresses}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        result = client.execute_command("getaddressdeltas", params)
        return [AddressDelta.model_validate(delta) for delta in result]
    
    def getaddressmempool(addresses: Union[str, List[str]]) -> List[MempoolEntry]:
        """Get all mempool entries for address(es)."""
        if isinstance(addresses, str):
            addresses = [addresses]
        result = client.execute_command("getaddressmempool", {"addresses": addresses})
        return [MempoolEntry.model_validate(entry) for entry in result]
    
    def getaddresstxids(addresses: Union[str, List[str]], start: Optional[int] = None, end: Optional[int] = None) -> List[str]:
        """Get all txids for address(es)."""
        if isinstance(addresses, str):
            addresses = [addresses]
        params = {"addresses": addresses}
        if start is not None:
            params["start"] = start
        if end is not None:
            params["end"] = end
        return client.execute_command("getaddresstxids", params)
    
    def getaddressutxos(addresses: Union[str, List[str]], chainInfo: bool = False) -> Union[List[AddressUtxo], Dict]:
        """Get all unspent outputs for address(es)."""
        if isinstance(addresses, str):
            addresses = [addresses]
        params = {"addresses": addresses, "chainInfo": chainInfo}
        result = client.execute_command("getaddressutxos", params)
        if chainInfo:
            return result  # Returns dict with utxos and chain state
        return [AddressUtxo.model_validate(utxo) for utxo in result]
    
    # Add methods to client
    client.getaddressbalance = getaddressbalance
    client.getaddressdeltas = getaddressdeltas
    client.getaddressmempool = getaddressmempool
    client.getaddresstxids = getaddresstxids
    client.getaddressutxos = getaddressutxos
    
    return client 