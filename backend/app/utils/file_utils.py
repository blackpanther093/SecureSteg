"""
Utility functions for file handling, validation, and metadata management.
"""

import os
import mimetypes
from pathlib import Path
from typing import Tuple, Optional
import hashlib


class FileValidator:
    """Validate files for steganography operations."""
    
    ALLOWED_IMAGE_FORMATS = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.webp'}
    ALLOWED_AUDIO_FORMATS = {'.wav', '.mp3', '.flac', '.aac'}
    ALLOWED_VIDEO_FORMATS = {'.mp4', '.mkv', '.avi', '.mov'}
    ALLOWED_CAPACITY_FORMATS = {'.pdf', '.txt', '.zip', '.docx', '.json'}
    
    MAX_FILE_SIZE_MB = 100  # Maximum upload size
    
    @staticmethod
    def validate_image(file_path: str) -> Tuple[bool, str]:
        """Validate image file."""
        if not os.path.exists(file_path):
            return False, "File not found"
        
        ext = Path(file_path).suffix.lower()
        if ext not in FileValidator.ALLOWED_IMAGE_FORMATS:
            return False, f"Unsupported image format. Allowed: {', '.join(FileValidator.ALLOWED_IMAGE_FORMATS)}"
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > FileValidator.MAX_FILE_SIZE_MB:
            return False, f"File too large. Maximum: {FileValidator.MAX_FILE_SIZE_MB}MB"
        
        return True, "Valid"
    
    @staticmethod
    def validate_payload_file(file_path: str) -> Tuple[bool, str]:
        """Validate payload/capacity file."""
        if not os.path.exists(file_path):
            return False, "File not found"
        
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 10:  # Max 10MB payload
            return False, "Payload file too large. Maximum: 10MB"
        
        return True, "Valid"


class FileProcessor:
    """Process and prepare files for steganography."""
    
    @staticmethod
    def calculate_file_hash(file_path: str) -> str:
        """Calculate SHA-256 hash of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def read_file_binary(file_path: str) -> bytes:
        """Read file as binary."""
        with open(file_path, 'rb') as f:
            return f.read()
    
    @staticmethod
    def write_file_binary(file_path: str, data: bytes) -> None:
        """Write binary data to file."""
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(data)


class SecurityUtils:
    """Security-related utilities."""
    
    @staticmethod
    def secure_cleanup(file_path: str, passes: int = 3) -> None:
        """
        Securely delete file by overwriting with random data.
        
        Args:
            file_path: Path to file to delete
            passes: Number of overwrite passes
        """
        import secrets
        
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'ba+', buffering=0) as f:
                for _ in range(passes):
                    f.seek(0)
                    f.write(secrets.token_bytes(file_size))
                    f.flush()
            
            os.remove(file_path)
        except Exception:
            # Fallback to regular deletion if secure delete fails
            if os.path.exists(file_path):
                os.remove(file_path)
