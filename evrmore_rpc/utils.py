"""
Utility functions for evrmore-rpc
"""

from typing import Any, Dict, List, Optional, Type, TypeVar, Union, Callable, Awaitable
from pydantic import BaseModel
from decimal import Decimal
import json
import inspect
import asyncio
from functools import wraps
import threading

T = TypeVar('T', bound=BaseModel)
R = TypeVar('R')  # Return type

# Thread-local storage to track context
_context = threading.local()

def format_amount(value: Union[int, float, str]) -> Decimal:
    """Format a numeric value as a Decimal."""
    return Decimal(str(value))

def validate_response(response: Any, model: Type[T]) -> T:
    """
    Validate a response against a Pydantic model.
    
    Args:
        response: The response to validate
        model: The Pydantic model to validate against
        
    Returns:
        The validated model instance
    """
    if isinstance(response, model):
        return response
    
    return model.model_validate(response)

def validate_list_response(response: Any, model: Type[T]) -> List[T]:
    """
    Validate a list response against a Pydantic model.
    
    Args:
        response: The list response to validate
        model: The Pydantic model to validate against
        
    Returns:
        A list of validated model instances
    """
    if not isinstance(response, list):
        raise ValueError(f"Expected list, got {type(response)}")
    
    return [validate_response(item, model) for item in response]

def validate_dict_response(response: Any, model: Type[T]) -> Dict[str, T]:
    """
    Validate a dictionary response against a Pydantic model.
    
    Args:
        response: The dictionary response to validate
        model: The Pydantic model to validate against
        
    Returns:
        A dictionary of validated model instances
    """
    if not isinstance(response, dict):
        raise ValueError(f"Expected dict, got {type(response)}")
    
    return {key: validate_response(value, model) for key, value in response.items()}

def format_command_args(*args: Any) -> List[str]:
    """Format command arguments for RPC calls."""
    formatted_args = []
    for arg in args:
        if arg is None:
            continue
        if isinstance(arg, bool):
            formatted_args.append("true" if arg else "false")
        elif isinstance(arg, (dict, list)):
            # Convert to JSON string and properly escape quotes
            formatted_args.append(json.dumps(arg))
        else:
            formatted_args.append(str(arg))
    return formatted_args

def set_async_context(is_async: bool) -> None:
    """
    Set the current context as async or sync.
    
    Args:
        is_async: Whether the current context is async
    """
    _context.is_async = is_async

def is_async_context() -> bool:
    """
    Check if the current context is async.
    
    Returns:
        True if the current context is async, False otherwise
    """
    # First, check if we've explicitly set the context
    if hasattr(_context, 'is_async'):
        return _context.is_async
    
    # Otherwise, try to detect based on the current coroutine
    try:
        # If we're in a coroutine, we're in an async context
        asyncio.get_running_loop()
        return True
    except RuntimeError:
        # If we're not in a coroutine, we're in a sync context
        return False

class AwaitableResult:
    """
    A special result type that can be used both with and without await.
    
    This class allows creating objects that work seamlessly in both
    synchronous and asynchronous contexts without requiring explicit
    context managers or cleanup.
    """
    
    def __init__(self, sync_result: Any, async_coro: Awaitable[Any], cleanup_func=None):
        """
        Initialize the awaitable result.
        
        Args:
            sync_result: The result to return in synchronous context
            async_coro: The coroutine to await in asynchronous context
            cleanup_func: Optional function to call for cleanup when used synchronously
        """
        self._sync_result = sync_result
        self._async_coro = async_coro
        self._cleanup_func = cleanup_func
        self._used = False
        
    def __await__(self):
        """
        Make the object awaitable.
        This is called when the object is used with 'await'.
        """
        self._used = True
        return self._async_coro.__await__()
    
    def __getattr__(self, name):
        """
        Forward attribute access to the sync result.
        This allows using the object directly as if it were the sync result.
        """
        # Mark as used in sync mode
        if not self._used:
            self._used = True
            # Cancel the coroutine to prevent warnings
            if hasattr(self._async_coro, 'close'):
                self._async_coro.close()
            elif hasattr(self._async_coro, 'cancel'):
                self._async_coro.cancel()
        
        return getattr(self._sync_result, name)
    
    def __getitem__(self, key):
        """
        Forward item access to the sync result.
        This allows using the object with dictionary-like syntax.
        """
        # Mark as used in sync mode
        if not self._used:
            self._used = True
            # Cancel the coroutine to prevent warnings
            if hasattr(self._async_coro, 'close'):
                self._async_coro.close()
            elif hasattr(self._async_coro, 'cancel'):
                self._async_coro.cancel()
        
        return self._sync_result[key]
    
    def __str__(self):
        """Return string representation of the sync result."""
        # Mark as used in sync mode
        if not self._used:
            self._used = True
            # Cancel the coroutine to prevent warnings
            if hasattr(self._async_coro, 'close'):
                self._async_coro.close()
            elif hasattr(self._async_coro, 'cancel'):
                self._async_coro.cancel()
        
        return str(self._sync_result)
    
    def __repr__(self):
        """Return representation of the sync result."""
        # Mark as used in sync mode
        if not self._used:
            self._used = True
            # Cancel the coroutine to prevent warnings
            if hasattr(self._async_coro, 'close'):
                self._async_coro.close()
            elif hasattr(self._async_coro, 'cancel'):
                self._async_coro.cancel()
        
        return repr(self._sync_result)
    
    def __del__(self):
        """Clean up resources when the object is garbage collected."""
        # If we have a cleanup function and the object was used in sync mode
        if self._cleanup_func and self._used:
            try:
                self._cleanup_func()
            except Exception:
                pass
        
        # Cancel the coroutine if it wasn't awaited
        if not self._used:
            if hasattr(self._async_coro, 'close'):
                self._async_coro.close()
            elif hasattr(self._async_coro, 'cancel'):
                self._async_coro.cancel()

def sync_or_async(sync_func: Callable[..., R], async_func: Callable[..., Awaitable[R]]) -> Callable[..., Union[R, Awaitable[R]]]:
    """
    Create a function that can be used in both sync and async contexts.
    
    Args:
        sync_func: The synchronous implementation
        async_func: The asynchronous implementation
        
    Returns:
        A function that will use the appropriate implementation based on context
    """
    @wraps(async_func)
    def wrapper(*args: Any, **kwargs: Any) -> Union[R, Awaitable[R]]:
        # Check if we're in an async context
        if is_async_context():
            return async_func(*args, **kwargs)
        else:
            return sync_func(*args, **kwargs)
    
    return wrapper 