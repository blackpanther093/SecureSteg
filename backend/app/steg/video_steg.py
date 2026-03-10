"""
Video steganography using frame-based embedding and codec manipulation.
"""

import numpy as np
import cv2
from typing import Tuple
import os


class VideoSteganography:
    """Video steganography with frame-based LSB embedding."""
    
    @staticmethod
    def embed_lsb(
        video_path: str,
        payload: bytes,
        frame_interval: int = 5
    ) -> Tuple[str, dict]:
        """
        Embed data in video frames using LSB.
        
        Args:
            video_path: Path to input video
            payload: Encrypted payload bytes
            frame_interval: Embed in every N-th frame
        
        Returns:
            Tuple of (output_path, metadata)
        """
        cap = cv2.VideoCapture(video_path)
        
        if not cap.isOpened():
            raise ValueError("Cannot open video file")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Check capacity
        max_capacity = (width * height * 3 * total_frames) // (8 * frame_interval)
        if len(payload) > max_capacity:
            raise ValueError(f"Payload too large for video. Max: {max_capacity} bytes")
        
        # Write output video
        output_path = video_path.replace('.mp4', '_stego.mp4').replace('.avi', '_stego.avi')
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        payload_bits = ''.join(format(byte, '08b') for byte in payload)
        bit_index = 0
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Embed in selected frames
            if frame_count % frame_interval == 0 and bit_index < len(payload_bits):
                frame_flat = frame.flatten()
                
                # Embed bits in LSB
                for i in range(len(frame_flat)):
                    if bit_index >= len(payload_bits):
                        break
                    bit = int(payload_bits[bit_index])
                    frame_flat[i] = (frame_flat[i] & 0xFE) | bit
                    bit_index += 1
                
                frame = frame_flat.reshape(frame.shape)
            
            out.write(frame.astype(np.uint8))
            frame_count += 1
        
        cap.release()
        out.release()
        
        return output_path, {
            "method": "video_lsb",
            "fps": fps,
            "resolution": f"{width}x{height}",
            "total_frames": total_frames,
            "frames_used": (total_frames // frame_interval),
            "payload_bits_embedded": bit_index
        }
    
    @staticmethod
    def extract_lsb(video_path: str, payload_size: int) -> bytes:
        """
        Extract data from video frames.
        
        Args:
            video_path: Path to stego video
            payload_size: Size of embedded payload
        
        Returns:
            Extracted payload bytes
        """
        cap = cv2.VideoCapture(video_path)
        
        payload_bits = []
        frame_count = 0
        
        while len(payload_bits) < (payload_size * 8):
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_flat = frame.flatten()
            
            for i in range(len(frame_flat)):
                if len(payload_bits) >= (payload_size * 8):
                    break
                bit = frame_flat[i] & 0x01
                payload_bits.append(str(bit))
            
            frame_count += 1
        
        cap.release()
        
        # Convert bits to bytes
        payload = bytes(
            int(''.join(payload_bits[i:i+8]), 2) 
            for i in range(0, len(payload_bits) - 7, 8)
        )
        
        return payload
