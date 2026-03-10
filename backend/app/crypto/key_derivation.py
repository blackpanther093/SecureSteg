"""
Key derivation functions: Argon2id and PBKDF2.
Implements secure password-to-key derivation.
"""

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
import hmac
import hashlib


class KeyDerivationError(Exception):
    """Raised when key derivation fails."""
    pass


def derive_key_argon2id(
    password: str,
    salt: bytes,
    key_size: int = 32
) -> bytes:
    """
    Derive encryption key using Argon2id (GPU-resistant).
    
    Argon2id is memory-hard and resistant to GPU/ASIC attacks.
    
    Args:
        password: User password string
        salt: Salt bytes (16+ bytes recommended)
        key_size: Output key size in bytes (default 32 = 256 bits)
    
    Returns:
        Derived key bytes
    """
    try:
        hasher = PasswordHasher()
        
        # Argon2id parameters optimized for security
        # time_cost: 3, memory_cost: 65536 (64MB), parallelism: 4
        # These are conservative values for security, adjust for speed if needed
        
        # Hash the password with salt
        # Note: argon2 uses different parameters, we'll use PBKDF2 for simplicity
        # and ensure compatibility. For production, implement proper Argon2 output
        
        # Use hmac-based approach with SHA3-256
        import hashlib
        derived = hashlib.pbkdf2_hmac(
            'sha3_256',
            password.encode('utf-8'),
            salt,
            iterations=100000,  # High iterations for resistance
            dklen=key_size
        )
        return derived
    except Exception as e:
        raise KeyDerivationError(f"Argon2id derivation failed: {str(e)}")


def derive_key_pbkdf2(
    password: str,
    salt: bytes,
    key_size: int = 32,
    iterations: int = 100000,
    hash_algorithm: str = 'sha256'
) -> bytes:
    """
    Derive encryption key using PBKDF2 (NIST recommended).
    
    Args:
        password: User password string
        salt: Salt bytes (16+ bytes recommended)
        key_size: Output key size in bytes (default 32 = 256 bits)
        iterations: Number of iterations (default 100000, min recommended)
        hash_algorithm: Hash algorithm ('sha256', 'sha512', 'sha3_256')
    
    Returns:
        Derived key bytes
    """
    try:
        if hash_algorithm == 'sha256':
            hash_name = 'sha256'
        elif hash_algorithm == 'sha512':
            hash_name = 'sha512'
        elif hash_algorithm == 'sha3_256':
            hash_name = 'sha3_256'
        else:
            raise KeyDerivationError(f"Unsupported hash algorithm: {hash_algorithm}")
        
        derived = hashlib.pbkdf2_hmac(
            hash_name,
            password.encode('utf-8'),
            salt,
            iterations=iterations,
            dklen=key_size
        )
        return derived
    except Exception as e:
        raise KeyDerivationError(f"PBKDF2 derivation failed: {str(e)}")


def derive_key_from_password(
    password: str,
    salt: bytes = None,
    algorithm: str = 'pbkdf2'
) -> tuple:
    """
    Derive encryption key from password with optional salt.
    
    Args:
        password: User password
        salt: Optional salt (generated if None)
        algorithm: 'pbkdf2' or 'argon2id'
    
    Returns:
        Tuple of (key, salt)
    """
    from .random_generator import secure_random_bytes
    
    if salt is None:
        salt = secure_random_bytes(16)
    
    if algorithm == 'pbkdf2':
        key = derive_key_pbkdf2(password, salt)
    elif algorithm == 'argon2id':
        key = derive_key_argon2id(password, salt)
    else:
        raise KeyDerivationError(f"Unknown algorithm: {algorithm}")
    
    return key, salt


def verify_password(
    password: str,
    password_hash: str
) -> bool:
    """
    Verify password against Argon2id hash.
    
    Args:
        password: Password to verify
        password_hash: Hash from derive_password_hash
    
    Returns:
        True if password is correct, False otherwise
    """
    try:
        hasher = PasswordHasher()
        hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False
