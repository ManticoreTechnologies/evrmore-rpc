from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class TxInput(BaseModel):
    """Model for transaction input"""
    txid: str = Field(..., description="The transaction id")
    vout: int = Field(..., description="The output number")
    sequence: Optional[int] = Field(None, description="The sequence number")

class AssetTransfer(BaseModel):
    """Model for asset transfer operation"""
    asset_name: str = Field(..., description="The name of the asset to transfer")
    amount: Decimal = Field(..., description="The amount of the asset to transfer")

class AssetTransferWithMessage(BaseModel):
    """Model for asset transfer with message operation"""
    asset_name: str = Field(..., description="The name of the asset to transfer")
    amount: Decimal = Field(..., description="The amount of the asset to transfer")
    message: str = Field(..., description="The IPFS hash or txid hash of the message")
    expire_time: int = Field(..., description="UTC time in seconds when the message expires")

class AssetIssue(BaseModel):
    """Model for asset issue operation"""
    asset_name: str = Field(..., description="The name of the new asset")
    asset_quantity: Decimal = Field(..., description="The quantity of the asset to issue")
    units: int = Field(..., ge=1, le=8, description="The number of decimals for the asset")
    reissuable: bool = Field(..., description="Whether the asset can be reissued")
    has_ipfs: bool = Field(..., description="Whether the asset has IPFS metadata")
    ipfs_hash: Optional[str] = Field(None, description="The IPFS hash for asset metadata")

class AssetReissue(BaseModel):
    """Model for asset reissue operation"""
    asset_name: str = Field(..., description="The name of the asset to reissue")
    asset_quantity: Decimal = Field(..., description="The quantity to reissue")
    reissuable: Optional[bool] = Field(True, description="Whether the asset remains reissuable")
    ipfs_hash: Optional[str] = Field(None, description="New IPFS hash for asset metadata")
    owner_change_address: Optional[str] = Field(None, description="Address to send the owner token to")

class DecodedScript(BaseModel):
    """Model for 'decodescript' response"""
    asm: str = Field(..., description="Script public key in assembly")
    type: str = Field(..., description="Type of script")
    reqSigs: Optional[int] = Field(None, description="Number of required signatures")
    addresses: Optional[List[str]] = Field(None, description="List of addresses involved in the script")
    p2sh: str = Field(..., description="P2SH address")

class DecodedRawTransaction(BaseModel):
    """Model for 'decoderawtransaction' response"""
    txid: str = Field(..., description="The transaction id")
    hash: str = Field(..., description="The transaction hash")
    size: int = Field(..., description="The transaction size")
    vsize: int = Field(..., description="The virtual transaction size")
    weight: int = Field(..., description="The transaction's weight")
    version: int = Field(..., description="The version")
    locktime: int = Field(..., description="The lock time")
    vin: List[Dict] = Field(..., description="The transaction inputs")
    vout: List[Dict] = Field(..., description="The transaction outputs")

def wrap_rawtransaction_commands(client):
    """Add typed raw transaction commands to the client."""
    
    def combinerawtransaction(txs: List[str]) -> str:
        """Combine multiple partially signed transactions into one."""
        return client.execute_command("combinerawtransaction", txs)
    
    def createrawtransaction(
        inputs: List[TxInput],
        outputs: Dict[str, Union[Decimal, Dict, str]],
        locktime: Optional[int] = None
    ) -> str:
        """Create a transaction spending given inputs and creating new outputs."""
        inputs_list = [input.model_dump(exclude_none=True) for input in inputs]
        if locktime is not None:
            return client.execute_command("createrawtransaction", inputs_list, outputs, locktime)
        return client.execute_command("createrawtransaction", inputs_list, outputs)
    
    def decoderawtransaction(hexstring: str) -> DecodedRawTransaction:
        """Return a JSON object representing the serialized, hex-encoded transaction."""
        result = client.execute_command("decoderawtransaction", hexstring)
        return DecodedRawTransaction.model_validate(result)
    
    def decodescript(hexstring: str) -> DecodedScript:
        """Decode a hex-encoded script."""
        result = client.execute_command("decodescript", hexstring)
        return DecodedScript.model_validate(result)
    
    def fundrawtransaction(
        hexstring: str,
        options: Optional[Dict] = None
    ) -> Dict[str, Union[str, Decimal]]:
        """Add inputs to a transaction until it has enough in value to meet its out value."""
        if options is not None:
            return client.execute_command("fundrawtransaction", hexstring, options)
        return client.execute_command("fundrawtransaction", hexstring)
    
    def getrawtransaction(
        txid: str,
        verbose: bool = False
    ) -> Union[str, Dict]:
        """Get the raw transaction data."""
        return client.execute_command("getrawtransaction", txid, verbose)
    
    def sendrawtransaction(
        hexstring: str,
        allowhighfees: bool = False
    ) -> str:
        """Submit a raw transaction to the network."""
        return client.execute_command("sendrawtransaction", hexstring, allowhighfees)
    
    def signrawtransaction(
        hexstring: str,
        prevtxs: Optional[List[Dict]] = None,
        privkeys: Optional[List[str]] = None,
        sighashtype: str = "ALL"
    ) -> Dict[str, Union[str, bool, List]]:
        """Sign inputs for a raw transaction."""
        if prevtxs is not None and privkeys is not None:
            return client.execute_command("signrawtransaction", hexstring, prevtxs, privkeys, sighashtype)
        elif prevtxs is not None:
            return client.execute_command("signrawtransaction", hexstring, prevtxs)
        return client.execute_command("signrawtransaction", hexstring)
    
    def testmempoolaccept(
        rawtxs: List[str],
        allowhighfees: bool = False
    ) -> List[Dict[str, Union[bool, str, int]]]:
        """Test if transactions would be accepted by mempool."""
        return client.execute_command("testmempoolaccept", rawtxs, allowhighfees)
    
    # Add methods to client
    client.combinerawtransaction = combinerawtransaction
    client.createrawtransaction = createrawtransaction
    client.decoderawtransaction = decoderawtransaction
    client.decodescript = decodescript
    client.fundrawtransaction = fundrawtransaction
    client.getrawtransaction = getrawtransaction
    client.sendrawtransaction = sendrawtransaction
    client.signrawtransaction = signrawtransaction
    client.testmempoolaccept = testmempoolaccept
    
    return client 