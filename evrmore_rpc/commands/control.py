from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class GetInfo(BaseModel):
    """Model for 'getinfo' response"""
    deprecation_warning: Optional[str] = Field(None, alias="deprecation-warning", description="Warning that the getinfo command is deprecated")
    version: int = Field(..., description="The server version")
    protocolversion: int = Field(..., description="The protocol version")
    walletversion: int = Field(..., description="The wallet version")
    balance: Decimal = Field(..., description="The total Evrmore balance of the wallet")
    blocks: int = Field(..., description="The current number of blocks processed in the server")
    timeoffset: int = Field(..., description="The time offset")
    connections: int = Field(..., description="The number of connections")
    proxy: Optional[str] = Field(None, description="The proxy used by the server")
    difficulty: Decimal = Field(..., description="The current difficulty")
    testnet: bool = Field(..., description="If the server is using testnet or not")
    keypoololdest: int = Field(..., description="The timestamp of the oldest pre-generated key in the key pool")
    keypoolsize: int = Field(..., description="How many new keys are pre-generated")
    unlocked_until: Optional[int] = Field(None, description="The timestamp until which the wallet is unlocked, or 0 if locked")
    paytxfee: Decimal = Field(..., description="The transaction fee set in EVR/kB")
    relayfee: Decimal = Field(..., description="Minimum relay fee for transactions in EVR/kB")
    errors: str = Field("", description="Any error messages")

class MemoryInfo(BaseModel):
    """Model for 'getmemoryinfo' response"""
    locked: Dict[str, int] = Field(..., description="Information about locked memory manager")

class RPCInfo(BaseModel):
    """Model for 'getrpcinfo' response"""
    active_commands: List[Dict[str, Union[str, int]]] = Field(..., description="Currently active commands")
    logpath: str = Field(..., description="Path to debug log file")

def wrap_control_commands(client):
    """Add typed control commands to the client."""
    
    def getinfo() -> GetInfo:
        """Get various state info about the server and wallet."""
        result = client.execute_command("getinfo")
        return GetInfo.model_validate(result)
    
    def getmemoryinfo(mode: str = "stats") -> MemoryInfo:
        """Get information about memory usage."""
        result = client.execute_command("getmemoryinfo", mode)
        return MemoryInfo.model_validate(result)
    
    def getrpcinfo() -> RPCInfo:
        """Get runtime details of the RPC server."""
        result = client.execute_command("getrpcinfo")
        return RPCInfo.model_validate(result)
    
    def help(command: Optional[str] = None) -> str:
        """Get help for a command."""
        if command:
            return client.execute_command("help", command)
        return client.execute_command("help")
    
    def stop() -> str:
        """Stop Evrmore server."""
        return client.execute_command("stop")
    
    def uptime() -> int:
        """Get server uptime in seconds."""
        return client.execute_command("uptime")
    
    # Add methods to client
    client.getinfo = getinfo
    client.getmemoryinfo = getmemoryinfo
    client.getrpcinfo = getrpcinfo
    client.help = help
    client.stop = stop
    client.uptime = uptime
    
    return client 