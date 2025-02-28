from typing import Any, Dict, List, Optional, Union
from pathlib import Path
import subprocess
import json
from rich.console import Console
from rich.table import Table
from pydantic import BaseModel

from evrmore_rpc.commands.blockchain import wrap_blockchain_commands
from evrmore_rpc.commands.assets import wrap_asset_commands
from evrmore_rpc.commands.addressindex import wrap_addressindex_commands
from evrmore_rpc.commands.control import wrap_control_commands
from evrmore_rpc.commands.generating import wrap_generating_commands
from evrmore_rpc.commands.messages import wrap_message_commands
from evrmore_rpc.commands.mining import wrap_mining_commands
from evrmore_rpc.commands.network import wrap_network_commands
from evrmore_rpc.commands.rawtransactions import wrap_rawtransaction_commands
from evrmore_rpc.commands.restricted import wrap_restricted_commands
from evrmore_rpc.commands.rewards import wrap_reward_commands
from evrmore_rpc.commands.util import wrap_util_commands
from evrmore_rpc.utils import format_command_args

console = Console()

class EvrmoreRPCError(Exception):
    """Custom exception for Evrmore RPC errors."""
    pass

class EvrmoreRPCClient:
    """
    A typed Python wrapper for evrmore-cli commands.
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
        
        # Add typed command wrappers
        wrap_blockchain_commands(self)
        wrap_asset_commands(self)
        wrap_addressindex_commands(self)
        wrap_control_commands(self)
        wrap_generating_commands(self)
        wrap_message_commands(self)
        wrap_mining_commands(self)
        wrap_network_commands(self)
        wrap_rawtransaction_commands(self)
        wrap_restricted_commands(self)
        wrap_reward_commands(self)
        wrap_util_commands(self)
        
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
        
    def execute_command(self, command: str, *args: Any) -> Any:
        """Execute an evrmore-cli command and return the result."""
        cmd = self._build_command(command, *args)
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            if result.stdout.strip():
                try:
                    return json.loads(result.stdout)
                except json.JSONDecodeError:
                    return result.stdout.strip()
            return None
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr.strip() or e.stdout.strip()
            raise EvrmoreRPCError(f"Command failed: {error_msg}")
            
    def __getattr__(self, name: str):
        """
        Dynamic method handler that allows calling RPC methods as Python methods.
        Example: client.getinfo() will execute 'evrmore-cli getinfo'
        """
        def method(*args: Any) -> Any:
            return self.execute_command(name, *args)
        return method 