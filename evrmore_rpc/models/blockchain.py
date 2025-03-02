"""
evrmore-rpc: Blockchain models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
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

class TxOut(BaseModel):
    """Model for 'gettxout' response"""
    bestblock: str = Field(..., description="The hash of the block at the tip of the chain")
    confirmations: int = Field(..., description="The number of confirmations")
    value: Decimal = Field(..., description="The transaction value in EVR")
    scriptPubKey: Dict[str, Any] = Field(..., description="The script key")
    coinbase: bool = Field(..., description="Whether this is a coinbase transaction output")

class TxOutSetInfo(BaseModel):
    """Model for 'gettxoutsetinfo' response"""
    height: int = Field(..., description="The current block height (index)")
    bestblock: str = Field(..., description="The hash of the block at the tip of the chain")
    transactions: int = Field(..., description="The number of transactions with unspent outputs")
    txouts: int = Field(..., description="The number of unspent transaction outputs")
    bogosize: int = Field(..., description="A meaningless metric for UTXO set size")
    hash_serialized_2: str = Field(..., description="The serialized hash")
    disk_size: int = Field(..., description="The estimated size of the chainstate on disk")
    total_amount: Decimal = Field(..., description="The total amount of coins in the UTXO set") 