from typing import Dict, List, Optional, Union
from decimal import Decimal
from pydantic import BaseModel, Field
from datetime import datetime

class NetworkInfo(BaseModel):
    """Model for 'getnetworkinfo' response"""
    version: int = Field(..., description="The server version")
    subversion: str = Field(..., description="The server subversion string")
    protocolversion: int = Field(..., description="The protocol version")
    localservices: str = Field(..., description="The services we offer to the network")
    localrelay: bool = Field(..., description="True if transaction relay is requested from peers")
    timeoffset: int = Field(..., description="The time offset")
    connections: int = Field(..., description="The number of connections")
    networkactive: bool = Field(..., description="Whether p2p networking is enabled")
    networks: List[Dict] = Field(..., description="Information per network")
    relayfee: Decimal = Field(..., description="Minimum relay fee for transactions in EVR/kB")
    incrementalfee: Decimal = Field(..., description="Minimum fee increment for mempool limiting in EVR/kB")
    localaddresses: List[Dict] = Field(..., description="List of local addresses")
    warnings: str = Field("", description="Any network and blockchain warnings")

class PeerInfo(BaseModel):
    """Model for 'getpeerinfo' response"""
    id: int = Field(..., description="Peer index")
    addr: str = Field(..., description="The ip address and port of the peer")
    addrbind: Optional[str] = Field(None, description="Bind address of the connection to the peer")
    addrlocal: Optional[str] = Field(None, description="Local address")
    services: str = Field(..., description="The services offered")
    relaytxes: bool = Field(..., description="Whether peer has asked us to relay transactions to it")
    lastsend: int = Field(..., description="The time in seconds since epoch since last send")
    lastrecv: int = Field(..., description="The time in seconds since epoch since last receive")
    bytessent: int = Field(..., description="The total bytes sent")
    bytesrecv: int = Field(..., description="The total bytes received")
    conntime: int = Field(..., description="The connection time in seconds since epoch")
    timeoffset: int = Field(..., description="The time offset in seconds")
    pingtime: Optional[float] = Field(None, description="ping time (if available)")
    minping: Optional[float] = Field(None, description="minimum observed ping time (if any at all)")
    pingwait: Optional[float] = Field(None, description="ping wait (if non-zero)")
    version: int = Field(..., description="The peer version, such as 70001")
    subver: str = Field(..., description="The string version")
    inbound: bool = Field(..., description="Inbound (true) or Outbound (false)")
    addnode: bool = Field(..., description="Whether connection was due to addnode/-connect or if it was an automatic/inbound connection")
    startingheight: int = Field(..., description="The starting height (block) of the peer")
    banscore: Optional[int] = Field(None, description="The ban score")
    synced_headers: int = Field(..., description="The last header we have in common with this peer")
    synced_blocks: int = Field(..., description="The last block we have in common with this peer")
    inflight: List[int] = Field(..., description="The heights of blocks we're currently asking from this peer")
    whitelisted: bool = Field(..., description="Whether the peer is whitelisted")
    bytessent_per_msg: Dict[str, int] = Field(..., description="A dictionary of bytes sent per message type")
    bytesrecv_per_msg: Dict[str, int] = Field(..., description="A dictionary of bytes received per message type")

class BannedEntry(BaseModel):
    """Model for items in 'listbanned' response"""
    address: str = Field(..., description="The banned address")
    banned_until: int = Field(..., description="The timestamp when the ban expires")
    ban_created: int = Field(..., description="The timestamp when the ban was created")
    ban_reason: str = Field(..., description="The reason for the ban")

class AddedNodeInfo(BaseModel):
    """Model for 'getaddednodeinfo' response"""
    addednode: str = Field(..., description="The node IP address or name")
    connected: bool = Field(..., description="If connected")
    addresses: List[Dict] = Field(..., description="List of addresses for this node")

def wrap_network_commands(client):
    """Add typed network commands to the client."""
    
    def addnode(node: str, command: str) -> None:
        """Add, remove or try a connection to a node."""
        if command not in ["add", "remove", "onetry"]:
            raise ValueError("Command must be one of: add, remove, onetry")
        return client.execute_command("addnode", node, command)
    
    def clearbanned() -> None:
        """Clear all banned IPs."""
        return client.execute_command("clearbanned")
    
    def disconnectnode(address: Optional[str] = None, nodeid: Optional[int] = None) -> None:
        """Disconnect from a specified node."""
        if address is not None and nodeid is not None:
            return client.execute_command("disconnectnode", address, nodeid)
        elif address is not None:
            return client.execute_command("disconnectnode", address)
        elif nodeid is not None:
            return client.execute_command("disconnectnode", "", nodeid)
        raise ValueError("Either address or nodeid must be specified")
    
    def getaddednodeinfo(node: Optional[str] = None) -> List[AddedNodeInfo]:
        """Get information about added nodes."""
        if node is not None:
            result = client.execute_command("getaddednodeinfo", node)
        else:
            result = client.execute_command("getaddednodeinfo")
        return [AddedNodeInfo.model_validate(info) for info in result]
    
    def getconnectioncount() -> int:
        """Get the number of connections to other nodes."""
        return client.execute_command("getconnectioncount")
    
    def getnettotals() -> Dict:
        """Get network traffic statistics."""
        return client.execute_command("getnettotals")
    
    def getnetworkinfo() -> NetworkInfo:
        """Get network info."""
        result = client.execute_command("getnetworkinfo")
        return NetworkInfo.model_validate(result)
    
    def getpeerinfo() -> List[PeerInfo]:
        """Get data about each connected node."""
        result = client.execute_command("getpeerinfo")
        return [PeerInfo.model_validate(peer) for peer in result]
    
    def listbanned() -> List[BannedEntry]:
        """List all banned IPs/Subnets."""
        result = client.execute_command("listbanned")
        return [BannedEntry.model_validate(entry) for entry in result]
    
    def ping() -> None:
        """Request that a ping be sent to all other nodes."""
        return client.execute_command("ping")
    
    def setban(subnet: str, command: str, bantime: Optional[int] = None, absolute: bool = False) -> None:
        """Add or remove an IP/Subnet from the banned list."""
        if command not in ["add", "remove"]:
            raise ValueError("Command must be either 'add' or 'remove'")
        if bantime is not None:
            return client.execute_command("setban", subnet, command, bantime, absolute)
        return client.execute_command("setban", subnet, command)
    
    def setnetworkactive(state: bool) -> bool:
        """Enable/disable all P2P network activity."""
        return client.execute_command("setnetworkactive", state)
    
    # Add methods to client
    client.addnode = addnode
    client.clearbanned = clearbanned
    client.disconnectnode = disconnectnode
    client.getaddednodeinfo = getaddednodeinfo
    client.getconnectioncount = getconnectioncount
    client.getnettotals = getnettotals
    client.getnetworkinfo = getnetworkinfo
    client.getpeerinfo = getpeerinfo
    client.listbanned = listbanned
    client.ping = ping
    client.setban = setban
    client.setnetworkactive = setnetworkactive
    
    return client 