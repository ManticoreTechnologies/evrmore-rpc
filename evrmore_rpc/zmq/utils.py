import binascii
import struct
from typing import Tuple, Optional, Dict, Any
from datetime import datetime

def decode_varint(data: bytes, offset: int = 0) -> Tuple[int, int]:
    """
    Decode a variable integer from bytes.
    
    Args:
        data: Raw bytes to decode
        offset: Starting offset in the bytes
        
    Returns:
        Tuple of (value, bytes_read)
    """
    n = 0
    for i in range(9):
        if i >= len(data):
            raise ValueError("Incomplete varint")
            
        ch = data[offset + i]
        if i < 8:
            n |= (ch & 0x7f) << (i * 7)
            if not (ch & 0x80):
                return n, i + 1
        else:
            n |= ch << 56
            return n, 9
            
    raise ValueError("Invalid varint")

def decode_script(script: bytes) -> Dict[str, Any]:
    """
    Decode a Bitcoin script into its operations.
    
    Args:
        script: Raw script bytes
        
    Returns:
        Dictionary containing script info
    """
    ops = []
    i = 0
    
    while i < len(script):
        op = script[i]
        i += 1
        
        if op <= 0x4b:
            # Direct push of bytes
            data = script[i:i + op]
            ops.append({
                'op': 'PUSH',
                'data': binascii.hexlify(data).decode()
            })
            i += op
        elif op == 0x4c:
            # OP_PUSHDATA1
            if i >= len(script):
                break
            length = script[i]
            i += 1
            data = script[i:i + length]
            ops.append({
                'op': 'PUSHDATA1',
                'data': binascii.hexlify(data).decode()
            })
            i += length
        elif op == 0x4d:
            # OP_PUSHDATA2
            if i + 1 >= len(script):
                break
            length = struct.unpack('<H', script[i:i + 2])[0]
            i += 2
            data = script[i:i + length]
            ops.append({
                'op': 'PUSHDATA2',
                'data': binascii.hexlify(data).decode()
            })
            i += length
        else:
            # Regular opcode
            ops.append({
                'op': f'OP_{op:02x}'.upper()
            })
            
    return {
        'asm': ' '.join(op.get('data', op['op']) for op in ops),
        'hex': binascii.hexlify(script).decode(),
        'ops': ops
    }

def parse_tx_input(data: bytes, offset: int = 0) -> Tuple[Dict[str, Any], int]:
    """
    Parse a transaction input from raw bytes.
    
    Args:
        data: Raw transaction bytes
        offset: Starting offset in the bytes
        
    Returns:
        Tuple of (input_dict, bytes_read)
    """
    if offset + 36 > len(data):
        raise ValueError("Incomplete transaction input")
        
    txid = binascii.hexlify(data[offset:offset + 32][::-1]).decode()
    vout = struct.unpack('<I', data[offset + 32:offset + 36])[0]
    
    script_length, varint_size = decode_varint(data[offset + 36:])
    script_start = offset + 36 + varint_size
    script_end = script_start + script_length
    
    if script_end + 4 > len(data):
        raise ValueError("Incomplete transaction input")
        
    script = data[script_start:script_end]
    sequence = struct.unpack('<I', data[script_end:script_end + 4])[0]
    
    return {
        'txid': txid,
        'vout': vout,
        'scriptSig': decode_script(script),
        'sequence': sequence
    }, script_end + 4 - offset

def parse_tx_output(data: bytes, offset: int = 0) -> Tuple[Dict[str, Any], int]:
    """
    Parse a transaction output from raw bytes.
    
    Args:
        data: Raw transaction bytes
        offset: Starting offset in the bytes
        
    Returns:
        Tuple of (output_dict, bytes_read)
    """
    if offset + 8 > len(data):
        raise ValueError("Incomplete transaction output")
        
    value = struct.unpack('<Q', data[offset:offset + 8])[0]
    
    script_length, varint_size = decode_varint(data[offset + 8:])
    script_start = offset + 8 + varint_size
    script_end = script_start + script_length
    
    if script_end > len(data):
        raise ValueError("Incomplete transaction output")
        
    script = data[script_start:script_end]
    
    return {
        'value': value / 100000000,  # Convert satoshis to EVR
        'n': 0,  # This needs to be set by the caller
        'scriptPubKey': decode_script(script)
    }, script_end - offset

def calculate_difficulty(bits: str) -> float:
    """
    Calculate the mining difficulty from compact bits.
    
    Args:
        bits: Compact difficulty bits as hex string
        
    Returns:
        Floating point difficulty
    """
    bits_int = int(bits, 16)
    size = bits_int >> 24
    word = bits_int & 0x007fffff
    
    if size <= 3:
        word >>= 8 * (3 - size)
        ret = word
    else:
        ret = word
        ret <<= 8 * (size - 3)
        
    ret = float(ret)
    ret /= 0xffff  # Normalize
    
    return ret

def parse_block_header(data: bytes) -> Dict[str, Any]:
    """
    Parse a block header from raw bytes.
    
    Args:
        data: Raw block header bytes
        
    Returns:
        Dictionary containing header info
    """
    if len(data) < 80:
        raise ValueError("Incomplete block header")
        
    return {
        'version': struct.unpack('<I', data[0:4])[0],
        'previousblockhash': binascii.hexlify(data[4:36][::-1]).decode(),
        'merkleroot': binascii.hexlify(data[36:68][::-1]).decode(),
        'time': datetime.fromtimestamp(struct.unpack('<I', data[68:72])[0]),
        'bits': binascii.hexlify(data[72:76]).decode(),
        'nonce': struct.unpack('<I', data[76:80])[0]
    } 