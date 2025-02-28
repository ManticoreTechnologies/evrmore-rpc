from typing import Dict, List, Optional, Union
from decimal import Decimal

from evrmore_rpc.commands.assets import (
    AssetData,
    AssetBalance,
    IssueAssetResult,
)

async def wrap_asset_commands_async(client):
    """Add typed async asset commands to the client."""
    
    async def getassetdata(asset_name: str) -> AssetData:
        """Get data about an asset."""
        result = await client.execute_command("getassetdata", asset_name)
        return AssetData.model_validate(result)
    
    async def listassets(
        asset: Optional[str] = None,
        verbose: bool = False,
        count: int = 50000,
        start: int = 0
    ) -> Dict[str, AssetData]:
        """List all assets."""
        args = []
        if asset is not None:
            args.append(asset)
        if verbose:
            args.append(verbose)
            if count != 50000 or start != 0:
                args.extend([count, start])
        result = await client.execute_command("listassets", *args)
        
        # Handle case where result is a list instead of a dict
        if isinstance(result, list):
            return {asset: {} for asset in result}
            
        if verbose:
            return {name: AssetData.model_validate(data) for name, data in result.items()}
        return result
    
    async def listmyassets(
        asset: Optional[str] = None,
        verbose: bool = False,
        count: int = 50000,
        start: int = 0,
        confs: int = 0
    ) -> Dict[str, Union[Decimal, AssetData]]:
        """List my asset balances."""
        args = []
        if asset is not None:
            args.append(asset)
        if verbose:
            args.append(verbose)
            if count != 50000 or start != 0 or confs != 0:
                args.extend([count, start, confs])
        result = await client.execute_command("listmyassets", *args)
        if verbose:
            return {name: AssetData.model_validate(data) for name, data in result.items()}
        return {name: Decimal(str(balance)) for name, balance in result.items()}
    
    async def issue(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: Optional[str] = None,
        change_address: Optional[str] = None,
        units: int = 0,
        reissuable: bool = True,
        has_ipfs: bool = False,
        ipfs_hash: Optional[str] = None
    ) -> str:
        """Issue a new asset."""
        result = await client.execute_command(
            "issue",
            asset_name,
            qty,
            to_address,
            change_address,
            units,
            reissuable,
            has_ipfs,
            ipfs_hash
        )
        return result
    
    async def transfer(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        message: Optional[str] = None,
        expire_time: Optional[int] = None,
        change_address: Optional[str] = None,
        asset_change_address: Optional[str] = None
    ) -> str:
        """Transfer an asset."""
        result = await client.execute_command(
            "transfer",
            asset_name,
            qty,
            to_address,
            message,
            expire_time,
            change_address,
            asset_change_address
        )
        return result
    
    async def reissue(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        change_address: Optional[str] = None,
        reissuable: Optional[bool] = None,
        new_units: Optional[int] = None,
        new_ipfs: Optional[str] = None
    ) -> str:
        """Reissue an asset."""
        result = await client.execute_command(
            "reissue",
            asset_name,
            qty,
            to_address,
            change_address,
            reissuable,
            new_units,
            new_ipfs
        )
        return result
    
    # Add methods to client
    client.getassetdata = getassetdata
    client.listassets = listassets
    client.listmyassets = listmyassets
    client.issue = issue
    client.transfer = transfer
    client.reissue = reissue
    
    return client 