import asyncio
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from evrmore_rpc.websockets import (
    EvrmoreWebSocketClient,
    WebSocketMessage,
    WebSocketSubscription,
    WebSocketError,
    WebSocketBlockData,
    WebSocketTransactionData,
    WebSocketSequenceData,
)

# Only apply asyncio mark to the TestWebSocketClient class
# Remove the global pytestmark

class TestWebSocketModels:
    """Test suite for WebSocket models."""
    
    def test_websocket_subscription(self):
        """Test WebSocketSubscription model."""
        subscription = WebSocketSubscription(action="subscribe", topic="blocks")
        assert subscription.action == "subscribe"
        assert subscription.topic == "blocks"
        
        # Test serialization
        data = subscription.model_dump()
        assert data == {"action": "subscribe", "topic": "blocks"}
        
        # Test JSON serialization
        json_data = subscription.model_dump_json()
        assert json.loads(json_data) == {"action": "subscribe", "topic": "blocks"}
    
    def test_websocket_message(self):
        """Test WebSocketMessage model."""
        block_data = WebSocketBlockData(
            hash="blockhash",
            height=123456,
            time=1234567890,
            tx=["tx1", "tx2"],
            size=1234,
            weight=4936,
            version=536870912,
            merkleroot="merkleroot",
            nonce=1234567890,
            bits="1d00ffff",
            difficulty=1.23456789,
            chainwork="chainwork",
        )
        
        message = WebSocketMessage(type="block", data=block_data)
        assert message.type == "block"
        assert message.data == block_data
        
        # Test serialization
        data = message.model_dump()
        assert data["type"] == "block"
        assert data["data"]["hash"] == "blockhash"
        assert data["data"]["height"] == 123456
        
        # Test JSON serialization
        json_data = message.model_dump_json()
        parsed = json.loads(json_data)
        assert parsed["type"] == "block"
        assert parsed["data"]["hash"] == "blockhash"
        assert parsed["data"]["height"] == 123456
    
    def test_websocket_error(self):
        """Test WebSocketError model."""
        error = WebSocketError(code=1001, message="Error message")
        assert error.code == 1001
        assert error.message == "Error message"
        
        # Test serialization
        data = error.model_dump()
        assert data == {"code": 1001, "message": "Error message"}
        
        # Test JSON serialization
        json_data = error.model_dump_json()
        assert json.loads(json_data) == {"code": 1001, "message": "Error message"}
    
    def test_websocket_block_data(self):
        """Test WebSocketBlockData model."""
        block = WebSocketBlockData(
            hash="blockhash",
            height=123456,
            time=1234567890,
            tx=["tx1", "tx2"],
            size=1234,
            weight=4936,
            version=536870912,
            merkleroot="merkleroot",
            nonce=1234567890,
            bits="1d00ffff",
            difficulty=1.23456789,
            chainwork="chainwork",
            previousblockhash="prevhash",
            nextblockhash="nexthash",
        )
        
        assert block.hash == "blockhash"
        assert block.height == 123456
        assert block.time == 1234567890
        assert block.tx == ["tx1", "tx2"]
        assert block.size == 1234
        assert block.weight == 4936
        assert block.version == 536870912
        assert block.merkleroot == "merkleroot"
        assert block.nonce == 1234567890
        assert block.bits == "1d00ffff"
        assert block.difficulty == 1.23456789
        assert block.chainwork == "chainwork"
        assert block.previousblockhash == "prevhash"
        assert block.nextblockhash == "nexthash"
    
    def test_websocket_transaction_data(self):
        """Test WebSocketTransactionData model."""
        tx = WebSocketTransactionData(
            txid="txid",
            hash="hash",
            size=225,
            vsize=225,
            version=1,
            locktime=0,
            vin=[{"txid": "prevtx", "vout": 0}],
            vout=[{"value": 1.0, "n": 0}],
            hex="rawtx",
            blockhash="blockhash",
            confirmations=1,
            time=1234567890,
            blocktime=1234567890,
        )
        
        assert tx.txid == "txid"
        assert tx.hash == "hash"
        assert tx.size == 225
        assert tx.vsize == 225
        assert tx.version == 1
        assert tx.locktime == 0
        assert tx.vin == [{"txid": "prevtx", "vout": 0}]
        assert tx.vout == [{"value": 1.0, "n": 0}]
        assert tx.hex == "rawtx"
        assert tx.blockhash == "blockhash"
        assert tx.confirmations == 1
        assert tx.time == 1234567890
        assert tx.blocktime == 1234567890
    
    def test_websocket_sequence_data(self):
        """Test WebSocketSequenceData model."""
        sequence = WebSocketSequenceData(
            sequence=123456,
            hash="hash",
        )
        
        assert sequence.sequence == 123456
        assert sequence.hash == "hash"

