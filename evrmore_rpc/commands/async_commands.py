"""
Async command wrappers for the Evrmore RPC client.
This module imports and exports all the async command wrappers.
"""

from typing import Any

from evrmore_rpc.commands.async_blockchain import wrap_blockchain_commands_async
from evrmore_rpc.commands.async_assets import wrap_asset_commands_async

# Import other async command wrappers as they are implemented

async def init_async_commands(client: Any) -> Any:
    """
    Initialize all async command wrappers for the client.
    
    Args:
        client: The EvrmoreAsyncRPCClient instance
        
    Returns:
        The client with all commands initialized
    """
    await wrap_blockchain_commands_async(client)
    await wrap_asset_commands_async(client)
    
    # Initialize other command wrappers as they are implemented
    
    return client 