"""
PDF steganography using stream manipulation and metadata embedding.
"""

from typing import Tuple
import struct


class PDFSteganography:
    """PDF steganography with stream-based embedding."""
    
    @staticmethod
    def embed_in_metadata(
        pdf_path: str,
        payload: bytes
    ) -> Tuple[str, dict]:
        """
        Embed data in PDF metadata streams.
        
        Args:
            pdf_path: Path to input PDF
            payload: Encrypted payload bytes
        
        Returns:
            Tuple of (output_path, metadata)
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_data = bytearray(f.read())
        except Exception as e:
            raise ValueError(f"Cannot read PDF: {str(e)}")
        
        # Find xref section
        xref_pos = pdf_data.rfind(b'xref')
        if xref_pos == -1:
            raise ValueError("Invalid or corrupted PDF structure")
        
        # Prepare payload with size header (4 bytes)
        payload_with_header = struct.pack('>I', len(payload)) + payload
        
        # Find suitable location to embed (in whitespace after objects)
        old_size = len(pdf_data)
        
        # Embed by extending object streams
        # Find all object definitions
        import re
        obj_pattern = rb'\n(\d+) 0 obj\s'
        
        embedded_size = 0
        for match in re.finditer(obj_pattern, pdf_data):
            if embedded_size >= len(payload_with_header):
                break
            
            obj_start = match.end()
            obj_end = pdf_data.find(b'endobj', obj_start)
            
            if obj_end > obj_start:
                # Add hidden stream data before endobj
                chunk_size = min(256, len(payload_with_header) - embedded_size)
                chunk = payload_with_header[embedded_size:embedded_size + chunk_size]
                
                # Prepend with marker byte
                pdf_data.insert(obj_end, b'\n% STEGO:' + chunk)
                embedded_size += chunk_size
        
        # Update file size in trailer
        output_path = pdf_path.replace('.pdf', '_stego.pdf')
        
        with open(output_path, 'wb') as f:
            f.write(pdf_data)
        
        return output_path, {
            "method": "pdf_metadata",
            "original_size": old_size,
            "new_size": len(pdf_data),
            "payload_size": len(payload),
            "embedded_bytes": embedded_size
        }
    
    @staticmethod
    def extract_from_metadata(pdf_path: str) -> bytes:
        """
        Extract data from PDF metadata.
        
        Args:
            pdf_path: Path to stego PDF
        
        Returns:
            Extracted payload bytes
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
        except Exception as e:
            raise ValueError(f"Cannot read PDF: {str(e)}")
        
        # Find all STEGO markers
        import re
        pattern = rb'% STEGO:(.*?)(?=\n|$)'
        
        extracted = b''
        for match in re.finditer(pattern, pdf_data):
            extracted += match.group(1)
        
        if not extracted:
            raise ValueError("No embedded data found in PDF")
        
        # Extract size header
        if len(extracted) < 4:
            raise ValueError("Invalid embedded data format")
        
        payload_size = struct.unpack('>I', extracted[:4])[0]
        return extracted[4:4 + payload_size]
    
    @staticmethod
    def calculate_capacity(pdf_path: str) -> dict:
        """
        Calculate maximum embedding capacity.
        
        Args:
            pdf_path: Path to PDF
        
        Returns:
            Capacity information
        """
        try:
            with open(pdf_path, 'rb') as f:
                pdf_data = f.read()
        except Exception as e:
            raise ValueError(f"Cannot read PDF: {str(e)}")
        
        # Approximate capacity: ~1-2% of PDF size for metadata
        pdf_size = len(pdf_data)
        max_capacity = max(1000, int(pdf_size * 0.015))
        
        return {
            "pdf_size": pdf_size,
            "max_capacity_bytes": max_capacity,
            "method": "metadata_stream",
            "detectability_risk": "low"
        }