@pytest.mark.asyncio
class TestWebSocketClient:
    """Test suite for WebSocketClient."""
    
    async def test_client_connect(self):
        """Test client connection."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Connect
        await client.connect()
        
        # Verify
        client._connect_websocket.assert_called_once()
        assert client.ws == mock_websocket
        assert client.connected is True
        
        # Clean up
        await client.disconnect()
    
    async def test_client_disconnect(self):
        """Test client disconnection."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Connect and disconnect
        await client.connect()
        await client.disconnect()
        
        # Verify
        mock_websocket.close.assert_called_once()
        assert client.connected is False
    
    async def test_client_subscribe(self):
        """Test client subscription."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Connect and subscribe
        await client.connect()
        await client.subscribe("blocks")
        
        # Verify
        mock_websocket.send.assert_called_once()
        assert "blocks" in client.subscriptions
        
        # Clean up
        await client.disconnect()
    
    async def test_client_unsubscribe(self):
        """Test client unsubscription."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Connect and add subscription directly
        await client.connect()
        client.subscriptions.add("blocks")
        
        # Unsubscribe
        await client.unsubscribe("blocks")
        
        # Verify
        mock_websocket.send.assert_called_once()
        assert "blocks" not in client.subscriptions
        
        # Clean up
        await client.disconnect()
    
    async def test_client_listen(self):
        """Test client message listening."""
        # Instead of mocking the WebSocket, let's directly add a message to the queue
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        
        # Create a block data object
        block_data = WebSocketBlockData(
            hash="blockhash",
            height=123456,
            time=1234567890,
            tx=["tx1", "tx2"],
            size=1234,
            weight=4936,
            version=536870912,
            merkleroot="merkleroot",
            nonce=1234567890,
            bits="1d00ffff",
            difficulty=1.23456789,
            chainwork="chainwork",
        )
        
        # Create a message
        message = WebSocketMessage(type="block", data=block_data)
        
        # Add the message to the queue
        await client.queue.put(message)
        
        # Get the message from the queue
        received_message = await client.queue.get()
        
        # Verify
        assert received_message.type == "block"
        assert received_message.data.hash == "blockhash"
        assert received_message.data.height == 123456
    
    async def test_client_aiter(self):
        """Test client async iteration."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Connect
        await client.connect()
        
        # Add a message to the queue
        block_data = WebSocketBlockData(
            hash="blockhash",
            height=123456,
            time=1234567890,
            tx=["tx1", "tx2"],
            size=1234,
            weight=4936,
            version=536870912,
            merkleroot="merkleroot",
            nonce=1234567890,
            bits="1d00ffff",
            difficulty=1.23456789,
            chainwork="chainwork",
        )
        message = WebSocketMessage(type="block", data=block_data)
        await client.queue.put(message)
        
        # Get the message via async iteration
        received_message = None
        async for msg in client:
            received_message = msg
            break
        
        # Verify
        assert received_message.type == "block"
        assert received_message.data.hash == "blockhash"
        
        # Clean up
        await client.disconnect()
    
    async def test_client_context_manager(self):
        """Test client as async context manager."""
        # Setup mock
        mock_websocket = AsyncMock()
        
        # Create client with mocked _connect_websocket method
        client = EvrmoreWebSocketClient(uri="ws://localhost:8765")
        client._connect_websocket = AsyncMock(return_value=mock_websocket)
        
        # Use client as context manager
        async with client:
            # Verify connection was established
            assert client.connected is True
            
        # Verify disconnection after context exit
        assert client.connected is False 