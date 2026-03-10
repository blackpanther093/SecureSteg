"""
High-security AES-256-GCM encryption module.
Implements authenticated encryption with cryptographic randomness.
"""

import os
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from Cryptodome.Random import get_random_bytes


class EncryptionError(Exception):
    """Raised when encryption/decryption fails."""
    pass


class AuthenticationError(Exception):
    """Raised when authentication tag verification fails."""
    pass


def generate_random_key(key_size: int = 32) -> bytes:
    """
    Generate a cryptographically secure random key.
    
    Args:
        key_size: Key size in bytes (default 32 = 256 bits)
    
    Returns:
        Random bytes suitable for AES encryption
    """
    return get_random_bytes(key_size)


def encrypt_aes_gcm(
    plaintext: bytes,
    key: bytes,
    associated_data: bytes = None,
    nonce: bytes = None
) -> tuple:
    """
    Encrypt data using AES-256-GCM with authenticated encryption.
    
    Args:
        plaintext: Data to encrypt
        key: 32-byte encryption key (256-bit)
        associated_data: Optional AAD for authentication
        nonce: Optional nonce (12 bytes recommended). Generated if None.
    
    Returns:
        Tuple of (ciphertext, nonce, tag)
    
    Raises:
        EncryptionError: If encryption fails
    """
    if len(key) != 32:
        raise EncryptionError(f"Key must be 256-bit (32 bytes), got {len(key)} bytes")
    
    if nonce is None:
        nonce = get_random_bytes(12)  # 96-bit nonce (recommended for GCM)
    elif len(nonce) != 12:
        raise EncryptionError(f"Nonce must be 12 bytes, got {len(nonce)}")
    
    try:
        aesgcm = AESGCM(key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, associated_data)
        
        # GCM mode produces ciphertext + authentication tag (last 16 bytes)
        # Split to return separately
        ct = ciphertext[:-16]
        tag = ciphertext[-16:]
        
        return ct, nonce, tag
    except Exception as e:
        raise EncryptionError(f"Encryption failed: {str(e)}")


def decrypt_aes_gcm(
    ciphertext: bytes,
    key: bytes,
    nonce: bytes,
    tag: bytes,
    associated_data: bytes = None
) -> bytes:
    """
    Decrypt data encrypted with AES-256-GCM.
    
    Args:
        ciphertext: Data to decrypt
        key: 32-byte encryption key (must match encryption key)
        nonce: Nonce used during encryption (12 bytes)
        tag: Authentication tag from encryption
        associated_data: Optional AAD (must match encryption AAD)
    
    Returns:
        Decrypted plaintext
    
    Raises:
        AuthenticationError: If authentication tag is invalid
        EncryptionError: If decryption fails
    """
    if len(key) != 32:
        raise EncryptionError(f"Key must be 256-bit (32 bytes), got {len(key)} bytes")
    
    if len(nonce) != 12:
        raise EncryptionError(f"Nonce must be 12 bytes, got {len(nonce)}")
    
    if len(tag) != 16:
        raise EncryptionError(f"Tag must be 16 bytes, got {len(tag)}")
    
    try:
        aesgcm = AESGCM(key)
        # Reconstruct the full ciphertext with tag
        full_ciphertext = ciphertext + tag
        plaintext = aesgcm.decrypt(nonce, full_ciphertext, associated_data)
        return plaintext
    except Exception as e:
        raise AuthenticationError(f"Authentication failed or decryption error: {str(e)}")


def derive_key_from_password(
    password: str,
    salt: bytes = None,
    algorithm: str = 'pbkdf2'
) -> tuple:
    """
    Derive encryption key from password.
    
    Args:
        password: User password
        salt: Optional salt (generated if None)
        algorithm: 'pbkdf2' or 'argon2id'
    
    Returns:
        Tuple of (key, salt)
    """
    from .key_derivation import derive_key_pbkdf2, derive_key_argon2id
    
    if salt is None:
        salt = get_random_bytes(16)
    
    if algorithm == 'pbkdf2':
        key = derive_key_pbkdf2(password, salt)
    elif algorithm == 'argon2id':
        key = derive_key_argon2id(password, salt)
    else:
        raise ValueError(f"Unknown algorithm: {algorithm}")
    
    return key, salt
