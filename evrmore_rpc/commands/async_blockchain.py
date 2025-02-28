from typing import Dict, List, Optional, Union
from decimal import Decimal

from evrmore_rpc.commands.blockchain import (
    BlockchainInfo,
    Block,
    BlockHeader,
    ChainTip,
    MempoolInfo,
)

async def wrap_blockchain_commands_async(client):
    """Add typed async blockchain commands to the client."""
    
    async def getblockchaininfo() -> BlockchainInfo:
        """Get current state of the blockchain."""
        result = await client.execute_command("getblockchaininfo")
        return BlockchainInfo.model_validate(result)
    
    async def getblock(blockhash: str, verbosity: int = 1) -> Union[str, Block, Dict]:
        """Get block data."""
        result = await client.execute_command("getblock", blockhash, verbosity)
        if verbosity == 0:
            return result  # Returns hex-encoded data
        elif verbosity == 1:
            return Block.model_validate(result)
        return result  # verbosity 2 returns too much data to model easily
    
    async def getblockheader(blockhash: str, verbose: bool = True) -> Union[str, BlockHeader]:
        """Get block header data."""
        result = await client.execute_command("getblockheader", blockhash, verbose)
        if not verbose:
            return result  # Returns hex-encoded data
        return BlockHeader.model_validate(result)
    
    async def getblockcount() -> int:
        """Get the height of the most-work fully-validated chain."""
        return await client.execute_command("getblockcount")
    
    async def getblockhash(height: int) -> str:
        """Get hash of block at specified height."""
        return await client.execute_command("getblockhash", height)
    
    async def getchaintips() -> List[ChainTip]:
        """Get information about all known chain tips."""
        result = await client.execute_command("getchaintips")
        return [ChainTip.model_validate(tip) for tip in result]
    
    async def getdifficulty() -> Decimal:
        """Get proof-of-work difficulty."""
        return Decimal(str(await client.execute_command("getdifficulty")))
    
    async def getmempoolinfo() -> MempoolInfo:
        """Get mempool information."""
        result = await client.execute_command("getmempoolinfo")
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