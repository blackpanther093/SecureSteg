"""
Utility functions for payload handling, extraction, and expiration checks.
"""

import time
from app.payload_structure import PayloadStructure, PayloadMetadata
from fastapi import HTTPException


class PayloadHandler:
    """Handles payload encoding, decoding, and expiration checks."""
    
    @staticmethod
    def try_decode_payload(raw_payload: bytes) -> tuple:
        """
        Try to decode as new payload format; fall back to old format if it fails.
        Returns (metadata, content, is_new_format)
        """
        try:
            # Try new format
            metadata, content = PayloadStructure.decode(raw_payload)
            return metadata, content, True
        except (ValueError, struct.error):
            # Fall back to old format (raw encrypted data)
            return None, raw_payload, False
    
    @staticmethod
    def check_expiration(metadata: PayloadMetadata) -> tuple[bool, str]:
        """
        Check if payload has expired based on metadata.
        Returns (is_expired, reason)
        """
        if metadata is None:
            return False, None
        
        is_expired, reason = PayloadStructure.check_expiration(metadata)
        return is_expired, reason


# Decorator for extraction operations
def handle_expiration_and_extraction(func):
    """Wrapper for extraction functions that handles expiration checking."""
    async def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        # Check expiration if metadata present
        if 'metadata' in result and result['metadata']:
            is_expired, reason = PayloadHandler.check_expiration(result['metadata'])
            if is_expired:
                raise HTTPException(
                    status_code=410,  # HTTP 410 Gone
                    detail=f"Message expired: {reason}"
                )
        return result
    return wrapper
