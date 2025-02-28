from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
import binascii

@dataclass
class ZMQTransaction:
    """Model for transaction notifications."""
    txid: str
    hex: str
    size: int
    vsize: int
    version: int
    locktime: int
    vin: List[Dict[str, Any]]
    vout: List[Dict[str, Any]]
    
    @classmethod
    def from_raw(cls, raw_tx: bytes) -> 'ZMQTransaction':
        """Create a transaction model from raw bytes."""
        # TODO: Implement transaction deserialization
        return cls(
            txid=binascii.hexlify(raw_tx[:32]).decode(),
            hex=binascii.hexlify(raw_tx).decode(),
            size=len(raw_tx),
            vsize=len(raw_tx),  # This is an approximation
            version=int.from_bytes(raw_tx[:4], 'little'),
            locktime=int.from_bytes(raw_tx[-4:], 'little'),
            vin=[],  # TODO: Parse inputs
            vout=[]  # TODO: Parse outputs
        )

@dataclass
class ZMQBlock:
    """Model for block notifications."""
    hash: str
    height: int
    version: int
    previousblockhash: str
    merkleroot: str
    time: datetime
    bits: str
    nonce: int
    difficulty: float
    transactions: List[str]
    
    @classmethod
    def from_raw(cls, raw_block: bytes) -> 'ZMQBlock':
        """Create a block model from raw bytes."""
        # TODO: Implement block deserialization
        return cls(
            hash=binascii.hexlify(raw_block[:32]).decode(),
            height=0,  # Need to query RPC for this
            version=int.from_bytes(raw_block[4:8], 'little'),
            previousblockhash=binascii.hexlify(raw_block[8:40]).decode(),
            merkleroot=binascii.hexlify(raw_block[40:72]).decode(),
            time=datetime.fromtimestamp(int.from_bytes(raw_block[72:76], 'little')),
            bits=binascii.hexlify(raw_block[76:80]).decode(),
            nonce=int.from_bytes(raw_block[80:84], 'little'),
            difficulty=0.0,  # Need to calculate this
            transactions=[]  # TODO: Parse transactions
        )

@dataclass
class ZMQSequence:
    """Model for sequence notifications."""
    hash: str
    height: int
    time: datetime
    
    @classmethod
    def from_notification(cls, sequence: int, body: bytes) -> 'ZMQSequence':
        """Create a sequence model from notification data."""
        return cls(
            hash=binascii.hexlify(body).decode(),
            height=sequence,
            time=datetime.now()
        ) 