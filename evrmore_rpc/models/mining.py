"""
evrmore-rpc: Mining models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class MiningInfo(BaseModel):
    """Model for 'getmininginfo' response"""
    blocks: int = Field(..., description="The current block")
    currentblockweight: Optional[int] = Field(None, description="The last block weight")
    currentblocktx: Optional[int] = Field(None, description="The last block transaction")
    difficulty: Decimal = Field(..., description="The current difficulty")
    difficulty_algorithm: str = Field(..., description="The current difficulty algorithm")
    networkhashps: float = Field(..., description="The network hashes per second")
    pooledtx: int = Field(..., description="The size of the mempool")
    chain: str = Field(..., description="Current network name")
    warnings: str = Field("", description="Any network and blockchain warnings")

class MiningStats(BaseModel):
    """Model for mining statistics"""
    hashrate: float = Field(..., description="Hashrate in hashes per second")
    difficulty: Decimal = Field(..., description="Current difficulty")
    block_time: float = Field(..., description="Average time between blocks in seconds")
    blocks_per_day: float = Field(..., description="Estimated blocks per day")
    
class BlockTemplate(BaseModel):
    """Model for 'getblocktemplate' response"""
    capabilities: List[str] = Field(..., description="Supported capabilities")
    version: int = Field(..., description="Block version")
    rules: List[str] = Field(..., description="Specific block rules that are to be enforced")
    vbavailable: Dict[str, int] = Field(..., description="Set of pending, supported versionbit (BIP 9) softfork deployments")
    vbrequired: int = Field(..., description="Bit mask of versionbits the server requires set in submissions")
    previousblockhash: str = Field(..., description="The hash of current highest block")
    transactions: List[Dict[str, Any]] = Field(..., description="Contents of non-coinbase transactions that should be included in the next block")
    coinbaseaux: Dict[str, str] = Field(..., description="Data that should be included in the coinbase's scriptSig content")
    coinbasevalue: int = Field(..., description="Maximum allowable input to coinbase transaction, including the generation award and transaction fees")
    longpollid: str = Field(..., description="An id to include with a request to longpoll on an update to this template")
    target: str = Field(..., description="The hash target")
    mintime: int = Field(..., description="The minimum timestamp appropriate for the next block time")
    mutable: List[str] = Field(..., description="List of ways the block template may be changed")
    noncerange: str = Field(..., description="A range of valid nonces")
    sigoplimit: int = Field(..., description="Limit of sigops in blocks")
    sizelimit: int = Field(..., description="Limit of block size")
    curtime: int = Field(..., description="Current timestamp in seconds since epoch")
    bits: str = Field(..., description="Compressed target of next block")
    height: int = Field(..., description="Height of the next block")
    default_witness_commitment: Optional[str] = Field(None, description="A default witness commitment for segwit blocks") 