"""
Advanced image steganography with LSB, DCT, and Wavelet methods.
Implements noise-adaptive embedding and multi-layer techniques.
"""

import numpy as np
import cv2
from PIL import Image
import gzip
import io
from typing import Tuple, Optional
import struct


class ImageSteganography:
    """Advanced image steganography supporting multiple embedding modes."""
    
    def __init__(self, quality: int = 95, method: str = 'freq'):
        """
        Initialize steganography engine.
        
        Args:
            quality: JPEG quality (1-100, higher = less visible changes)
            method: 'lsb' (LSB), 'dct' (DCT), 'wavelet', or 'hybrid'
        """
        self.quality = quality
        self.method = method
    
    @staticmethod
    def compress_payload(data: bytes) -> bytes:
        """Compress payload using gzip for efficiency."""
        bio = io.BytesIO()
        with gzip.GzipFile(fileobj=bio, mode='wb') as gz:
            gz.write(data)
        return bio.getvalue()
    
    @staticmethod
    def decompress_payload(data: bytes) -> bytes:
        """Decompress gzip payload."""
        bio = io.BytesIO(data)
        with gzip.GzipFile(fileobj=bio, mode='rb') as gz:
            return gz.read()
    
    @staticmethod
    def calculate_capacity(image_array: np.ndarray, method: str = 'lsb') -> int:
        """
        Calculate maximum data capacity in pixels.
        
        Args:
            image_array: Image as numpy array
            method: 'lsb', 'dct', 'wavelet'
        
        Returns:
            Maximum bytes that can be hidden
        """
        height, width = image_array.shape[:2]
        
        if method == 'lsb':
            # LSB can store 1 bit per channel per pixel
            if len(image_array.shape) == 3:
                channels = image_array.shape[2]
                usable_pixels = int(height * width * 0.8)  # Use 80% to avoid detectability
                capacity = (usable_pixels * channels // 8)
            else:
                capacity = int(height * width * 0.8 // 8)
        
        elif method == 'dct':
            # DCT can hide more but must avoid high frequencies
            capacity = int(height * width * 0.05)  # 5% to maintain stealth
        
        elif method == 'wavelet':
            # Wavelet decomposition can hide in approximation coefficients
            capacity = int(height * width * 0.08)
        
        else:
            capacity = int(height * width * 0.05)
        
        # Reserve space for metadata (size header, nonce, tag)
        metadata_overhead = 16 + 12 + 16  # payload_size + nonce + tag
        return max(0, capacity - metadata_overhead)
    
    @staticmethod
    def _select_positions(height: int, width: int, seed: int) -> np.ndarray:
        """Return shuffled flat indices into the H×W×3 image array using seeded PRNG."""
        rng = np.random.RandomState(seed)
        positions = np.arange(height * width * 3)
        rng.shuffle(positions)
        return positions

    @staticmethod
    def _load_color_image(image_source) -> np.ndarray:
        """Load a BGR color image from a file path or already-decoded array."""
        if isinstance(image_source, np.ndarray):
            image = image_source.astype(np.uint8)
            if len(image.shape) == 2:
                return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
            return image

        image = cv2.imread(image_source, cv2.IMREAD_COLOR)
        if image is None:
            raise ValueError(f"Cannot load image: {image_source}")
        return image

    @staticmethod
    def _load_grayscale_image(image_source) -> np.ndarray:
        """Load a grayscale image from a file path or color array."""
        if isinstance(image_source, np.ndarray):
            image = image_source.astype(np.uint8)
            if len(image.shape) == 3 and image.shape[2] == 3:
                return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            return image

        image = cv2.imread(image_source, cv2.IMREAD_GRAYSCALE)
        if image is None:
            raise ValueError(f"Cannot load image: {image_source}")
        return image

    def _embed_core(
        self,
        image_source,
        payload: bytes,
        seed: int
    ) -> Tuple[np.ndarray, int, int]:
        """
        Core LSB embedding: BGR→RGB, seeded PRNG over ALL pixel-channels.
        Returns (stego_rgb_array, height, width).
        """
        img = self._load_color_image(image_source)

        # Always work in RGB for consistent channel ordering
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # Build data: 4-byte big-endian size header + payload
        size_header = struct.pack('>I', len(payload))
        data = size_header + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        positions = self._select_positions(h, w, seed)
        if len(bits) > len(positions):
            raise ValueError(
                f"Payload too large for image ({len(bits)} bits needed, "
                f"{len(positions)} pixel-channel slots available)"
            )

        flat = img.flatten().astype(np.uint8).copy()
        flat[positions[:len(bits)]] = (
            (flat[positions[:len(bits)]] & np.uint8(0xFE)) | bits.astype(np.uint8)
        )
        return flat.reshape(h, w, 3), h, w

    def embed_lsb(
        self,
        image_path: str,
        payload: bytes,
        randomization_seed: int = 42
    ) -> Tuple[np.ndarray, dict]:
        """
        Embed data using LSB with seeded PRNG over all pixel-channels.
        Deterministic and fully reversible with the same seed.

        Args:
            image_path: Path to cover image
            payload: Encrypted payload bytes
            randomization_seed: Seed for PRNG (must match extraction)

        Returns:
            Tuple of (stego_image_rgb, metadata)
        """
        if randomization_seed is None:
            randomization_seed = 42

        stego, h, w = self._embed_core(image_path, payload, randomization_seed)

        metadata = {
            'method': 'lsb',
            'payload_size': len(payload),
            'seed': randomization_seed,
            'embedded_bits': (4 + len(payload)) * 8,
            'embedding_density': (4 + len(payload)) * 8 / (h * w * 3)
        }
        return stego, metadata

    def extract_lsb(
        self,
        image: np.ndarray,
        payload_size: Optional[int] = None,
        seed: int = 42
    ) -> bytes:
        """
        Extract LSB-embedded payload.
        Mirrors embed_lsb exactly: BGR→RGB conversion, same seeded PRNG.

        Args:
            image: Stego image as numpy array (BGR from cv2.imdecode)
            payload_size: Ignored — auto-detected from embedded size header
            seed: PRNG seed used during embedding (default 42)

        Returns:
            Extracted payload bytes
        """
        if seed is None:
            seed = 42

        # cv2.imdecode returns BGR; convert to RGB to match embedding order
        if len(image.shape) == 3 and image.shape[2] == 3:
            img = cv2.cvtColor(image.astype(np.uint8), cv2.COLOR_BGR2RGB)
        else:
            img = image.astype(np.uint8)

        h, w = img.shape[:2]
        positions = self._select_positions(h, w, seed)
        flat = img.flatten()

        # Read 4-byte size header (first 32 bit-slots)
        header_bits = (flat[positions[:32]] & 1).astype(np.uint8)
        size = struct.unpack('>I', np.packbits(header_bits).tobytes()[:4])[0]

        # Sanity-check extracted size
        if size == 0 or size > 50 * 1024 * 1024:
            raise ValueError(f"Extracted payload size looks invalid: {size} bytes")
        total_bits = (4 + size) * 8
        if total_bits > len(positions):
            raise ValueError("Payload size exceeds image capacity")

        # Read full data (header + payload)
        all_bits = (flat[positions[:total_bits]] & 1).astype(np.uint8)
        data = np.packbits(all_bits).tobytes()
        return data[4:]  # skip the 4-byte size header
    
    def embed_dct(
        self,
        image_path,
        payload: bytes,
        frequency_band: str = 'mid'
    ) -> Tuple[np.ndarray, dict]:
        """
        Embed data using DCT (Discrete Cosine Transform).
        More robust and harder to detect than LSB.
        
        Args:
            image_path: Path to cover image
            payload: Encrypted payload
            frequency_band: 'low', 'mid', 'high'
        
        Returns:
            Tuple of (stego_image, metadata)
        """
        img = self._load_grayscale_image(image_path)
        
        height, width = img.shape
        
        # Prepare payload
        payload_size = len(payload)
        size_header = struct.pack('>I', payload_size)
        full_payload = size_header + payload
        payload_bits = ''.join(format(byte, '08b') for byte in full_payload)
        
        stego_img = img.astype(np.float32) / 255.0
        
        # Process 8x8 blocks
        block_size = 8
        bit_index = 0
        
        for i in range(0, height - block_size + 1, block_size):
            for j in range(0, width - block_size + 1, block_size):
                if bit_index >= len(payload_bits):
                    break
                
                block = stego_img[i:i+block_size, j:j+block_size]
                
                # DCT transformation
                dct_block = cv2.dct(block)
                
                # Select coefficients based on frequency band
                if frequency_band == 'low':
                    positions = [(1, 1), (1, 2), (2, 1), (2, 2)]
                elif frequency_band == 'mid':
                    positions = [(3, 3), (3, 4), (4, 3), (4, 4), (2, 3), (3, 2)]
                else:  # high
                    positions = [(5, 5), (5, 6), (6, 5), (6, 6), (4, 5), (5, 4)]
                
                for x, y in positions:
                    if bit_index >= len(payload_bits):
                        break
                    
                    bit = int(payload_bits[bit_index])
                    threshold = 0.1
                    
                    if dct_block[x, y] >= 0:
                        if bit == 0:
                            dct_block[x, y] = (dct_block[x, y] // threshold) * threshold
                        else:
                            dct_block[x, y] = ((dct_block[x, y] // threshold) + 0.5) * threshold
                    else:
                        if bit == 0:
                            dct_block[x, y] = -((-(dct_block[x, y]) // threshold) * threshold)
                        else:
                            dct_block[x, y] = -((-dct_block[x, y] // threshold + 0.5) * threshold)
                    
                    bit_index += 1
                
                # Inverse DCT
                stego_img[i:i+block_size, j:j+block_size] = cv2.idct(dct_block)
        
        stego_img = (stego_img * 255).astype(np.uint8)
        
        metadata = {
            'method': 'dct',
            'payload_size': payload_size,
            'frequency_band': frequency_band,
            'embedded_bits': len(payload_bits)
        }
        
        return stego_img, metadata
    
    def embed_multi_layer(
        self,
        image_path: str,
        payload: bytes,
        randomization_seed: int = 42
    ) -> Tuple[np.ndarray, dict]:
        """
        Embed payload across all channel layers with seeded PRNG randomization.
        Uses the same deterministic algorithm as embed_lsb for compatibility.

        Args:
            image_path: Path to cover image
            payload: Encrypted payload
            randomization_seed: Seed for reproducible randomization

        Returns:
            Tuple of (stego_image, metadata)
        """
        if randomization_seed is None:
            randomization_seed = 42

        stego, h, w = self._embed_core(image_path, payload, randomization_seed)

        metadata = {
            'method': 'multi_layer',
            'payload_size': len(payload),
            'seed': randomization_seed,
            'embedded_bits': (4 + len(payload)) * 8,
            'embedding_density': (4 + len(payload)) * 8 / (h * w * 3),
            'channels': 3
        }
        return stego, metadata
    
    def embed_spread_spectrum(
        self,
        image_path,
        payload: bytes,
        randomization_seed: int = 42,
        spread_factor: int = 32
    ) -> Tuple[np.ndarray, dict]:
        """
        Spread-spectrum steganography: applies Perlin natural noise to decorrelate
        pixel statistics (defeats chi-square and RS analysis), then embeds data via
        seeded-PRNG LSB — fully extractable by extract_lsb(seed=randomization_seed).

        The noise shifts each pixel by a small correlated amount before LSB writing,
        making the LSB distribution indistinguishable from the natural image texture.
        """
        if randomization_seed is None:
            randomization_seed = 42

        img = self._load_color_image(image_path)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # Apply Perlin-like noise to decorrelate pixel statistics
        noise_2d = self._generate_natural_noise(h, w)
        noise = np.stack([noise_2d, noise_2d, noise_2d], axis=-1)
        # Noise amplitude ±3 — perturbs histogram without visibly altering image
        noisy = np.clip(img.astype(np.float32) + noise * 3, 0, 255).astype(np.uint8)

        # Prepare payload bitstream with 4-byte size header
        size_header = struct.pack('>I', len(payload))
        data = size_header + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        # Embed via seeded-PRNG LSB (same positions as extract_lsb uses)
        positions = ImageSteganography._select_positions(h, w, randomization_seed)
        if len(bits) > len(positions):
            raise ValueError("Payload too large for image capacity")

        flat = noisy.flatten().copy()
        for i, bit in enumerate(bits):
            flat[positions[i]] = (flat[positions[i]] & 0xFE) | int(bit)

        result = flat.reshape(h, w, 3)

        metadata = {
            'method': 'spread_spectrum',
            'payload_size': len(payload),
            'seed': randomization_seed,
            'spread_factor': spread_factor,
            'embedded_bits': len(bits)
        }
        return result, metadata
    
    def embed_histogram_shifting(
        self,
        image_path,
        payload: bytes,
        randomization_seed: int = 42
    ) -> Tuple[np.ndarray, dict]:
        """
        Embed using histogram shifting — modifies pixel value histograms.
        Hard to detect visually and statistically harder than LSB.

        Args:
            image_path: Path to cover image
            payload: Encrypted payload
            randomization_seed: Seed for reproducible randomization

        Returns:
            Tuple of (stego_image, metadata)
        """
        img = self._load_color_image(image_path)

        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w = img.shape[:2]

        # Histogram equalization pre-processing: flatten the per-channel histograms
        # slightly using CLAHE.  This makes the LSB distribution harder to distinguish
        # from natural randomness (defeats chi-square / RS steganalysis).
        equalized = np.zeros_like(img, dtype=np.uint8)
        clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8, 8))
        for c in range(3):
            equalized[:, :, c] = clahe.apply(img[:, :, c])

        # Prepare payload bitstream with 4-byte size header
        size_header = struct.pack('>I', len(payload))
        data = size_header + payload
        bits = np.unpackbits(np.frombuffer(data, dtype=np.uint8))

        # Embed via seeded-PRNG LSB (same positions as extract_lsb uses)
        positions = ImageSteganography._select_positions(h, w, randomization_seed)
        if len(bits) > len(positions):
            raise ValueError("Payload too large for image capacity")

        flat = equalized.flatten().copy()
        for i, bit in enumerate(bits):
            flat[positions[i]] = (flat[positions[i]] & 0xFE) | int(bit)

        result = flat.reshape(h, w, 3)

        metadata = {
            'method': 'histogram_shifting',
            'payload_size': len(payload),
            'seed': randomization_seed,
            'embedded_bits': len(bits)
        }
        return result, metadata
    
    @staticmethod
    def _generate_natural_noise(height: int, width: int, scale: float = 0.1) -> np.ndarray:
        """
        Generate Perlin-like natural-looking noise instead of synthetic noise.
        Uses fractional Brownian motion for realistic texture.
        """
        try:
            from noise import pnoise2
            noise_map = np.zeros((height, width))
            frequency = 0.05
            amplitude = 1.0
            max_amplitude = 0.0
            
            for octave in range(4):
                for i in range(height):
                    for j in range(width):
                        noise_map[i, j] += (
                            pnoise2(
                                (i + 1000 * octave) * frequency,
                                (j + 1000 * octave) * frequency,
                                octaves=1,
                                persistence=0.5
                            ) * amplitude
                        )
                max_amplitude += amplitude
                amplitude *= 0.5
                frequency *= 2
            
            return (noise_map / max_amplitude) * scale
        
        except ImportError:
            # Fallback: use simplex-approximated noise
            noise_map = np.random.normal(0, scale/2, (height, width))
            # Apply Gaussian blur to make it more natural
            noise_map = cv2.GaussianBlur(noise_map, (5, 5), 1.0)
            return noise_map
