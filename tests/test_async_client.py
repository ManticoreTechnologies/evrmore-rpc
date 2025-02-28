import pytest
import asyncio
from decimal import Decimal

from evrmore_rpc import EvrmoreAsyncRPCClient, EvrmoreRPCError

# Async tests require pytest-asyncio
pytestmark = pytest.mark.asyncio

class TestEvrmoreAsyncRPCClient:
    """Test suite for the EvrmoreAsyncRPCClient."""
    
    async def test_initialization(self):
        """Test client initialization."""
        client = EvrmoreAsyncRPCClient()
        await client.initialize()
        assert client._initialized is True
        
    async def test_context_manager(self):
        """Test client as async context manager."""
        async with EvrmoreAsyncRPCClient() as client:
            assert client._initialized is True
            
    async def test_getblockcount(self):
        """Test getblockcount command."""
        async with EvrmoreAsyncRPCClient() as client:
            count = await client.getblockcount()
            assert isinstance(count, int)
            assert count > 0
            
    async def test_getblockchaininfo(self):
        """Test getblockchaininfo command."""
        async with EvrmoreAsyncRPCClient() as client:
            info = await client.getblockchaininfo()
            assert info.chain in ["main", "test", "regtest"]
            assert isinstance(info.blocks, int)
            assert isinstance(info.difficulty, Decimal)
            
    async def test_getblock(self):
        """Test getblock command."""
        async with EvrmoreAsyncRPCClient() as client:
            # First get a block hash
            count = await client.getblockcount()
            test_height = 1 if count > 1 else 0
            block_hash = await client.getblockhash(test_height)
            
            # Now get the block
            block = await client.getblock(block_hash)
            assert block.hash == block_hash
            assert block.height == test_height
            assert isinstance(block.time, int)
            
    async def test_listassets(self):
        """Test listassets command."""
        async with EvrmoreAsyncRPCClient() as client:
            assets = await client.listassets()
            assert isinstance(assets, dict)
            
    async def test_parallel_requests(self):
        """Test running multiple requests in parallel."""
        async with EvrmoreAsyncRPCClient() as client:
            # Run 3 commands in parallel
            count, info, difficulty = await asyncio.gather(
                client.getblockcount(),
                client.getblockchaininfo(),
                client.getdifficulty()
            )
            
            assert isinstance(count, int)
            assert count > 0
            assert info.chain in ["main", "test", "regtest"]
            assert isinstance(difficulty, Decimal)
            
    async def test_error_handling(self):
        """Test error handling."""
        async with EvrmoreAsyncRPCClient() as client:
            with pytest.raises(EvrmoreRPCError):
                # This should fail with an invalid block hash
                await client.getblock("1111111111111111111111111111111111111111111111111111111111111111")
                
    async def test_authentication_error(self):
        """Test authentication error."""
        # Use invalid credentials
        client = EvrmoreAsyncRPCClient(rpcuser="invalid", rpcpassword="invalid")
        await client.initialize()
        
        with pytest.raises(EvrmoreRPCError) as excinfo:
            await client.getblockcount()
        assert "Command failed" in str(excinfo.value) 