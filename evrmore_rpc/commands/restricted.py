from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field

class QualifierAsset(BaseModel):
    """Model for qualifier asset information"""
    name: str = Field(..., description="The name of the qualifier asset")
    amount: Decimal = Field(..., description="The amount of the qualifier asset")
    ipfs_hash: Optional[str] = Field(None, description="The IPFS hash of the qualifier asset")
    txid: str = Field(..., description="The transaction ID of the qualifier asset creation")

class RestrictedAsset(BaseModel):
    """Model for restricted asset information"""
    name: str = Field(..., description="The name of the restricted asset")
    amount: Decimal = Field(..., description="The amount of the restricted asset")
    units: int = Field(..., description="The units of the restricted asset")
    reissuable: bool = Field(..., description="Whether the asset is reissuable")
    verifier: str = Field(..., description="The verifier string for the restricted asset")
    ipfs_hash: Optional[str] = Field(None, description="The IPFS hash of the restricted asset")
    txid: str = Field(..., description="The transaction ID of the restricted asset creation")

class AddressRestriction(BaseModel):
    """Model for address restriction information"""
    address: str = Field(..., description="The restricted address")
    restricted_name: str = Field(..., description="The name of the restricted asset")
    status: bool = Field(..., description="Whether the address is restricted")

class AddressTag(BaseModel):
    """Model for address tag information"""
    address: str = Field(..., description="The tagged address")
    tag_name: str = Field(..., description="The name of the tag")
    status: bool = Field(..., description="Whether the address has the tag")

