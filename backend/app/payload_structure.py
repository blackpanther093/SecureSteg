"""
Enhanced payload structure supporting files, expiration, watermarks, and metadata.
Payload format: MAGIC(2) + VERSION(1) + METADATA_SIZE(2) + METADATA + CONTENT_SIZE(4) + CONTENT
"""

import json
import struct
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict
from enum import Enum

class ExpirationMode(str, Enum):
    """Expiration modes for self-destruct messages."""
    UNLIMITED = "unlimited"
    ONE_DECODE = "one_decode"
    HOURS_24 = "24_hours"


class WatermarkMode(str, Enum):
    """Watermark visibility modes."""
    HIDDEN = "hidden"          # Full steganography
    VISIBLE = "visible"        # Visible overlay


class EmbeddingMethod(str, Enum):
    """Advanced embedding methods."""
    LSB = "lsb"                          # Basic LSB
    MULTI_LAYER_LSB = "multi_layer_lsb" # LSB across all channels
    AES_LSB = "aes_lsb"                  # AES-encrypted before LSB
    DCT = "dct"                          # Discrete Cosine Transform
    DWT = "dwt"                          # Discrete Wavelet Transform
    SPREAD_SPECTRUM = "spread_spectrum"  # Spread spectrum
    PHASE_CODING = "phase_coding"        # Phase coding in frequency domain
    HISTOGRAM_SHIFTING = "histogram_shifting"  # Histogram-based
    PERLIN_NOISE = "perlin_noise"        # Perlin noise embedding


@dataclass
class PayloadMetadata:
    """Metadata for hidden payload."""
    version: int = 1
    content_type: str = "text/plain"  # MIME type
    filename: Optional[str] = None     # Original filename if not text
    expiration_mode: str = ExpirationMode.UNLIMITED
    expiration_timestamp: Optional[int] = None  # Unix timestamp
    decode_count: int = 0              # Tracks decodes for one_decode mode
    max_decodes: Optional[int] = None  # Optional hard decode limit
    watermark_mode: str = WatermarkMode.HIDDEN
    embedding_method: str = EmbeddingMethod.MULTI_LAYER_LSB
    seed: int = 42                     # PRNG seed
    encryption_key_hash: Optional[str] = None  # SHA256 of encryption key
    is_encrypted: bool = True
    compression: bool = True
    creation_timestamp: int = int(time.time())
    
    def to_json(self) -> str:
        """Serialize to JSON."""
        data = asdict(self)
        return json.dumps(data, indent=None)
    
    @staticmethod
    def from_json(json_str: str) -> 'PayloadMetadata':
        """Deserialize from JSON."""
        data = json.loads(json_str)
        return PayloadMetadata(**data)


class PayloadStructure:
    """Encapsulates the binary payload structure."""
    
    MAGIC = b'SG'  # Magic bytes for SecureSteg
    VERSION = 1
    
    @staticmethod
    def encode(
        content: bytes,
        metadata: PayloadMetadata
    ) -> bytes:
        """
        Encode payload with metadata.
        
        Format:
        MAGIC(2) + VERSION(1) + METADATA_LEN(2) + METADATA_JSON + CONTENT_LEN(4) + CONTENT
        """
        metadata_json = metadata.to_json().encode('utf-8')
        metadata_len = len(metadata_json)
        
        if metadata_len > 65535:
            raise ValueError("Metadata too large (max 65535 bytes)")
        if len(content) > 4294967295:
            raise ValueError("Content too large (max 4GB)")
        
        # Build payload
        payload = PayloadStructure.MAGIC
        payload += struct.pack('B', PayloadStructure.VERSION)
        payload += struct.pack('>H', metadata_len)
        payload += metadata_json
        payload += struct.pack('>I', len(content))
        payload += content
        
        return payload
    
    @staticmethod
    def decode(payload: bytes) -> tuple[PayloadMetadata, bytes]:
        """
        Decode payload to extract metadata and content.
        
        Returns: (metadata, content)
        """
        pos = 0
        
        # Check magic
        magic = payload[pos:pos+2]
        if magic != PayloadStructure.MAGIC:
            raise ValueError(f"Invalid magic bytes: {magic}")
        pos += 2
        
        # Check version
        version = payload[pos]
        if version != PayloadStructure.VERSION:
            raise ValueError(f"Unsupported payload version: {version}")
        pos += 1
        
        # Read metadata length
        metadata_len = struct.unpack('>H', payload[pos:pos+2])[0]
        pos += 2
        
        # Read metadata
        metadata_json = payload[pos:pos+metadata_len].decode('utf-8')
        metadata = PayloadMetadata.from_json(metadata_json)
        pos += metadata_len
        
        # Read content length
        content_len = struct.unpack('>I', payload[pos:pos+4])[0]
        pos += 4
        
        # Read content
        content = payload[pos:pos+content_len]
        
        return metadata, content
    
    @staticmethod
    def check_expiration(metadata: PayloadMetadata) -> tuple[bool, Optional[str]]:
        """
        Check if payload has expired.
        
        Returns: (is_expired, reason)
        """
        if metadata.expiration_mode == ExpirationMode.UNLIMITED:
            return False, None
        
        if metadata.expiration_mode == ExpirationMode.ONE_DECODE:
            if metadata.decode_count > 0:
                return True, "Message has already been decoded and set to self-destruct"

        elif metadata.expiration_mode == "decode_limit":
            if metadata.max_decodes and metadata.decode_count >= metadata.max_decodes:
                return True, f"Message reached decode limit ({metadata.max_decodes})"
        
        elif metadata.expiration_mode == ExpirationMode.HOURS_24:
            if metadata.expiration_timestamp is None:
                return False, None
            if int(time.time()) > metadata.expiration_timestamp:
                return True, "Message expired after 24 hours"

        elif metadata.expiration_mode == "time_limit":
            if metadata.expiration_timestamp is None:
                return False, None
            if int(time.time()) > metadata.expiration_timestamp:
                return True, "Message expired due to time limit"
        
        return False, None
    
    @staticmethod
    def increment_decode_count(metadata: PayloadMetadata) -> None:
        """Increment decode counter for self-destruct tracking."""
        metadata.decode_count += 1
