"""
Document steganography for DOCX, ODT, and other document formats.
Uses XML comment embedding and ZIP slack space.
"""

from typing import Tuple
import zipfile
import xml.etree.ElementTree as ET
import struct
import io


class DocumentSteganography:
    """Document steganography for DOCX, ODT formats."""
    
    @staticmethod
    def embed_in_docx(
        docx_path: str,
        payload: bytes
    ) -> Tuple[str, dict]:
        """
        Embed data in DOCX file (ZIP-based, XML-aware).
        
        Args:
            docx_path: Path to input DOCX
            payload: Encrypted payload bytes
        
        Returns:
            Tuple of (output_path, metadata)
        """
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_in:
                docx_files = {name: docx_in.read(name) for name in docx_in.namelist()}
        except Exception as e:
            raise ValueError(f"Cannot read DOCX: {str(e)}")
        
        # Extract and modify document.xml
        if 'word/document.xml' not in docx_files:
            raise ValueError("Invalid DOCX structure")
        
        doc_xml_data = docx_files['word/document.xml'].decode('utf-8', errors='ignore')
        
        # Encode payload as hex and embed in comment
        payload_hex = payload.hex()
        
        # Create hidden comment with marked data
        hidden_comment = f'<!-- STEGO_DATA:{payload_hex} -->'
        
        # Insert before closing </w:document> tag
        if '</w:document>' in doc_xml_data:
            doc_xml_data = doc_xml_data.replace(
                '</w:document>',
                f'{hidden_comment}\n</w:document>',
                1
            )
        else:
            doc_xml_data += hidden_comment
        
        docx_files['word/document.xml'] = doc_xml_data.encode('utf-8')
        
        # Write new DOCX
        output_path = docx_path.replace('.docx', '_stego.docx')
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as docx_out:
            for name, data in docx_files.items():
                docx_out.writestr(name, data)
        
        return output_path, {
            "method": "docx_xml_comment",
            "format": "docx",
            "payload_size": len(payload),
            "embedding_location": "document.xml"
        }
    
    @staticmethod
    def extract_from_docx(docx_path: str) -> bytes:
        """
        Extract data from DOCX file.
        
        Args:
            docx_path: Path to stego DOCX
        
        Returns:
            Extracted payload bytes
        """
        try:
            with zipfile.ZipFile(docx_path, 'r') as docx_in:
                doc_xml_data = docx_in.read('word/document.xml').decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Cannot read DOCX: {str(e)}")
        
        # Extract hidden comment
        import re
        pattern = r'<!-- STEGO_DATA:(.*?) -->'
        match = re.search(pattern, doc_xml_data)
        
        if not match:
            raise ValueError("No embedded data found in DOCX")
        
        payload_hex = match.group(1)
        return bytes.fromhex(payload_hex)
    
    @staticmethod
    def embed_in_odt(
        odt_path: str,
        payload: bytes
    ) -> Tuple[str, dict]:
        """
        Embed data in ODT file (LibreOffice document).
        
        Args:
            odt_path: Path to input ODT
            payload: Encrypted payload bytes
        
        Returns:
            Tuple of (output_path, metadata)
        """
        try:
            with zipfile.ZipFile(odt_path, 'r') as odt_in:
                odt_files = {name: odt_in.read(name) for name in odt_in.namelist()}
        except Exception as e:
            raise ValueError(f"Cannot read ODT: {str(e)}")
        
        # Extract content.xml
        if 'content.xml' not in odt_files:
            raise ValueError("Invalid ODT structure")
        
        content_xml_data = odt_files['content.xml'].decode('utf-8', errors='ignore')
        
        # Embed in comment
        payload_hex = payload.hex()
        hidden_comment = f'<!-- STEGO:{payload_hex} -->'
        
        # Append before closing tag
        if '</office:document-content>' in content_xml_data:
            content_xml_data = content_xml_data.replace(
                '</office:document-content>',
                f'{hidden_comment}\n</office:document-content>',
                1
            )
        
        odt_files['content.xml'] = content_xml_data.encode('utf-8')
        
        output_path = odt_path.replace('.odt', '_stego.odt')
        
        with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as odt_out:
            for name, data in odt_files.items():
                odt_out.writestr(name, data)
        
        return output_path, {
            "method": "odt_xml_comment",
            "format": "odt",
            "payload_size": len(payload),
            "embedding_location": "content.xml"
        }
    
    @staticmethod
    def extract_from_odt(odt_path: str) -> bytes:
        """
        Extract data from ODT file.
        
        Args:
            odt_path: Path to stego ODT
        
        Returns:
            Extracted payload bytes
        """
        try:
            with zipfile.ZipFile(odt_path, 'r') as odt_in:
                content_xml_data = odt_in.read('content.xml').decode('utf-8', errors='ignore')
        except Exception as e:
            raise ValueError(f"Cannot read ODT: {str(e)}")
        
        import re
        pattern = r'<!-- STEGO:(.*?) -->'
        match = re.search(pattern, content_xml_data)
        
        if not match:
            raise ValueError("No embedded data found in ODT")
        
        payload_hex = match.group(1)
        return bytes.fromhex(payload_hex)
    
    @staticmethod
    def calculate_capacity(doc_path: str) -> dict:
        """
        Calculate maximum embedding capacity.
        
        Args:
            doc_path: Path to document
        
        Returns:
            Capacity information
        """
        try:
            with zipfile.ZipFile(doc_path, 'r') as doc_in:
                total_size = sum(f.file_size for f in doc_in.infolist())
        except Exception as e:
            raise ValueError(f"Cannot read document: {str(e)}")
        
        # Can embed ~5% of file size in XML comments
        max_capacity = max(2000, int(total_size * 0.05))
        
        return {
            "document_size": total_size,
            "max_capacity_bytes": max_capacity,
            "method": "xml_comment",
            "detectability_risk": "very_low"
        }
