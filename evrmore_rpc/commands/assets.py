from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class AssetData(BaseModel):
    """Model for 'getassetdata' response"""
    name: str = Field(..., description="The asset name")
    amount: Decimal = Field(..., description="The amount of this asset")
    units: int = Field(..., description="The units of this asset")
    reissuable: bool = Field(..., description="If this asset can be reissued")
    has_ipfs: bool = Field(..., description="If this asset has an IPFS hash")
    ipfs_hash: Optional[str] = Field(None, description="The IPFS hash of this asset")
    txid: Optional[str] = Field(None, description="The transaction ID of the asset creation")
    verifier_string: Optional[str] = Field(None, description="The verifier string for restricted assets")
    
class AssetBalance(BaseModel):
    """Model for asset balance entries"""
    name: str = Field(..., description="The asset name")
    balance: Decimal = Field(..., description="The asset balance")
    units: int = Field(..., description="The units of this asset")

class IssueAssetResult(BaseModel):
    """Model for 'issue' command response"""
    txid: str = Field(..., description="The transaction id")
    
def wrap_asset_commands(client):
    """Add typed asset commands to the client."""
    
    def getassetdata(asset_name: str) -> AssetData:
        """Get data about an asset."""
        result = client.execute_command("getassetdata", asset_name)
        return AssetData.model_validate(result)
    
    def listassets(
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
        result = client.execute_command("listassets", *args)
        if verbose:
            return {name: AssetData.model_validate(data) for name, data in result.items()}
        return result
    
    def listmyassets(
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
        result = client.execute_command("listmyassets", *args)
        if verbose:
            return {name: AssetData.model_validate(data) for name, data in result.items()}
        return {name: Decimal(str(balance)) for name, balance in result.items()}
    
    def issue(
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
        result = client.execute_command(
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
    
    def transfer(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        message: Optional[str] = None,
        expire_time: Optional[int] = None,
        change_address: Optional[str] = None,
        asset_change_address: Optional[str] = None
    ) -> str:
        """Transfer an asset."""
        result = client.execute_command(
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
    
    def reissue(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        change_address: Optional[str] = None,
        reissuable: Optional[bool] = None,
        new_units: Optional[int] = None,
        new_ipfs: Optional[str] = None
    ) -> str:
        """Reissue an asset."""
        result = client.execute_command(
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