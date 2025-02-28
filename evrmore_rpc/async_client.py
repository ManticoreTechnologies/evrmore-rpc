from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import asyncio
import json
from rich.console import Console
from rich.table import Table
from pydantic import BaseModel

from evrmore_rpc.client import EvrmoreRPCError
from evrmore_rpc.utils import format_command_args
from evrmore_rpc.commands.async_commands import init_async_commands

console = Console()

class EvrmoreAsyncRPCClient:
    """
    An async typed Python wrapper for evrmore-cli commands.
    Provides a clean interface with autocomplete support for all evrmore-cli commands.
    """
    
    def __init__(self, 
                 datadir: Optional[Path] = None,
                 rpcuser: Optional[str] = None,
                 rpcpassword: Optional[str] = None,
                 rpcport: Optional[int] = None,
                 testnet: bool = False):
        self.datadir = datadir
        self.rpcuser = rpcuser
        self.rpcpassword = rpcpassword
        self.rpcport = rpcport
        self.testnet = testnet
        self._initialized = False
        
    async def initialize(self):
        """Initialize command wrappers."""
        if not self._initialized:
            await init_async_commands(self)
            self._initialized = True
        return self
    
    async def __aenter__(self):
        """Async context manager entry."""
        return await self.initialize()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        pass
        
    def _build_command(self, command: str, *args: Any) -> List[str]:
        """Build the evrmore-cli command with proper arguments."""
        cmd = ["evrmore-cli"]
        
        if self.datadir:
            cmd.extend(["-datadir=" + str(self.datadir)])
        if self.rpcuser:
            cmd.extend(["-rpcuser=" + self.rpcuser])
        if self.rpcpassword:
            cmd.extend(["-rpcpassword=" + self.rpcpassword])
        if self.rpcport:
            cmd.extend(["-rpcport=" + str(self.rpcport)])
        if self.testnet:
            cmd.append("-testnet")
            
        cmd.append(command)
        cmd.extend(format_command_args(*args))
        return cmd
        
    async def execute_command(self, command: str, *args: Any) -> Any:
        """Execute an evrmore-cli command asynchronously and return the result."""
        cmd = self._build_command(command, *args)
        try:
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout_bytes, stderr_bytes = await proc.communicate()
            
            # Decode the bytes to string
            stdout = stdout_bytes.decode('utf-8') if stdout_bytes else ""
            stderr = stderr_bytes.decode('utf-8') if stderr_bytes else ""
            
            if proc.returncode != 0:
                error_msg = stderr.strip() or stdout.strip()
                raise EvrmoreRPCError(f"Command failed: {error_msg}")
                
            if stdout.strip():
                try:
                    return json.loads(stdout)
                except json.JSONDecodeError:
                    return stdout.strip()
            return None
        except Exception as e:
            if isinstance(e, EvrmoreRPCError):
                raise
            raise EvrmoreRPCError(f"Command execution failed: {str(e)}")
            
    def __getattr__(self, name: str):
        """
        Dynamic method handler that allows calling RPC methods as Python methods.
        Example: await client.getinfo() will execute 'evrmore-cli getinfo'
        """
        async def method(*args: Any) -> Any:
            if not self._initialized:
                await self.initialize()
            return await self.execute_command(name, *args)
        return method 