#!/usr/bin/env python3
"""
Tests for the utility functions in utils.py.
"""

import pytest
import asyncio
import json
from decimal import Decimal
from unittest.mock import MagicMock, patch
from pydantic import BaseModel
from typing import List, Dict, Optional

from evrmore_rpc.utils import (
    format_amount,
    validate_response,
    validate_list_response,
    validate_dict_response,
    format_command_args,
    set_async_context,
    is_async_context,
    AwaitableResult,
    sync_or_async
)

class TestUtils:
    """Tests for utility functions."""
    
    # Define model for testing validation functions
    class ValidationModel(BaseModel):
        """Model for validation function tests."""
        name: str
        value: int
        optional: Optional[str] = None
    
    def test_format_amount(self):
        """Test format_amount function."""
        # Test with integer
        assert format_amount(100) == Decimal('100')
        
        # Test with float
        assert format_amount(100.5) == Decimal('100.5')
        
        # Test with string
        assert format_amount("100.5") == Decimal('100.5')
        
        # Test with scientific notation
        assert format_amount("1e-8") == Decimal('0.00000001')
    
    def test_validate_response(self):
        """Test validate_response function."""
        # Test with dict
        data = {"name": "test", "value": 123}
        result = validate_response(data, self.ValidationModel)
        assert isinstance(result, self.ValidationModel)
        assert result.name == "test"
        assert result.value == 123
        
        # Test with model instance
        model = self.ValidationModel(name="test", value=123)
        result = validate_response(model, self.ValidationModel)
        assert result is model  # Should return the same instance
        
        # Test with invalid data
        with pytest.raises(ValueError):
            validate_response({"name": "test"}, self.ValidationModel)  # Missing required field
    
    def test_validate_list_response(self):
        """Test validate_list_response function."""
        # Test with list of dicts
        data = [
            {"name": "test1", "value": 123},
            {"name": "test2", "value": 456, "optional": "extra"}
        ]
        result = validate_list_response(data, self.ValidationModel)
        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, self.ValidationModel) for item in result)
        assert result[0].name == "test1"
        assert result[1].optional == "extra"
        
        # Test with non-list input
        with pytest.raises(ValueError):
            validate_list_response({"name": "test"}, self.ValidationModel)
    
    def test_validate_dict_response(self):
        """Test validate_dict_response function."""
        # Test with dict of dicts
        data = {
            "item1": {"name": "test1", "value": 123},
            "item2": {"name": "test2", "value": 456, "optional": "extra"}
        }
        result = validate_dict_response(data, self.ValidationModel)
        assert isinstance(result, dict)
        assert len(result) == 2
        assert all(isinstance(item, self.ValidationModel) for item in result.values())
        assert result["item1"].name == "test1"
        assert result["item2"].optional == "extra"
        
        # Test with non-dict input
        with pytest.raises(ValueError):
            validate_dict_response(["test"], self.ValidationModel)
    
    def test_format_command_args(self):
        """Test format_command_args function."""
        # Test with various types
        args = [
            "string",
            123,
            True,
            False,
            None,
            {"key": "value"},
            ["item1", "item2"]
        ]
        result = format_command_args(*args)
        assert result == [
            "string",
            "123",
            "true",
            "false",
            # None should be skipped
            '{"key": "value"}',
            '["item1", "item2"]'
        ]
        
        # Test that JSON is properly formatted
        json_arg = format_command_args({"complex": {"nested": True}})[0]
        # Parse it back to ensure it's valid JSON
        parsed = json.loads(json_arg)
        assert parsed["complex"]["nested"] is True
    
    def test_async_context_detection(self):
        """Test async context detection."""
        # Test setting context explicitly
        set_async_context(True)
        assert is_async_context() is True
        
        set_async_context(False)
        assert is_async_context() is False
        
        # Reset for other tests
        set_async_context(False)
    
    @pytest.mark.asyncio
    async def test_async_context_detection_in_coroutine(self):
        """Test async context detection in a coroutine."""
        # For testing purposes, we'll just verify that we can set and get the async context
        # in a coroutine environment
        
        # Set the context to async
        set_async_context(True)
        assert is_async_context() is True
        
        # Reset for other tests
        set_async_context(False)
    
    def test_awaitable_result_sync(self):
        """Test AwaitableResult in synchronous context."""
        # Create mock objects
        sync_result = "sync_result"
        async_coro = MagicMock()
        async_coro.close = MagicMock()
        cleanup_func = MagicMock()
        
        # Create AwaitableResult
        result = AwaitableResult(sync_result, async_coro, cleanup_func)
        
        # Test attribute access
        assert result.__str__() == "sync_result"
        
        # Test that coroutine was closed
        async_coro.close.assert_called_once()
        
        # Test cleanup on deletion
        result.__del__()
        cleanup_func.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_awaitable_result_async(self):
        """Test AwaitableResult in asynchronous context."""
        # Create mock objects
        sync_result = "sync_result"
        async_result = "async_result"
        
        async def mock_coro():
            return async_result
        
        cleanup_func = MagicMock()
        
        # Create AwaitableResult
        result = AwaitableResult(sync_result, mock_coro(), cleanup_func)
        
        # Test awaiting
        awaited_result = await result
        assert awaited_result == async_result
        
        # Cleanup should not be called in async mode
        cleanup_func.assert_not_called()
    
    def test_sync_or_async_in_sync_context(self):
        """Test sync_or_async in synchronous context."""
        # Create mock functions
        sync_func = MagicMock(return_value="sync_result")
        async_func = MagicMock()
        
        # Create combined function
        with patch('evrmore_rpc.utils.is_async_context', return_value=False):
            combined_func = sync_or_async(sync_func, async_func)
            result = combined_func(1, 2, key="value")
        
        # Check that sync function was called with correct args
        sync_func.assert_called_once_with(1, 2, key="value")
        async_func.assert_not_called()
        assert result == "sync_result"
    
    @pytest.mark.asyncio
    async def test_sync_or_async_in_async_context(self):
        """Test sync_or_async in asynchronous context."""
        # Create mock functions
        sync_func = MagicMock()
        
        async def mock_async_func(*args, **kwargs):
            return "async_result"
        
        # Create combined function
        with patch('evrmore_rpc.utils.is_async_context', return_value=True):
            combined_func = sync_or_async(sync_func, mock_async_func)
            result = await combined_func(1, 2, key="value")
        
        # Check that async function was used
        sync_func.assert_not_called()
        assert result == "async_result" 