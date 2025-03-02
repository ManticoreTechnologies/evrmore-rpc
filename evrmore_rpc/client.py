#!/usr/bin/env python3
"""
evrmore-rpc: A streamlined, high-performance async Python wrapper for Evrmore blockchain
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Any, Dict, List, Optional, Union, Tuple, TypeVar, Type, cast, Callable, overload
import os
import json
import time
import asyncio
import statistics
from pathlib import Path
from urllib.parse import urlparse
import base64
from decimal import Decimal
import aiohttp
import requests
from pydantic import BaseModel, Field
from functools import wraps
import inspect

# Import models
from evrmore_rpc.models import (
    BlockchainInfo,
    Block,
    AssetInfo,
    NetworkInfo
)

# Import utilities
from evrmore_rpc.utils import sync_or_async, is_async_context, AwaitableResult

# Default Evrmore data directory
DEFAULT_DATADIR = Path.home() / ".evrmore"

# Type variables for better type hints
T = TypeVar('T')  # Generic type for client
R = TypeVar('R')  # Return type

class EvrmoreRPCError(Exception):
    """Exception raised when an RPC command fails."""
    pass

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

class EvrmoreConfig:
    """
    Parser for Evrmore configuration file (evrmore.conf).
    Automatically reads and parses the configuration file.
    """
    
    def __init__(self, datadir: Optional[Union[str, Path]] = None, testnet: bool = False):
        """
        Initialize the configuration parser.
        
        Args:
            datadir: Path to Evrmore data directory (defaults to ~/.evrmore)
            testnet: Whether to use testnet
        """
        self.datadir = Path(datadir) if datadir else DEFAULT_DATADIR
        self.testnet = testnet
        self.config_data: Dict[str, Any] = {}
        
        # Load configuration
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from evrmore.conf."""
        config_path = self._get_config_path()
        
        if not config_path.exists():
            return
        
        with open(config_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                
                # Handle key=value pairs
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Convert value to appropriate type
                    if value.lower() in ('true', '1'):
                        value = True
                    elif value.lower() in ('false', '0'):
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    
                    self.config_data[key] = value
                else:
                    # Handle flags (e.g., testnet)
                    self.config_data[line.strip()] = True
    
    def _get_config_path(self) -> Path:
        """Get the path to the configuration file."""
        if self.testnet:
            return self.datadir / "testnet3" / "evrmore.conf"
        return self.datadir / "evrmore.conf"
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value."""
        return self.config_data.get(key, default)
    
    def get_rpc_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """Get RPC credentials from configuration."""
        return self.get('rpcuser'), self.get('rpcpassword')
    
    def get_rpc_connection_info(self) -> Tuple[str, int]:
        """Get RPC connection information from configuration."""
        host = self.get('rpcconnect', '127.0.0.1')
        
        # Determine port based on network
        if self.testnet:
            port = self.get('rpcport', 18819)
        else:
            port = self.get('rpcport', 8819)
            
        return host, port
    
    def get_zmq_endpoints(self) -> Dict[str, str]:
        """Get ZMQ endpoints from configuration."""
        endpoints = {}
        for key, value in self.config_data.items():
            if key.startswith('zmq'):
                notification_type = key[3:]
                endpoints[notification_type] = value
        return endpoints
    
    def get_zmq_hwm(self) -> Dict[str, int]:
        """Get ZMQ high water mark settings from configuration."""
        hwm = {}
        for key, value in self.config_data.items():
            if key.startswith('zmqhwm'):
                notification_type = key[6:]
                hwm[notification_type] = int(value)
        return hwm
    
    def get_p2p_connection_info(self) -> Tuple[str, int]:
        """Get P2P connection information from configuration."""
        host = self.get('bind', '127.0.0.1')
        port = self.get('port', 8818 if not self.testnet else 18818)
        return host, port
    
    def is_server_enabled(self) -> bool:
        """Check if server is enabled."""
        return self.get('server', False)
    
    def is_index_enabled(self, index_name: str) -> bool:
        """Check if a specific index is enabled."""
        return self.get(index_name, False)
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration values."""
        return self.config_data.copy()
    
    def __getitem__(self, key: str) -> Any:
        """Get a configuration value using dictionary syntax."""
        return self.config_data[key]
    
    def __contains__(self, key: str) -> bool:
        """Check if a configuration key exists."""
        return key in self.config_data

class EvrmoreClient:
    """
    A polymorphic high-performance JSON-RPC client for Evrmore.
    Supports both synchronous and asynchronous usage with the same API.
    """
    
    def __init__(self, 
                 url: Optional[str] = None,
                 datadir: Optional[Union[str, Path]] = None,
                 rpcuser: Optional[str] = None,
                 rpcpassword: Optional[str] = None,
                 rpcport: Optional[int] = None,
                 testnet: bool = False,
                 timeout: int = 30,
                 async_mode: Optional[bool] = None):
        """
        Initialize the RPC client.
        
        Args:
            url: The URL of the Evrmore RPC server (e.g., http://localhost:8819/)
            datadir: Path to Evrmore data directory (defaults to ~/.evrmore)
            rpcuser: RPC username (if not provided, will be read from config)
            rpcpassword: RPC password (if not provided, will be read from config)
            rpcport: RPC port number (if not provided, will be read from config)
            testnet: Whether to use testnet
            timeout: Request timeout in seconds
            async_mode: Force async mode (True) or sync mode (False). If None, auto-detect based on context.
        """
        self.timeout = timeout
        self.testnet = testnet
        self.datadir = Path(datadir) if datadir else DEFAULT_DATADIR
        
        # Determine async mode
        self._async_mode = async_mode
        if self._async_mode is None:
            # Auto-detect based on whether we're in an async context
            self._async_mode = is_async_context()
        
        # Load configuration from evrmore.conf if available
        self.config = EvrmoreConfig(datadir=self.datadir, testnet=self.testnet)
        
        # If URL is provided, parse it for credentials
        if url:
            parsed_url = urlparse(url)
            self.host = parsed_url.hostname or "127.0.0.1"
            self.port = parsed_url.port or (8819 if not testnet else 18819)
            self.rpcuser = parsed_url.username or rpcuser
            self.rpcpassword = parsed_url.password or rpcpassword
            self.url = f"http://{self.host}:{self.port}"
        else:
            # Get connection info from config
            self.host, self.port = self.config.get_rpc_connection_info()
            if rpcport:
                self.port = rpcport  # Override with explicit port if provided
            self.url = f"http://{self.host}:{self.port}"
            
            # Get credentials from config if not provided
            if not rpcuser or not rpcpassword:
                config_user, config_pass = self.config.get_rpc_credentials()
                self.rpcuser = rpcuser or config_user
                self.rpcpassword = rpcpassword or config_pass
        
        # Initialize sessions to None, will be created when needed
        self.async_session: Optional[aiohttp.ClientSession] = None
        self.sync_session: Optional[requests.Session] = None
        
        self.headers = {
            'Content-Type': 'application/json',
        }
        
        # Add authentication if credentials are provided
        if self.rpcuser and self.rpcpassword:
            auth = f"{self.rpcuser}:{self.rpcpassword}"
            auth_header = base64.b64encode(auth.encode()).decode()
            self.headers['Authorization'] = f"Basic {auth_header}"
    
    def _prepare_payload(self, command: str, *args: Any) -> Dict[str, Any]:
        """
        Prepare the JSON-RPC payload for a command.
        
        Args:
            command: The RPC command to execute
            args: Arguments for the command
            
        Returns:
            The JSON-RPC payload
        """
        payload = {
            "jsonrpc": "1.0",
            "id": str(time.time()),
            "method": command,
            "params": args
        }
        return payload
    
    def _handle_response(self, response_data: Dict[str, Any]) -> Any:
        """
        Handle the JSON-RPC response.
        
        Args:
            response_data: The JSON-RPC response data
            
        Returns:
            The result of the RPC command
            
        Raises:
            EvrmoreRPCError: If the RPC command fails
        """
        if "error" in response_data and response_data["error"] is not None:
            error = response_data["error"]
            if isinstance(error, dict):
                message = error.get("message", str(error))
                code = error.get("code", -1)
                raise EvrmoreRPCError(f"RPC error ({code}): {message}")
            else:
                raise EvrmoreRPCError(f"RPC error: {error}")
        
        if "result" not in response_data:
            raise EvrmoreRPCError("No result in response")
        
        return response_data["result"]
    
    # Synchronous methods
    
    def initialize_sync(self) -> None:
        """Initialize the synchronous client session."""
        if self.sync_session is None:
            self.sync_session = requests.Session()
            self.sync_session.headers.update(self.headers)
    
    def __enter__(self) -> 'EvrmoreClient':
        """Enter the synchronous context manager."""
        self.initialize_sync()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the synchronous context manager."""
        if self.sync_session:
            self.sync_session.close()
    
    def execute_command_sync(self, command: str, *args: Any) -> Any:
        """
        Execute an RPC command synchronously.
        
        Args:
            command: The RPC command to execute
            args: Arguments for the command
            
        Returns:
            The result of the RPC command
            
        Raises:
            EvrmoreRPCError: If the RPC command fails
        """
        if self.sync_session is None:
            self.initialize_sync()
        
        if self.sync_session is None:
            raise EvrmoreRPCError("Session not initialized")
        
        payload = self._prepare_payload(command, *args)
        
        try:
            response = self.sync_session.post(
                self.url,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                raise EvrmoreRPCError(f"HTTP error {response.status_code}: {response.text}")
            
            response_data = response.json()
            return self._handle_response(response_data)
        except requests.RequestException as e:
            raise EvrmoreRPCError(f"Request failed: {str(e)}")
        except json.JSONDecodeError:
            raise EvrmoreRPCError("Invalid JSON response")
    
    # Asynchronous methods
    
    async def initialize_async(self) -> None:
        """Initialize the asynchronous client session."""
        if self.async_session is None or self.async_session.closed:
            self.async_session = aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
    
    async def __aenter__(self) -> 'EvrmoreClient':
        """Enter the async context manager."""
        await self.initialize_async()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit the async context manager."""
        if self.async_session and not self.async_session.closed:
            await self.async_session.close()
    
    def __del__(self):
        """
        Destructor to ensure resources are properly cleaned up.
        This will attempt to close any open sessions when the client is garbage collected.
        """
        # Close the sync session if it exists
        if hasattr(self, 'sync_session') and self.sync_session is not None:
            try:
                self.sync_session.close()
                self.sync_session = None
            except Exception:
                pass
        
        # For async session, we can't await in __del__, so we need to use a different approach
        if hasattr(self, 'async_session') and self.async_session is not None and not self.async_session.closed:
            # Create a warning about unclosed session
            import warnings
            warnings.warn(
                "EvrmoreClient was garbage collected with an unclosed async session. "
                "Please use 'async with' or explicitly call 'await client.close()' to avoid this warning.",
                ResourceWarning,
                stacklevel=2
            )
            
            # Try to close the session without awaiting
            # This is not ideal but better than nothing
            if hasattr(self.async_session, '_connector'):
                connector = getattr(self.async_session, '_connector', None)
                if connector and not connector.closed:
                    connector.close()
            
            # Set to None to avoid double cleanup
            self.async_session = None
    
    async def close(self):
        """
        Explicitly close the client sessions.
        This method should be called when not using context managers.
        
        In async contexts, use:
            await client.close()
            
        In sync contexts, use:
            client.close_sync()
        """
        # Close async session if it exists
        if self.async_session and not self.async_session.closed:
            await self.async_session.close()
            self.async_session = None
        
        # Also close sync session if it exists
        if self.sync_session:
            self.sync_session.close()
            self.sync_session = None
    
    def close_sync(self):
        """
        Explicitly close the synchronous session.
        This method should be called when not using context managers in sync code.
        """
        if self.sync_session:
            self.sync_session.close()
            self.sync_session = None
    
    async def execute_command_async(self, command: str, *args: Any) -> Any:
        """
        Execute an RPC command asynchronously.
        
        Args:
            command: The RPC command to execute
            args: Arguments for the command
            
        Returns:
            The result of the RPC command
            
        Raises:
            EvrmoreRPCError: If the RPC command fails
        """
        if self.async_session is None or self.async_session.closed:
            await self.initialize_async()
        
        if self.async_session is None:
            raise EvrmoreRPCError("Session not initialized")
        
        payload = self._prepare_payload(command, *args)
        
        try:
            async with self.async_session.post(
                self.url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                if response.status != 200:
                    text = await response.text()
                    raise EvrmoreRPCError(f"HTTP error {response.status}: {text}")
                
                response_data = await response.json()
                return self._handle_response(response_data)
        except aiohttp.ClientError as e:
            raise EvrmoreRPCError(f"Request failed: {str(e)}")
        except asyncio.TimeoutError:
            raise EvrmoreRPCError(f"Request timed out after {self.timeout} seconds")
        except json.JSONDecodeError:
            raise EvrmoreRPCError("Invalid JSON response")
    
    # Polymorphic methods
    
    def initialize(self) -> Union[None, asyncio.coroutine]:
        """Initialize the client session (sync or async)."""
        if self._async_mode:
            return self.initialize_async()
        else:
            return self.initialize_sync()
    
    def execute_command(self, command: str, *args: Any) -> Any:
        """
        Execute an RPC command, automatically detecting whether to use sync or async.
        
        This method will use the sync_or_async utility to determine whether to execute
        the command synchronously or asynchronously based on the calling context.
        
        Args:
            command: The RPC command to execute
            *args: Arguments to pass to the command
            
        Returns:
            The result of the command, or a coroutine if in async context
        """
        from evrmore_rpc.utils import AwaitableResult
        
        # If _async_mode is explicitly set, use that
        if self._async_mode is not None:
            if self._async_mode:
                return self.execute_command_async(command, *args)
            else:
                return self.execute_command_sync(command, *args)
        
        # Otherwise, create a session for sync execution
        session = self._get_or_create_sync_session()
        
        # Execute the sync method immediately
        sync_result = self.execute_command_sync(command, *args)
        
        # Create a coroutine for the async method
        async_coro = self.execute_command_async(command, *args)
        
        # Return an AwaitableResult that works in both contexts
        return AwaitableResult(
            sync_result, 
            async_coro,
            # No cleanup needed here as we manage sessions separately
            cleanup_func=None
        )
    
    # Add this new method for session management
    def _get_or_create_sync_session(self):
        """Get or create a synchronous session."""
        if self.sync_session is None:
            self.initialize_sync()
        return self.sync_session
    
    async def _get_or_create_async_session(self):
        """Get or create an asynchronous session."""
        if self.async_session is None or self.async_session.closed:
            await self.initialize_async()
        return self.async_session
    
    def _cleanup_sync_session(self):
        """Clean up the synchronous session."""
        if self.sync_session is not None:
            try:
                self.sync_session.close()
                self.sync_session = None
            except Exception:
                pass
    
    # Update the __getattr__ method to use the improved AwaitableResult
    def __getattr__(self, name: str) -> Callable:
        """
        Dynamically create methods for RPC commands.
        
        This allows calling any RPC command as a method on the client.
        For example: client.getblockchaininfo() will call the 'getblockchaininfo' RPC command.
        
        Args:
            name: The name of the RPC command
            
        Returns:
            A callable that will execute the RPC command
        """
        from evrmore_rpc.utils import AwaitableResult
        
        # Define the method factory
        def method_factory(*args: Any) -> Any:
            # If async_mode is explicitly set, use that mode
            if self._async_mode is not None:
                if self._async_mode:
                    return self.execute_command_async(name, *args)
                else:
                    return self.execute_command_sync(name, *args)
            
            # Otherwise, create a session for sync execution
            session = self._get_or_create_sync_session()
            
            # Execute the sync method immediately
            sync_result = self.execute_command_sync(name, *args)
            
            # Create a coroutine for the async method
            async_coro = self.execute_command_async(name, *args)
            
            # Return an AwaitableResult that works in both contexts
            return AwaitableResult(
                sync_result, 
                async_coro,
                # No cleanup needed here as we manage sessions separately
                cleanup_func=None
            )
        
        return method_factory
    
    # Stress testing
    
    def stress_test_sync(self, num_calls: int = 100, command: str = "getblockcount", concurrency: int = 10) -> Dict[str, Any]:
        """
        Run a synchronous stress test with the specified command.
        
        Args:
            num_calls: Number of calls to make
            command: RPC command to execute
            concurrency: Number of concurrent calls (simulated with threads)
            
        Returns:
            Dictionary with test results
        """
        import threading
        from queue import Queue
        
        if self.sync_session is None:
            self.initialize_sync()
        
        start_time = time.time()
        results = []
        result_queue = Queue()
        last_result = None
        
        def worker():
            while True:
                try:
                    call_start = time.time()
                    result = self.execute_command_sync(command)
                    call_end = time.time()
                    result_queue.put(((call_end - call_start) * 1000, result))  # Convert to ms
                except Exception as e:
                    print(f"Error during stress test: {e}")
                    result_queue.put((float('inf'), None))
                break
        
        # Process in batches to control concurrency
        for i in range(0, num_calls, concurrency):
            batch_size = min(concurrency, num_calls - i)
            threads = []
            
            for _ in range(batch_size):
                thread = threading.Thread(target=worker)
                thread.start()
                threads.append(thread)
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Collect results
            for _ in range(batch_size):
                time_taken, result = result_queue.get()
                results.append(time_taken)
                last_result = result
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Filter out failed calls (infinity)
        valid_results = [r for r in results if r != float('inf')]
        
        if not valid_results:
            raise EvrmoreRPCError("All stress test calls failed")
        
        return {
            "total_time": total_time,
            "requests_per_second": num_calls / total_time,
            "avg_time": sum(valid_results) / len(valid_results),
            "min_time": min(valid_results),
            "max_time": max(valid_results),
            "median_time": statistics.median(valid_results),
            "num_calls": num_calls,
            "concurrency": concurrency,
            "last_result": last_result
        }
    
    async def stress_test_async(self, num_calls: int = 100, command: str = "getblockcount", concurrency: int = 10) -> Dict[str, Any]:
        """
        Run an asynchronous stress test with the specified command.
        
        Args:
            num_calls: Number of calls to make
            command: RPC command to execute
            concurrency: Number of concurrent calls
            
        Returns:
            Dictionary with test results
        """
        if self.async_session is None or self.async_session.closed:
            await self.initialize_async()
        
        start_time = time.time()
        results = []
        tasks = set()
        
        async def make_call():
            call_start = time.time()
            try:
                result = await self.execute_command_async(command)
                call_end = time.time()
                results.append((call_end - call_start) * 1000)  # Convert to ms
                return result
            except Exception as e:
                print(f"Error during stress test: {e}")
                results.append(float('inf'))
                return None
        
        # Process in batches to control concurrency
        last_result = None
        for i in range(0, num_calls, concurrency):
            batch_size = min(concurrency, num_calls - i)
            batch_tasks = set()
            
            for _ in range(batch_size):
                task = asyncio.create_task(make_call())
                batch_tasks.add(task)
                tasks.add(task)
            
            # Wait for the current batch to complete
            batch_results = await asyncio.gather(*batch_tasks)
            if batch_results:
                last_result = batch_results[-1]
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Filter out failed calls (infinity)
        valid_results = [r for r in results if r != float('inf')]
        
        if not valid_results:
            raise EvrmoreRPCError("All stress test calls failed")
        
        return {
            "total_time": total_time,
            "requests_per_second": num_calls / total_time,
            "avg_time": sum(valid_results) / len(valid_results),
            "min_time": min(valid_results),
            "max_time": max(valid_results),
            "median_time": statistics.median(valid_results),
            "num_calls": num_calls,
            "concurrency": concurrency,
            "last_result": last_result
        }
    
    def stress_test(self, num_calls: int = 100, command: str = "getblockcount", concurrency: int = 10) -> Dict[str, Any]:
        """
        Run a stress test with the specified command (sync or async).
        
        Args:
            num_calls: Number of calls to make
            command: RPC command to execute
            concurrency: Number of concurrent calls
            
        Returns:
            Dictionary with test results
        """
        # If async_mode is explicitly set, use that
        if self._async_mode is not None:
            if self._async_mode:
                return self.stress_test_async(num_calls, command, concurrency)
            else:
                return self.stress_test_sync(num_calls, command, concurrency)
        
        # Otherwise, use the sync_or_async utility to automatically choose the right implementation
        return sync_or_async(
            self.stress_test_sync,
            self.stress_test_async
        )(num_calls, command, concurrency)
    
    def force_sync(self):
        """
        Force the client to use synchronous mode.
        This is useful when using the client in a thread from an async context.
        
        Returns:
            self: The client instance with sync mode forced
        """
        self._async_mode = False
        return self
    
    def force_async(self):
        """
        Force the client to use asynchronous mode.
        This is useful when you want to ensure async mode is used.
        
        Returns:
            self: The client instance with async mode forced
        """
        self._async_mode = True
        return self
    
    def reset(self):
        """
        Reset the client's state.
        This is useful when switching between sync and async modes.
        
        Returns:
            self: The client instance with reset state
        """
        self._async_mode = None
        return self 