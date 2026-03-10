"""
Audio steganography using LSB and phase shift methods.
"""

import numpy as np
import struct
import io
from typing import Tuple


class AudioSteganography:
    """Audio steganography with LSB embedding."""
    
    @staticmethod
    def embed_lsb(
        audio_data: np.ndarray,
        payload: bytes,
        sample_rate: int = 44100
    ) -> Tuple[np.ndarray, dict]:
        """
        Embed data in audio LSB.
        
        Args:
            audio_data: Audio samples
            payload: Encrypted payload
            sample_rate: Sample rate
        
        Returns:
            Tuple of (stego_audio, metadata)
        """
        # Prepare payload with size header
        payload_size = len(payload)
        size_header = struct.pack('>I', payload_size)
        full_payload = size_header + payload
        payload_bits = ''.join(format(byte, '08b') for byte in full_payload)
        
        stego_audio = audio_data.copy().astype(np.int32)
        bit_index = 0
        
        # Embed in least significant bits
        for i in range(len(stego_audio)):
            if bit_index >= len(payload_bits):
                break
            
            bit = int(payload_bits[bit_index])
            stego_audio[i] = (stego_audio[i] & 0xFFFFFFFE) | bit
            bit_index += 1
        
        metadata = {
            'method': 'audio_lsb',
            'payload_size': payload_size,
            'sample_rate': sample_rate,
            'embedded_bits': len(payload_bits)
        }
        
        return stego_audio.astype(audio_data.dtype), metadata
    
    @staticmethod
    def extract_lsb(
        audio_data: np.ndarray,
        payload_size: int = None
    ) -> bytes:
        """Extract LSB-embedded audio payload."""
        audio_int = audio_data.astype(np.int32)
        bits = [str(sample & 1) for sample in audio_int]
        
        if payload_size is None:
            # Auto-detect
            size_bits = ''.join(bits[:32])
            payload_size = struct.unpack('>I', bytes(int(size_bits[i:i+8], 2) for i in range(0, 32, 8)))[0]
        
        # Extract payload
        needed_bits = (4 + payload_size) * 8
        payload_bits = ''.join(bits[:needed_bits])
        payload_bytes = bytes(int(payload_bits[i:i+8], 2) for i in range(0, len(payload_bits), 8))
        
        return payload_bytes[4:]