def wrap_restricted_commands(client):
    """Add typed restricted asset commands to the client."""
    
    def addtagtoaddress(
        tag_name: str,
        to_address: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Add a qualifier tag to an address."""
        return client.execute_command(
            "addtagtoaddress",
            tag_name,
            to_address,
            change_address,
            asset_data
        )
    
    def checkaddressrestriction(address: str, restricted_name: str) -> bool:
        """Check if an address is restricted for a restricted asset."""
        return client.execute_command("checkaddressrestriction", address, restricted_name)
    
    def checkaddresstag(address: str, tag_name: str) -> bool:
        """Check if an address has a specific qualifier tag."""
        return client.execute_command("checkaddresstag", address, tag_name)
    
    def checkglobalrestriction(restricted_name: str) -> bool:
        """Check if a restricted asset is globally frozen."""
        return client.execute_command("checkglobalrestriction", restricted_name)
    
    def freezeaddress(
        asset_name: str,
        address: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Freeze a restricted asset for an address."""
        return client.execute_command(
            "freezeaddress",
            asset_name,
            address,
            change_address,
            asset_data
        )
    
    def freezerestrictedasset(
        asset_name: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Globally freeze a restricted asset."""
        return client.execute_command(
            "freezerestrictedasset",
            asset_name,
            change_address,
            asset_data
        )
    
    def getverifierstring(restricted_name: str) -> str:
        """Get the verifier string for a restricted asset."""
        return client.execute_command("getverifierstring", restricted_name)
    
    def issuequalifierasset(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: Optional[str] = None,
        change_address: Optional[str] = None,
        has_ipfs: bool = False,
        ipfs_hash: Optional[str] = None
    ) -> str:
        """Issue a new qualifier asset."""
        return client.execute_command(
            "issuequalifierasset",
            asset_name,
            qty,
            to_address,
            change_address,
            has_ipfs,
            ipfs_hash
        )
    
    def issuerestrictedasset(
        asset_name: str,
        qty: Union[int, Decimal],
        verifier: str,
        to_address: str,
        change_address: Optional[str] = None,
        units: int = 0,
        reissuable: bool = True,
        has_ipfs: bool = False,
        ipfs_hash: Optional[str] = None
    ) -> str:
        """Issue a new restricted asset."""
        return client.execute_command(
            "issuerestrictedasset",
            asset_name,
            qty,
            verifier,
            to_address,
            change_address,
            units,
            reissuable,
            has_ipfs,
            ipfs_hash
        )
    
    def isvalidverifierstring(verifier_string: str) -> bool:
        """Check if a verifier string is valid."""
        return client.execute_command("isvalidverifierstring", verifier_string)
    
    def listaddressesfortag(tag_name: str) -> List[str]:
        """List addresses that have a specific qualifier tag."""
        return client.execute_command("listaddressesfortag", tag_name)
    
    def listaddressrestrictions(address: str) -> List[AddressRestriction]:
        """List all restrictions for an address."""
        result = client.execute_command("listaddressrestrictions", address)
        return [AddressRestriction.model_validate(r) for r in result]
    
    def listglobalrestrictions() -> List[str]:
        """List all globally frozen restricted assets."""
        return client.execute_command("listglobalrestrictions")
    
    def listtagsforaddress(address: str) -> List[AddressTag]:
        """List all qualifier tags for an address."""
        result = client.execute_command("listtagsforaddress", address)
        return [AddressTag.model_validate(t) for t in result]
    
    def reissuerestrictedasset(
        asset_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        change_verifier: bool = False,
        new_verifier: Optional[str] = None,
        change_address: Optional[str] = None,
        new_units: Optional[int] = None,
        reissuable: Optional[bool] = None,
        new_ipfs: Optional[str] = None
    ) -> str:
        """Reissue a restricted asset."""
        return client.execute_command(
            "reissuerestrictedasset",
            asset_name,
            qty,
            to_address,
            change_verifier,
            new_verifier,
            change_address,
            new_units,
            reissuable,
            new_ipfs
        )
    
    def removetagfromaddress(
        tag_name: str,
        to_address: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Remove a qualifier tag from an address."""
        return client.execute_command(
            "removetagfromaddress",
            tag_name,
            to_address,
            change_address,
            asset_data
        )
    
    def transferqualifier(
        qualifier_name: str,
        qty: Union[int, Decimal],
        to_address: str,
        change_address: Optional[str] = None,
        message: Optional[str] = None,
        expire_time: Optional[int] = None
    ) -> str:
        """Transfer a qualifier asset."""
        return client.execute_command(
            "transferqualifier",
            qualifier_name,
            qty,
            to_address,
            change_address,
            message,
            expire_time
        )
    
    def unfreezeaddress(
        asset_name: str,
        address: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Unfreeze a restricted asset for an address."""
        return client.execute_command(
            "unfreezeaddress",
            asset_name,
            address,
            change_address,
            asset_data
        )
    
    def unfreezerestrictedasset(
        asset_name: str,
        change_address: Optional[str] = None,
        asset_data: Optional[str] = None
    ) -> str:
        """Globally unfreeze a restricted asset."""
        return client.execute_command(
            "unfreezerestrictedasset",
            asset_name,
            change_address,
            asset_data
        )
    
    def viewmyrestrictedaddresses() -> List[AddressRestriction]:
        """View all restricted addresses owned by the wallet."""
        result = client.execute_command("viewmyrestrictedaddresses")
        return [AddressRestriction.model_validate(r) for r in result]
    
    def viewmytaggedaddresses() -> List[AddressTag]:
        """View all tagged addresses owned by the wallet."""
        result = client.execute_command("viewmytaggedaddresses")
        return [AddressTag.model_validate(t) for t in result]
    
    # Add methods to client
    client.addtagtoaddress = addtagtoaddress
    client.checkaddressrestriction = checkaddressrestriction
    client.checkaddresstag = checkaddresstag
    client.checkglobalrestriction = checkglobalrestriction
    client.freezeaddress = freezeaddress
    client.freezerestrictedasset = freezerestrictedasset
    client.getverifierstring = getverifierstring
    client.issuequalifierasset = issuequalifierasset
    client.issuerestrictedasset = issuerestrictedasset
    client.isvalidverifierstring = isvalidverifierstring
    client.listaddressesfortag = listaddressesfortag
    client.listaddressrestrictions = listaddressrestrictions
    client.listglobalrestrictions = listglobalrestrictions
    client.listtagsforaddress = listtagsforaddress
    client.reissuerestrictedasset = reissuerestrictedasset
    client.removetagfromaddress = removetagfromaddress
    client.transferqualifier = transferqualifier
    client.unfreezeaddress = unfreezeaddress
    client.unfreezerestrictedasset = unfreezerestrictedasset
    client.viewmyrestrictedaddresses = viewmyrestrictedaddresses
    client.viewmytaggedaddresses = viewmytaggedaddresses
    
    return client 