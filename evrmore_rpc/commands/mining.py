from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class MiningInfo(BaseModel):
    """Model for 'getmininginfo' response"""
    blocks: int = Field(..., description="The current block")
    currentblockweight: int = Field(..., description="The last block weight")
    currentblocktx: int = Field(..., description="The last block transaction")
    difficulty: Decimal = Field(..., description="The current difficulty")
    networkhashps: Decimal = Field(..., description="The network hashes per second")
    hashespersec: int = Field(..., description="The hashes per second of built-in miner")
    pooledtx: int = Field(..., description="The size of the mempool")
    chain: str = Field(..., description="Current network name (main, test, regtest)")
    warnings: str = Field("", description="Any network and blockchain warnings")
    errors: Optional[str] = Field(None, description="DEPRECATED. Same as warnings")

class BlockTemplate(BaseModel):
    """Model for 'getblocktemplate' response"""
    version: int = Field(..., description="The block version")
    rules: List[str] = Field(..., description="List of rules that the server supports")
    vbavailable: Dict = Field(..., description="Set of pending, supported versionbit (BIP 9) softfork deployments")
    vbrequired: int = Field(..., description="Bit mask of versionbits the server requires set in submissions")
    previousblockhash: str = Field(..., description="The hash of current highest block")
    transactions: List[Dict] = Field(..., description="Contents of non-coinbase transactions that should be included in the next block")
    coinbaseaux: Dict = Field(..., description="Data that should be included in the coinbase's scriptSig content")
    coinbasevalue: int = Field(..., description="Maximum allowable input to coinbase transaction")
    longpollid: str = Field(..., description="An id to include with a request to longpoll on an update to this template")
    target: str = Field(..., description="The hash target")
    mintime: int = Field(..., description="The minimum timestamp appropriate for the next block time")
    mutable: List[str] = Field(..., description="List of ways the block template may be changed")
    noncerange: str = Field(..., description="A range of valid nonces")
    sigoplimit: int = Field(..., description="Limit of sigops in blocks")
    sizelimit: int = Field(..., description="Limit of block size")
    weightlimit: int = Field(..., description="Limit of block weight")
    curtime: int = Field(..., description="Current timestamp in seconds since epoch")
    bits: str = Field(..., description="Compressed target of next block")
    height: int = Field(..., description="Height of the next block")

def wrap_mining_commands(client):
    """Add typed mining commands to the client."""
    
    def getblocktemplate(template_request: Optional[Dict] = None) -> BlockTemplate:
        """Get block template for mining."""
        if template_request:
            result = client.execute_command("getblocktemplate", template_request)
        else:
            result = client.execute_command("getblocktemplate")
        return BlockTemplate.model_validate(result)
    
    def getevrprogpowhash(header_hash: str, mix_hash: str, nonce: int, height: int, target: str) -> str:
        """Get EVR ProgPoW hash."""
        return client.execute_command("getevrprogpowhash", header_hash, mix_hash, nonce, height, target)
    
    def getmininginfo() -> MiningInfo:
        """Get mining-related information."""
        result = client.execute_command("getmininginfo")
        return MiningInfo.model_validate(result)
    
    def getnetworkhashps(nblocks: int = 120, height: int = -1) -> Decimal:
        """Get network hashes per second."""
        result = client.execute_command("getnetworkhashps", nblocks, height)
        return Decimal(str(result))
    
    def pprpcsb(header_hash: str, mix_hash: str, nonce: str) -> bool:
        """Submit ProgPoW solution."""
        return client.execute_command("pprpcsb", header_hash, mix_hash, nonce)
    
    def prioritisetransaction(txid: str, dummy_value: int, fee_delta: int) -> bool:
        """Prioritize a transaction."""
        return client.execute_command("prioritisetransaction", txid, dummy_value, fee_delta)
    
    def submitblock(hexdata: str, dummy: Optional[str] = None) -> Optional[str]:
        """Submit a new block to the network."""
        if dummy:
            return client.execute_command("submitblock", hexdata, dummy)
        return client.execute_command("submitblock", hexdata)
    
    # Add methods to client
    client.getblocktemplate = getblocktemplate
    client.getevrprogpowhash = getevrprogpowhash
    client.getmininginfo = getmininginfo
    client.getnetworkhashps = getnetworkhashps
    client.pprpcsb = pprpcsb
    client.prioritisetransaction = prioritisetransaction
    client.submitblock = submitblock
    
    return client 