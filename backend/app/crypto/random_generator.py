"""
Cryptographically secure random number generation.
Uses high-entropy sources for cryptographic operations.
"""

from Cryptodome.Random import get_random_bytes
import secrets
import string


class RandomGenerationError(Exception):
    """Raised when random generation fails."""
    pass


def secure_random_bytes(length: int) -> bytes:
    """
    Generate cryptographically secure random bytes.
    
    Args:
        length: Number of random bytes to generate
    
    Returns:
        Random bytes
    """
    if length < 0:
        raise RandomGenerationError("Length must be non-negative")
    
    try:
        return get_random_bytes(length)
    except Exception as e:
        raise RandomGenerationError(f"Random byte generation failed: {str(e)}")


def secure_random_int(min_val: int, max_val: int) -> int:
    """
    Generate cryptographically secure random integer.
    
    Args:
        min_val: Minimum value (inclusive)
        max_val: Maximum value (inclusive)
    
    Returns:
        Random integer in range
    """
    try:
        return secrets.randbelow(max_val - min_val + 1) + min_val
    except Exception as e:
        raise RandomGenerationError(f"Random integer generation failed: {str(e)}")


def generate_recovery_key(format_style: str = 'hex') -> str:
    """
    Generate a human-readable recovery/decryption key.
    
    Args:
        format_style: 'hex', 'base58', or 'alphanumeric'
    
    Returns:
        Formatted key string
    """
    try:
        key_bytes = secure_random_bytes(16)
        
        if format_style == 'hex':
            # Format: 8F92-A1B2-77C9-D4E5
            hex_str = key_bytes.hex().upper()
            return '-'.join([hex_str[i:i+4] for i in range(0, len(hex_str), 4)])
        
        elif format_style == 'base58':
            # Base58 encoding (避免 0, O, I, l)
            alphabet = "123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz"
            num = int.from_bytes(key_bytes, byteorder='big')
            result = []
            while num > 0:
                num, remainder = divmod(num, 58)
                result.append(alphabet[remainder])
            return ''.join(reversed(result)) or '1'
        
        elif format_style == 'alphanumeric':
            # Format: 8F92A1B277C9D4E5ABCD
            return key_bytes.hex().upper()
        
        else:
            raise RandomGenerationError(f"Unknown format style: {format_style}")
    
    except Exception as e:
        raise RandomGenerationError(f"Recovery key generation failed: {str(e)}")


def generate_keyless_mode_key() -> tuple:
    """
    Generate a random key for keyless mode sharing.
    
    Returns:
        Tuple of (key_bytes, key_string)
    """
    key_bytes = secure_random_bytes(32)  # 256-bit key
    key_string = generate_recovery_key('hex')
    return key_bytes, key_string
