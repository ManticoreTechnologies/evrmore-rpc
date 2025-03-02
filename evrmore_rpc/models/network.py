"""
evrmore-rpc: Network models for Evrmore RPC responses
Copyright (c) 2025 Manticore Technologies
MIT License - See LICENSE file for details
"""

from typing import Dict, List, Optional, Union, Any
from decimal import Decimal
from pydantic import BaseModel, Field

class Network(BaseModel):
    """Model for network information in 'getnetworkinfo' response"""
    name: str = Field(..., description="Network name")
    limited: bool = Field(..., description="Whether the network is limited")
    reachable: bool = Field(..., description="Whether the network is reachable")
    proxy: Optional[str] = Field(None, description="Proxy used for this network")
    proxy_randomize_credentials: bool = Field(..., description="Whether credentials are randomized")

class LocalAddress(BaseModel):
    """Model for local address information in 'getnetworkinfo' response"""
    address: str = Field(..., description="Local address")
    port: int = Field(..., description="Local port")
    score: int = Field(..., description="Address score")

class NetworkInfo(BaseModel):
    """Model for 'getnetworkinfo' response"""
    version: int = Field(..., description="Node version")
    subversion: str = Field(..., description="Node subversion")
    protocolversion: int = Field(..., description="Protocol version")
    localservices: str = Field(..., description="Services provided by this node")
    localrelay: bool = Field(..., description="Whether this node relays transactions")
    timeoffset: int = Field(..., description="Time offset in seconds")
    connections: int = Field(..., description="Number of connections")
    networks: List[Network] = Field(..., description="Information per network")
    relayfee: Decimal = Field(..., description="Minimum relay fee")
    localaddresses: List[LocalAddress] = Field(default_factory=list, description="List of local addresses")
    warnings: str = Field("", description="Network warnings")

class PeerInfo(BaseModel):
    """Model for items in 'getpeerinfo' response"""
    id: int = Field(..., description="Peer ID")
    addr: str = Field(..., description="Peer address")
    addrbind: Optional[str] = Field(None, description="Bind address")
    addrlocal: Optional[str] = Field(None, description="Local address")
    services: str = Field(..., description="Services provided by the peer")
    relaytxes: bool = Field(..., description="Whether the peer relays transactions")
    lastsend: int = Field(..., description="Time since last send")
    lastrecv: int = Field(..., description="Time since last receive")
    bytessent: int = Field(..., description="Total bytes sent")
    bytesrecv: int = Field(..., description="Total bytes received")
    conntime: int = Field(..., description="Connection time")
    timeoffset: int = Field(..., description="Time offset in seconds")
    pingtime: Optional[float] = Field(None, description="Ping time")
    minping: Optional[float] = Field(None, description="Minimum ping time")
    version: int = Field(..., description="Peer version")
    subver: str = Field(..., description="Peer subversion")
    inbound: bool = Field(..., description="Whether the peer is inbound")
    addnode: bool = Field(..., description="Whether the peer was added via addnode")
    startingheight: int = Field(..., description="Starting height")
    banscore: int = Field(..., description="Ban score")
    synced_headers: int = Field(..., description="Synced headers")
    synced_blocks: int = Field(..., description="Synced blocks")
    inflight: List[int] = Field(default_factory=list, description="Blocks in flight")
    whitelisted: bool = Field(..., description="Whether the peer is whitelisted")
    
class NetTotals(BaseModel):
    """Model for 'getnettotals' response"""
    totalbytesrecv: int = Field(..., description="Total bytes received")
    totalbytessent: int = Field(..., description="Total bytes sent")
    timemillis: int = Field(..., description="Current UNIX time in milliseconds")
    uploadtarget: Dict[str, Any] = Field(..., description="Upload target information") 