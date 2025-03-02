#!/usr/bin/env python3
"""
Tests for the EvrmoreClient class.
"""

import os
import pytest
import asyncio
from unittest.mock import patch, MagicMock, AsyncMock

from evrmore_rpc import EvrmoreClient, EvrmoreRPCError

# Skip tests if no Evrmore node is available
pytestmark = pytest.mark.skipif(
    os.environ.get("EVRMORE_SKIP_TESTS") == "1",
    reason="Skipping tests that require an Evrmore node"
)

class TestEvrmoreClient:
    """Tests for the EvrmoreClient class."""
    
    def test_init(self):
        """Test client initialization."""
        client = EvrmoreClient()
        assert client is not None
    
    def test_sync_call(self):
        """Test synchronous RPC call."""
        with patch('requests.Session.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "test_result", "error": None, "id": 1}
            mock_post.return_value = mock_response
            
            client = EvrmoreClient()
            # Initialize the session manually
            client.initialize_sync()
            result = client.test_method()
            
            assert result == "test_result"
            mock_post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_async_call(self):
        """Test asynchronous RPC call."""
        with patch('aiohttp.ClientSession.post') as mock_post:
            # Create a proper AsyncMock for the response
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Set up the json method to return a coroutine that returns the result
            async def mock_json():
                return {"result": "test_result", "error": None, "id": 1}
            
            mock_response.json = mock_json
            mock_context = AsyncMock()
            mock_context.__aenter__.return_value = mock_response
            mock_post.return_value = mock_context
            
            client = EvrmoreClient()
            # Initialize the session manually
            await client.initialize_async()
            result = await client.test_method()
            
            assert result == "test_result"
            mock_post.assert_called_once()
    
    def test_error_handling(self):
        """Test error handling."""
        with patch('requests.Session.post') as mock_post:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "result": None, 
                "error": {"code": -1, "message": "Test error"}, 
                "id": 1
            }
            mock_post.return_value = mock_response
            
            client = EvrmoreClient()
            # Initialize the session manually
            client.initialize_sync()
            with pytest.raises(EvrmoreRPCError) as excinfo:
                client.test_method()
            
            assert "Test error" in str(excinfo.value)
    
    def test_reset(self):
        """Test client reset."""
        client = EvrmoreClient()
        # Force sync mode
        client = client.force_sync()
        assert client._async_mode is False
        
        # Reset
        client = client.reset()
        assert client._async_mode is None
    
    def test_force_sync(self):
        """Test force_sync method."""
        client = EvrmoreClient()
        client = client.force_sync()
        assert client._async_mode is False
    
    def test_force_async(self):
        """Test force_async method."""
        client = EvrmoreClient()
        client = client.force_async()
        assert client._async_mode is True 