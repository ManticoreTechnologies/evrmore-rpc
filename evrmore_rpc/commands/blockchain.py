from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class BlockchainInfo(BaseModel):
    """Model for 'getblockchaininfo' response"""
    chain: str = Field(..., description="Current network name")
    blocks: int = Field(..., description="The current number of blocks processed")
    headers: int = Field(..., description="The current number of headers we have validated")
    bestblockhash: str = Field(..., description="The hash of the currently best block")
    difficulty: Decimal = Field(..., description="The current difficulty")
    difficulty_algorithm: str = Field(..., description="The current difficulty algorithm")
    mediantime: int = Field(..., description="Median time for the current best block")
    verificationprogress: float = Field(..., description="Estimate of verification progress [0..1]")
    chainwork: str = Field(..., description="Total amount of work in active chain, in hexadecimal")
    size_on_disk: int = Field(..., description="The estimated size of the block and undo files on disk")
    pruned: bool = Field(..., description="If the blocks are subject to pruning")
    softforks: List[Dict] = Field(default_factory=list, description="Status of softforks")
    bip9_softforks: Dict = Field(default_factory=dict, description="Status of BIP9 softforks")
    warnings: str = Field("", description="Any network and blockchain warnings")

class Block(BaseModel):
    """Model for 'getblock' response"""
    hash: str = Field(..., description="The block hash (same as provided)")
    confirmations: int = Field(..., description="The number of confirmations")
    strippedsize: int = Field(..., description="The block size excluding witness data")
    size: int = Field(..., description="The block size")
    weight: int = Field(..., description="The block weight")
    height: int = Field(..., description="The block height or index")
    version: int = Field(..., description="The block version")
    versionHex: str = Field(..., description="The block version formatted in hexadecimal")
    merkleroot: str = Field(..., description="The merkle root")
    tx: List[str] = Field(..., description="The transaction ids")
    time: int = Field(..., description="The block time expressed in UNIX epoch time")
    mediantime: int = Field(..., description="The median block time expressed in UNIX epoch time")
    nonce: int = Field(..., description="The nonce")
    bits: str = Field(..., description="The bits")
    difficulty: Decimal = Field(..., description="The difficulty")
    chainwork: str = Field(..., description="Expected number of hashes required to produce the chain up to this block (in hex)")
    headerhash: str = Field(..., description="The hash of the block header")
    mixhash: str = Field(..., description="The mix hash")
    nonce64: int = Field(..., description="The 64-bit nonce")
    previousblockhash: Optional[str] = Field(None, description="The hash of the previous block")
    nextblockhash: Optional[str] = Field(None, description="The hash of the next block")

class BlockHeader(BaseModel):
    """Model for 'getblockheader' response"""
    hash: str = Field(..., description="The block hash")
    confirmations: int = Field(..., description="The number of confirmations")
    height: int = Field(..., description="The block height or index")
    version: int = Field(..., description="The block version")
    versionHex: str = Field(..., description="The block version formatted in hexadecimal")
    merkleroot: str = Field(..., description="The merkle root")
    time: int = Field(..., description="The block time expressed in UNIX epoch time")
    mediantime: int = Field(..., description="The median block time expressed in UNIX epoch time")
    nonce: int = Field(..., description="The nonce")
    bits: str = Field(..., description="The bits")
    difficulty: Decimal = Field(..., description="The difficulty")
    chainwork: str = Field(..., description="Expected number of hashes required to produce the chain up to this block (in hex)")
    previousblockhash: Optional[str] = Field(None, description="The hash of the previous block")
    nextblockhash: Optional[str] = Field(None, description="The hash of the next block")

class ChainTip(BaseModel):
    """Model for items in 'getchaintips' response"""
    height: int = Field(..., description="Height of the chain tip")
    hash: str = Field(..., description="Block hash of the tip")
    branchlen: int = Field(..., description="Length of branch connecting the tip to the main chain")
    status: str = Field(..., description="Status of the chain")

class MempoolInfo(BaseModel):
    """Model for 'getmempoolinfo' response"""
    loaded: bool = Field(..., description="True if the mempool is fully loaded")
    size: int = Field(..., description="Current tx count")
    bytes: int = Field(..., description="Sum of all virtual transaction sizes")
    usage: int = Field(..., description="Total memory usage for the mempool")
    maxmempool: int = Field(..., description="Maximum memory usage for the mempool")
    mempoolminfee: Decimal = Field(..., description="Minimum fee rate in EVR/kB for tx to be accepted")
    minrelaytxfee: Decimal = Field(..., description="Current minimum relay fee for transactions")

def wrap_blockchain_commands(client):
    """Add typed blockchain commands to the client."""
    
    def getblockchaininfo() -> BlockchainInfo:
        """Get current state of the blockchain."""
        result = client.execute_command("getblockchaininfo")
        return BlockchainInfo.model_validate(result)
    
    def getblock(blockhash: str, verbosity: int = 1) -> Union[str, Block, Dict]:
        """Get block data."""
        result = client.execute_command("getblock", blockhash, verbosity)
        if verbosity == 0:
            return result  # Returns hex-encoded data
        elif verbosity == 1:
            return Block.model_validate(result)
        return result  # verbosity 2 returns too much data to model easily
    
    def getblockheader(blockhash: str, verbose: bool = True) -> Union[str, BlockHeader]:
        """Get block header data."""
        result = client.execute_command("getblockheader", blockhash, verbose)
        if not verbose:
            return result  # Returns hex-encoded data
        return BlockHeader.model_validate(result)
    
    def getblockcount() -> int:
        """Get the height of the most-work fully-validated chain."""
        return client.execute_command("getblockcount")
    
    def getblockhash(height: int) -> str:
        """Get hash of block at specified height."""
        return client.execute_command("getblockhash", height)
    
    def getchaintips() -> List[ChainTip]:
        """Get information about all known chain tips."""
        result = client.execute_command("getchaintips")
        return [ChainTip.model_validate(tip) for tip in result]
    
    def getdifficulty() -> Decimal:
        """Get proof-of-work difficulty."""
        return Decimal(str(client.execute_command("getdifficulty")))
    
    def getmempoolinfo() -> MempoolInfo:
        """Get mempool information."""
        result = client.execute_command("getmempoolinfo")
        return MempoolInfo.model_validate(result)
    
    # Add methods to client
    client.getblockchaininfo = getblockchaininfo
    client.getblock = getblock
    client.getblockheader = getblockheader
    client.getblockcount = getblockcount
    client.getblockhash = getblockhash
    client.getchaintips = getchaintips
    client.getdifficulty = getdifficulty
    client.getmempoolinfo = getmempoolinfo
    
    return client 