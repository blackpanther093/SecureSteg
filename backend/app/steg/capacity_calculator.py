"""
Capacity calculator for steganographic embeddings.
Provides realistic capacity estimates based on image characteristics.
"""

import numpy as np
import cv2


class CapacityCalculator:
    """Calculate maximum hideable data capacity."""
    
    @staticmethod
    def calculate_image_capacity(
        image_array: np.ndarray,
        method: str = 'lsb',
        safety_margin: float = 0.8
    ) -> dict:
        """
        Calculate realistic capacity for image steganography.
        
        Args:
            image_array: Image as numpy array
            method: 'lsb', 'dct', 'wavelet', 'multi_layer'
            safety_margin: Safety factor to avoid detectability (0.0-1.0)
        
        Returns:
            Dictionary with capacity metrics
        """
        height, width = image_array.shape[:2]
        total_pixels = height * width
        
        # Calculate theoretical capacity
        if len(image_array.shape) == 3:
            channels = image_array.shape[2]
        else:
            channels = 1
        
        # Analyze image entropy to refine estimates
        if len(image_array.shape) == 3:
            gray = cv2.cvtColor(image_array.astype(np.uint8), cv2.COLOR_RGB2GRAY)
        else:
            gray = image_array.astype(np.uint8)
        
        entropy = CapacityCalculator._calculate_entropy(gray)
        entropy_factor = min(1.0, entropy / 7.0)  # Normalize by max entropy
        
        if method == 'lsb':
            # LSB: 1 bit per channel per pixel
            theoretical_bits = total_pixels * channels * 8
            # Reduce based on noise and safety margin
            practical_bits = int(theoretical_bits * 0.4 * safety_margin * entropy_factor)
        
        elif method == 'multi_layer':
            # Multi-layer LSB with randomization - slightly better
            theoretical_bits = total_pixels * channels * 8
            practical_bits = int(theoretical_bits * 0.5 * safety_margin * entropy_factor)
        
        elif method == 'dct':
            # DCT: more complex, lower capacity but more robust
            practical_bits = int(total_pixels * 0.08 * 8 * safety_margin)
        
        elif method == 'wavelet':
            practical_bits = int(total_pixels * 0.10 * 8 * safety_margin)
        
        else:
            practical_bits = int(total_pixels * 0.3 * channels * 8 * safety_margin)
        
        # Account for overhead (metadata + encryption)
        overhead_bytes = 16 + 12 + 16 + 4  # tag + nonce + padding + size header
        usable_bits = practical_bits - (overhead_bytes * 8)
        
        capacity_bytes = max(0, usable_bits // 8)
        
        return {
            'method': method,
            'image_size': f"{width}x{height}",
            'channels': channels,
            'max_capacity_bytes': capacity_bytes,
            'max_capacity_kb': capacity_bytes / 1024,
            'max_capacity_mb': capacity_bytes / (1024 * 1024),
            'theoretical_bits': practical_bits,
            'entropy': round(entropy, 2),
            'safety_margin': int(safety_margin * 100),
            'estimated_detectability': CapacityCalculator._estimate_detectability(
                capacity_bytes, total_pixels * channels, entropy
            )
        }
    
    @staticmethod
    def _calculate_entropy(image_gray: np.ndarray) -> float:
        """Calculate Shannon entropy of image."""
        hist, _ = np.histogram(image_gray.flatten(), 256, [0, 256])
        hist = hist[hist > 0]
        hist = hist / len(image_gray.flatten())
        entropy = -np.sum(hist * np.log2(hist))
        return entropy
    
    @staticmethod
    def _estimate_detectability(
        hidden_bytes: int,
        total_channels: int,
        entropy: float
    ) -> str:
        """
        Estimate detection risk level.
        
        Returns: 'VERY LOW', 'LOW', 'MEDIUM', 'HIGH', 'VERY HIGH'
        """
        if total_channels == 0:
            return 'VERY HIGH'
        
        embedding_density = (hidden_bytes * 8) / total_channels
        
        # Factor in entropy - high entropy images are safer
        entropy_factor = entropy / 7.0
        adjusted_density = embedding_density / max(entropy_factor, 0.5)
        
        if adjusted_density < 0.001:
            return 'VERY LOW'
        elif adjusted_density < 0.01:
            return 'LOW'
        elif adjusted_density < 0.05:
            return 'MEDIUM'
        elif adjusted_density < 0.15:
            return 'HIGH'
        else:
            return 'VERY HIGH'
    
    @staticmethod
    def can_fit_file(
        image_array: np.ndarray,
        file_size: int,
        method: str = 'lsb'
    ) -> dict:
        """
        Check if file can be hidden in image.
        
        Args:
            image_array: Image array
            file_size: Size of file to hide in bytes
            method: Embedding method
        
        Returns:
            Dictionary with fit analysis
        """
        capacity_info = CapacityCalculator.calculate_image_capacity(
            image_array, method
        )
        
        can_fit = file_size <= capacity_info['max_capacity_bytes']
        
        return {
            'can_fit': can_fit,
            'file_size_bytes': file_size,
            'file_size_kb': file_size / 1024,
            'max_capacity_bytes': capacity_info['max_capacity_bytes'],
            'available_space': max(0, capacity_info['max_capacity_bytes'] - file_size),
            'utilization': f"{(file_size / capacity_info['max_capacity_bytes'] * 100):.1f}%",
            'detectability': capacity_info['estimated_detectability'],
            'recommendation': CapacityCalculator._get_recommendation(
                file_size, capacity_info['max_capacity_bytes']
            )
        }
    
    @staticmethod
    def _get_recommendation(file_size: int, capacity: int) -> str:
        """Get recommendation based on file size vs capacity."""
        if file_size > capacity:
            return "File too large - cannot hide in this image"
        elif file_size > capacity * 0.8:
            return "Risky - near capacity limit, high detection probability"
        elif file_size > capacity * 0.5:
            return "Caution - moderate detectability risk"
        else:
            return "Safe - low detection risk"
