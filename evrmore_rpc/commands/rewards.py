from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class SnapshotRequest(BaseModel):
    """Model for snapshot request information"""
    asset_name: str = Field(..., description="The name of the asset")
    block_height: int = Field(..., description="The block height of the snapshot")
    status: str = Field(..., description="The status of the snapshot request")

class DistributionStatus(BaseModel):
    """Model for distribution status information"""
    asset_name: str = Field(..., description="The name of the asset")
    snapshot_height: int = Field(..., description="The block height of the snapshot")
    distribution_asset_name: str = Field(..., description="The name of the distribution asset")
    gross_distribution_amount: Decimal = Field(..., description="The total amount to distribute")
    status: str = Field(..., description="The status of the distribution")
    processing_ids: List[str] = Field(default_factory=list, description="List of processing transaction IDs")
    error: Optional[str] = Field(None, description="Error message if distribution failed")

def wrap_reward_commands(client):
    """Add typed reward commands to the client."""
    
    def cancelsnapshotrequest(asset_name: str, block_height: int) -> bool:
        """Cancel a snapshot request for an asset."""
        return client.execute_command("cancelsnapshotrequest", asset_name, block_height)
    
    def distributereward(
        asset_name: str,
        snapshot_height: int,
        distribution_asset_name: str,
        gross_distribution_amount: Union[int, Decimal],
        exception_addresses: Optional[List[str]] = None,
        change_address: Optional[str] = None,
        dry_run: bool = False
    ) -> Union[str, Dict]:
        """Distribute rewards to asset holders."""
        return client.execute_command(
            "distributereward",
            asset_name,
            snapshot_height,
            distribution_asset_name,
            gross_distribution_amount,
            exception_addresses,
            change_address,
            dry_run
        )
    
    def getdistributestatus(
        asset_name: str,
        snapshot_height: int,
        distribution_asset_name: str,
        gross_distribution_amount: Union[int, Decimal],
        exception_addresses: Optional[List[str]] = None
    ) -> DistributionStatus:
        """Get the status of a reward distribution."""
        result = client.execute_command(
            "getdistributestatus",
            asset_name,
            snapshot_height,
            distribution_asset_name,
            gross_distribution_amount,
            exception_addresses
        )
        return DistributionStatus.model_validate(result)
    
    def getsnapshotrequest(asset_name: str, block_height: int) -> SnapshotRequest:
        """Get information about a snapshot request."""
        result = client.execute_command("getsnapshotrequest", asset_name, block_height)
        return SnapshotRequest.model_validate(result)
    
    def listsnapshotrequests(
        asset_names: Optional[List[str]] = None,
        block_heights: Optional[List[int]] = None
    ) -> List[SnapshotRequest]:
        """List all snapshot requests."""
        result = client.execute_command("listsnapshotrequests", asset_names, block_heights)
        return [SnapshotRequest.model_validate(req) for req in result]
    
    def requestsnapshot(asset_name: str, block_height: int) -> bool:
        """Request a snapshot of asset holders at a specific block height."""
        return client.execute_command("requestsnapshot", asset_name, block_height)
    
    # Add methods to client
    client.cancelsnapshotrequest = cancelsnapshotrequest
    client.distributereward = distributereward
    client.getdistributestatus = getdistributestatus
    client.getsnapshotrequest = getsnapshotrequest
    client.listsnapshotrequests = listsnapshotrequests
    client.requestsnapshot = requestsnapshot
    
    return client 