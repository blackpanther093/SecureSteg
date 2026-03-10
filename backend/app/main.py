"""
Main FastAPI application for SecureSteg platform.
Implements all core endpoints with security middleware.
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.proxies import ProxyHeadersMiddleware
from typing import Optional
import os
import uuid
import json
from datetime import datetime
import tempfile
import time
import hashlib
import cv2
import numpy as np
from PIL import Image
import io

# Import modules
from app.crypto import (
    encrypt_aes_gcm, decrypt_aes_gcm, generate_random_key,
    derive_key_from_password, secure_random_bytes, generate_recovery_key
)
from app.payload_structure import PayloadMetadata, PayloadStructure, ExpirationMode, WatermarkMode, EmbeddingMethod
from app.steg import ImageSteganography, CapacityCalculator
from app.steg.audio_steg import AudioSteganography
from app.steg.video_steg import VideoSteganography
from app.steg.pdf_steg import PDFSteganography
from app.steg.document_steg import DocumentSteganography
from app.detection import SteganalysisDetector
from app.utils import FileValidator, FileProcessor, SecurityUtils
import mimetypes

# Initialize FastAPI app
app = FastAPI(
    title="SecureSteg - Universal Steganography Platform",
    description="High-security steganography with encrypted hidden communication",
    version="1.0.0"
)

# Security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*", 
        "http://localhost:3000", 
        "http://localhost:5173", 
        "http://localhost:5174",
        "https://securesteg-frontend.onrender.com",
        "https://*.onrender.com"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Metadata", "X-Session-ID"],
)

allowed_hosts = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")
if allowed_hosts == ["*"]:
    allowed_hosts = ["*"]
else:
    allowed_hosts = [h.strip() for h in allowed_hosts] + ["localhost", "127.0.0.1", "*.localhost"]

app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)
# app.add_middleware(ProxyHeadersMiddleware)
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=allowed_hosts
)

DECODE_STATE: dict[str, int] = {}
OUTPUT_CACHE: dict[str, dict] = {}
OUTPUT_TTL_SECONDS = 15 * 60


def _prune_output_cache() -> None:
    cutoff = time.time() - OUTPUT_TTL_SECONDS
    expired_keys = [key for key, value in OUTPUT_CACHE.items() if value.get("created_at", 0) < cutoff]
    for key in expired_keys:
        OUTPUT_CACHE.pop(key, None)


def _cache_output(session_id: str, data: bytes, filename: str, media_type: str) -> None:
    _prune_output_cache()
    OUTPUT_CACHE[session_id] = {
        "data": data,
        "filename": filename,
        "media_type": media_type,
        "created_at": time.time(),
    }


def _temp_file_from_bytes(data: bytes, suffix: str) -> str:
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        temp_file.write(data)
        temp_file.flush()
        return temp_file.name
    finally:
        temp_file.close()


def _get_decode_count(payload_hash: str) -> int:
    value = DECODE_STATE.get(payload_hash, 0)
    try:
        return int(value)
    except Exception:
        return 0


def _increment_decode_count(payload_hash: str) -> int:
    current = int(DECODE_STATE.get(payload_hash, 0))
    DECODE_STATE[payload_hash] = current + 1
    return current + 1


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "SecureSteg",
        "status": "active",
        "version": "1.0.0",
        "endpoints": {
            "embed": "POST /embed",
            "extract": "POST /extract",
            "detect": "POST /detect",
            "generate_key": "POST /generate-key",
            "capacity": "POST /capacity",
            "health": "GET /health",
            "status_page": "GET /status"
        }
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    _prune_output_cache()
    return {
        "status": "healthy",
        "service": "SecureSteg",
        "timestamp": datetime.now().isoformat(),
        "cached_outputs": len(OUTPUT_CACHE),
        "tracked_decode_limits": len(DECODE_STATE),
    }


@app.get("/status", response_class=HTMLResponse)
async def status_page():
    """Render-friendly HTML status page."""
    _prune_output_cache()
    html = f"""
        <!DOCTYPE html>
        <html lang='en'>
            <head>
                <meta charset='utf-8' />
                <meta name='viewport' content='width=device-width, initial-scale=1' />
                <title>SecureSteg Backend Status</title>
                <style>
                    :root {{
                        color-scheme: dark light;
                        --bg: #0f1718;
                        --bg2: #142427;
                        --panel: rgba(15, 24, 26, 0.84);
                        --text: #eef5f0;
                        --muted: #9cb0ac;
                        --accent: #5bd8c5;
                        --ok: #6bdb9d;
                        --border: rgba(255,255,255,0.1);
                    }}
                    body {{
                        margin: 0;
                        min-height: 100vh;
                        display: grid;
                        place-items: center;
                        background:
                            radial-gradient(circle at top left, rgba(91,216,197,0.16), transparent 24%),
                            linear-gradient(145deg, var(--bg), var(--bg2));
                        color: var(--text);
                        font-family: Segoe UI, Inter, sans-serif;
                    }}
                    .card {{
                        width: min(720px, calc(100vw - 32px));
                        border-radius: 24px;
                        padding: 28px;
                        background: var(--panel);
                        border: 1px solid var(--border);
                        box-shadow: 0 24px 60px rgba(0,0,0,0.28);
                    }}
                    .pill {{
                        display: inline-flex;
                        padding: 8px 12px;
                        border-radius: 999px;
                        background: rgba(107,219,157,0.12);
                        color: var(--ok);
                        font-size: 12px;
                        text-transform: uppercase;
                        letter-spacing: .12em;
                    }}
                    .grid {{
                        display: grid;
                        gap: 12px;
                        grid-template-columns: repeat(2, minmax(0, 1fr));
                        margin-top: 20px;
                    }}
                    .metric {{
                        border-radius: 16px;
                        padding: 16px;
                        background: rgba(255,255,255,0.04);
                        border: 1px solid var(--border);
                    }}
                    .label {{ color: var(--muted); font-size: 13px; margin-bottom: 8px; }}
                    .value {{ font-size: 20px; font-weight: 700; }}
                </style>
            </head>
            <body>
                <main class='card'>
                    <div class='pill'>Backend Status</div>
                    <h1>SecureSteg API is operating normally.</h1>
                    <p style='color: var(--muted); line-height: 1.7;'>This page is designed for deployment environments such as Render so you can confirm liveness, output-cache activity, and decode-limit tracking from a browser without calling JSON endpoints directly.</p>
                    <div class='grid'>
                        <div class='metric'><div class='label'>Service</div><div class='value'>SecureSteg</div></div>
                        <div class='metric'><div class='label'>Status</div><div class='value'>Healthy</div></div>
                        <div class='metric'><div class='label'>Cached Outputs</div><div class='value'>{len(OUTPUT_CACHE)}</div></div>
                        <div class='metric'><div class='label'>Tracked Decode Limits</div><div class='value'>{len(DECODE_STATE)}</div></div>
                    </div>
                    <p style='color: var(--muted); margin-top: 18px;'>Updated: {datetime.now().isoformat()}</p>
                </main>
            </body>
        </html>
    """
    return HTMLResponse(content=html)


@app.post("/capacity")
async def calculate_capacity(file: UploadFile = File(...)):
    """
    Calculate maximum data capacity for any media format.
    
    Returns capacity info and detectability assessment for:
    - Images: All formats (PNG, JPG, BMP, etc.)
    - Audio: WAV, MP3, FLAC, OGG
    - Video: MP4, AVI, MKV, MOV
    - PDF: All PDFs
    - Documents: DOCX, ODT
    """
    try:
        contents = await file.read()
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        # Route based on file type
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']:
            # IMAGE capacity
            image_array = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
            if image_array is None:
                raise HTTPException(status_code=400, detail="Invalid image file")
            
            capacities = {}
            for method in ['lsb', 'multi_layer', 'dct']:
                try:
                    cap_info = CapacityCalculator.calculate_image_capacity(image_array, method)
                    capacities[method] = cap_info
                except Exception as e:
                    capacities[method] = {"error": str(e)}
            
            return {
                "status": "success",
                "format": "image",
                "image_dimensions": f"{image_array.shape[1]}x{image_array.shape[0]}",
                "image_channels": image_array.shape[2] if len(image_array.shape) == 3 else 1,
                "recommendations": {
                    "recommended_method": "multi_layer",
                    "reason": "Best balance of capacity and stealthiness"
                },
                "capacities": capacities
            }
            
        elif file_ext in ['.wav', '.mp3', '.flac', '.ogg']:
            # AUDIO capacity
            audio_steg = AudioSteganography()
            file_size = len(contents)
            max_capacity = (file_size * 3) // (8 * 2)  # Conservative estimate
            
            return {
                "status": "success",
                "format": "audio",
                "file_size": file_size,
                "max_capacity_bytes": max_capacity,
                "method": "audio_lsb",
                "capacity_percentage": f"{(max_capacity / file_size * 100):.2f}%"
            }
            
        elif file_ext in ['.mp4', '.avi', '.mkv', '.mov']:
            # VIDEO capacity
            video_steg = VideoSteganography()
            file_size = len(contents)
            max_capacity = (file_size * 5) // (8 * 4)  # Conservation estimate
            
            return {
                "status": "success",
                "format": "video",
                "file_size": file_size,
                "max_capacity_bytes": max_capacity,
                "method": "video_lsb",
                "capacity_percentage": f"{(max_capacity / file_size * 100):.2f}%"
            }
            
        elif file_ext == '.pdf':
            # PDF capacity
            pdf_steg = PDFSteganography()
            file_path = _temp_file_from_bytes(contents, '.pdf')
            try:
                cap_info = pdf_steg.calculate_capacity(file_path)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return {
                "status": "success",
                "format": "pdf",
                **cap_info
            }
            
        elif file_ext in ['.docx', '.doc']:
            # DOCX capacity
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.docx')
            try:
                cap_info = doc_steg.calculate_capacity(file_path)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return {
                "status": "success",
                "format": "docx",
                **cap_info
            }
            
        elif file_ext in ['.odt']:
            # ODT capacity
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.odt')
            try:
                cap_info = doc_steg.calculate_capacity(file_path)
            finally:
                if os.path.exists(file_path):
                    os.remove(file_path)
            
            return {
                "status": "success",
                "format": "odt",
                **cap_info
            }
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Capacity calculation failed: {str(e)}")


@app.post("/embed")
async def embed_data(
    file: UploadFile = File(...),
    secret_message: str = Form(default=""),
    secret_file: Optional[UploadFile] = File(default=None),
    password: str = Form(default=""),
    method: str = Form(default="auto"),
    compression: bool = Form(default=True),
    encryption_mode: str = Form(default="auto"),
    self_destruct_mode: str = Form(default="unlimited"),
    watermark_mode: str = Form(default="hidden"),
    decode_limit: int = Form(default=0),
    time_limit_hours: int = Form(default=0),
    is_file: bool = Form(default=False),
    filename: str = Form(default=""),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Embed encrypted data into any media format.
    
    Supports: Images (PNG, JPG), Audio (WAV, MP3), Video (MP4, AVI), 
    PDF, DOCX, ODT
    
    Features:
    - AES-256-GCM encryption
    - Optional password protection
    - Automatic format detection
    - Multiple embedding methods per format
    - Returns steganographic file and metadata
    """
    upload_id = str(uuid.uuid4())
    temp_files = []
    
    try:
        contents = await file.read()
        
        # Detect file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        mime_type, _ = mimetypes.guess_type(file.filename)
        
        # Determine content type
        if secret_file is not None or is_file:
            # File mode: read bytes from the uploaded secret file
            if secret_file is not None:
                secret_file_bytes = await secret_file.read()
                actual_filename = filename or secret_file.filename
                secret_mime, _ = mimetypes.guess_type(actual_filename)
                content_type = secret_mime or "application/octet-stream"
            else:
                # Fallback: treat secret_message as a file path is not supported;
                # the caller should send an actual file via secret_file field.
                raise HTTPException(
                    status_code=400,
                    detail="File mode requires uploading the secret file in the 'secret_file' field"
                )
            content = secret_file_bytes
        else:
            content_type = "text/plain"
            actual_filename = None
            content = secret_message.encode('utf-8')
        
        # Compress if requested
        if compression:
            content = ImageSteganography.compress_payload(content)
        
        # Create payload metadata with explicit decode/time limits.
        # Priority: explicit controls > legacy self_destruct_mode.
        max_decodes = max(0, int(decode_limit or 0))
        limit_hours = max(0, int(time_limit_hours or 0))

        if max_decodes == 0 and self_destruct_mode == "one_decode":
            max_decodes = 1
        if limit_hours == 0 and self_destruct_mode == "24_hours":
            limit_hours = 24

        expiration_timestamp = None
        expiration_mode = "unlimited"
        if limit_hours > 0:
            expiration_timestamp = int(time.time()) + (limit_hours * 60 * 60)
            expiration_mode = "time_limit"
        if max_decodes > 0:
            expiration_mode = "decode_limit"
        
        payload_metadata = PayloadMetadata(
            version=1,
            content_type=content_type,
            filename=actual_filename,
            expiration_mode=expiration_mode,
            expiration_timestamp=expiration_timestamp,
            max_decodes=max_decodes if max_decodes > 0 else None,
            watermark_mode=watermark_mode,
            embedding_method=method,
            seed=42,
            is_encrypted=encryption_mode != 'none',
            compression=compression,
            creation_timestamp=int(time.time())
        )
        
        # Encrypt content based on encryption mode
        recovery_key = None
        if encryption_mode == 'none':
            # No encryption - just wrap with metadata
            full_payload = PayloadStructure.encode(content, payload_metadata)
        else:
            # Encrypt the content
            if encryption_mode == 'auto' or (encryption_mode == 'manual' and not password):
                # Auto-generate key
                key = generate_random_key(32)
                salt = None
                recovery_key = '-'.join([key.hex().upper()[i:i+4] for i in range(0, 64, 4)])
            else:
                # Use password
                key, salt = derive_key_from_password(password)
                recovery_key = None
            
            ciphertext, nonce, tag = encrypt_aes_gcm(content, key)
            
            # Build encrypted payload
            if salt:
                encrypted_content = salt + nonce + tag + ciphertext
            else:
                encrypted_content = nonce + tag + ciphertext
            
            payload_metadata.encryption_key_hash = hashlib.sha256(key).hexdigest()
            full_payload = PayloadStructure.encode(encrypted_content, payload_metadata)
        
        stego_path = None
        stego_bytes = None
        metadata = {}
        response_media_type = "application/octet-stream"
        output_filename = file.filename
        
        # Route based on file type
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']:
            # IMAGE steganography
            image_array = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
            if image_array is None:
                raise HTTPException(status_code=400, detail="Invalid image file")
            
            cap_info = CapacityCalculator.calculate_image_capacity(image_array, method if method != 'auto' else 'multi_layer')
            
            if len(full_payload) > cap_info['max_capacity_bytes']:
                raise HTTPException(
                    status_code=413,
                    detail=f"Payload too large for image. Max: {cap_info['max_capacity_bytes']} bytes"
                )
            
            steg = ImageSteganography(method=method if method != 'auto' else 'multi_layer_lsb')
            
            # Map method names to actual methods
            if method in ['lsb', 'auto']:
                stego_image, metadata = steg.embed_lsb(image_array, full_payload, randomization_seed=42)
            elif method == 'multi_layer_lsb' or method == 'multi_layer':
                stego_image, metadata = steg.embed_multi_layer(image_array, full_payload, randomization_seed=42)
            elif method == 'dct':
                stego_image, metadata = steg.embed_dct(image_array, full_payload)
            elif method == 'spread_spectrum':
                stego_image, metadata = steg.embed_spread_spectrum(image_array, full_payload, randomization_seed=42)
            elif method == 'histogram_shifting':
                stego_image, metadata = steg.embed_histogram_shifting(image_array, full_payload, randomization_seed=42)
            else:
                stego_image, metadata = steg.embed_multi_layer(image_array, full_payload, randomization_seed=42)
            
            stego_img_uint8 = stego_image.astype(np.uint8)
            
            # Handle both grayscale (DCT) and RGB (LSB, multi-layer) images
            if len(stego_img_uint8.shape) == 2:
                # Grayscale - convert to RGB
                pil_image = Image.fromarray(stego_img_uint8, mode='L').convert('RGB')
            else:
                # RGB
                pil_image = Image.fromarray(stego_img_uint8, mode='RGB')
            
            output_buffer = io.BytesIO()
            pil_image.save(output_buffer, 'PNG', optimize=True, compress_level=9)
            stego_bytes = output_buffer.getvalue()
            
            response_media_type = "image/png"
            output_filename = 'stego_output.png'
            
        elif file_ext in ['.wav', '.mp3', '.flac', '.ogg']:
            # AUDIO steganography
            audio_steg = AudioSteganography()
            file_path = _temp_file_from_bytes(contents, file_ext)
            temp_files.append(file_path)
            stego_path, metadata = audio_steg.embed_lsb(file_path, full_payload)
            response_media_type = "audio/wav"
            output_filename = f"stego_{uuid.uuid4().hex[:8]}.wav"
            
        elif file_ext in ['.mp4', '.avi', '.mkv', '.mov']:
            # VIDEO steganography
            video_steg = VideoSteganography()
            file_path = _temp_file_from_bytes(contents, file_ext)
            temp_files.append(file_path)
            stego_path, metadata = video_steg.embed_lsb(file_path, full_payload)
            response_media_type = "video/mp4"
            output_filename = f"stego_{uuid.uuid4().hex[:8]}.mp4"
            
        elif file_ext == '.pdf':
            # PDF steganography
            pdf_steg = PDFSteganography()
            file_path = _temp_file_from_bytes(contents, '.pdf')
            temp_files.append(file_path)
            stego_path, metadata = pdf_steg.embed_in_metadata(file_path, full_payload)
            response_media_type = "application/pdf"
            output_filename = f"stego_{uuid.uuid4().hex[:8]}.pdf"
            
        elif file_ext in ['.docx', '.doc']:
            # DOCX steganography
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.docx')
            temp_files.append(file_path)
            stego_path, metadata = doc_steg.embed_in_docx(file_path, full_payload)
            response_media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            output_filename = f"stego_{uuid.uuid4().hex[:8]}.docx"
            
        elif file_ext in ['.odt']:
            # ODT steganography
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.odt')
            temp_files.append(file_path)
            stego_path, metadata = doc_steg.embed_in_odt(file_path, full_payload)
            response_media_type = "application/vnd.oasis.opendocument.text"
            output_filename = f"stego_{uuid.uuid4().hex[:8]}.odt"
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}. Supported: Images, Audio, Video, PDF, DOCX, ODT"
            )
        
        if stego_path:
            temp_files.append(stego_path)
            with open(stego_path, 'rb') as generated_file:
                stego_bytes = generated_file.read()

        if not stego_bytes:
            raise HTTPException(status_code=500, detail="Failed to generate output data")

        _cache_output(upload_id, stego_bytes, output_filename, response_media_type)
        
        # Return JSON metadata — client fetches the file via /download-stego?session_id=...
        response_metadata = {
            "status": "success",
            "message": "Data embedded successfully",
            "session_id": upload_id,
            "format": file_ext.strip('.'),
            "payload_size_bytes": len(content),
            "encrypted_size_bytes": len(full_payload),
            "password_protected": bool(password) if encryption_mode == 'manual' else False,
            "recovery_key": recovery_key,
            "output_filename": output_filename,
            "encryption_mode": encryption_mode,
            "self_destruct_mode": self_destruct_mode,
            "expiration_mode": expiration_mode,
            "decode_limit": max_decodes,
            "time_limit_hours": limit_hours,
            "watermark_mode": watermark_mode,
            "embedding_method": method,
            "metadata": metadata
        }
        
        return JSONResponse(content=response_metadata)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding failed: {str(e)}")
    finally:
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)


# ---- Extract helpers ----

def _decode_output(plaintext: bytes, meta):
    """Return plaintext as UTF-8 string or base64-encoded binary blob."""
    import base64
    if meta and meta.content_type and not meta.content_type.startswith('text/'):
        return base64.b64encode(plaintext).decode('utf-8')
    try:
        return plaintext.decode('utf-8')
    except Exception:
        return base64.b64encode(plaintext).decode('utf-8')


def _build_extract_response(message: str, plaintext: bytes, meta, file_ext: str) -> dict:
    """Build standardised extract response."""
    resp = {
        "status": "success",
        "message": "Data extracted successfully",
        "extracted_data": message,
        "data_size_bytes": len(plaintext),
        "format": file_ext.strip('.'),
        "timestamp": datetime.now().isoformat(),
    }
    if meta:
        resp["content_type"]     = meta.content_type
        resp["filename"]         = meta.filename
        resp["expiration_mode"]  = meta.expiration_mode
        resp["watermark_mode"]   = meta.watermark_mode
        resp["embedding_method"] = meta.embedding_method
        resp["creation_timestamp"] = meta.creation_timestamp
        if meta.expiration_mode == "24_hours" and meta.expiration_timestamp:
            remaining = meta.expiration_timestamp - int(time.time())
            resp["expires_in_seconds"] = max(0, remaining)
        if meta.expiration_mode == "time_limit" and meta.expiration_timestamp:
            remaining = meta.expiration_timestamp - int(time.time())
            resp["expires_in_seconds"] = max(0, remaining)
        if getattr(meta, "max_decodes", None):
            resp["decode_limit"] = meta.max_decodes
        if getattr(meta, "decode_count", None) is not None:
            resp["decode_count"] = meta.decode_count
    return resp


@app.post("/extract")
async def extract_data(
    file: UploadFile = File(...),
    password: str = Form(default=""),
    recovery_key: str = Form(default=""),
    method: str = Form(default="auto")
):
    """
    Extract hidden encrypted data from any media format.
    
    Supports: Images (PNG, JPG), Audio (WAV, MP3), Video (MP4, AVI),
    PDF, DOCX, ODT
    
    Features:
    - Automatic format detection
    - New PayloadStructure format with metadata, expiration, self-destruct
    - Password-protected or keyless extraction
    - Decompression handling
    - Integrity verification
    """
    temp_files = []
    
    try:
        contents = await file.read()
        
        # Detect file type
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        full_payload = None
        
        # Route based on file type to extract raw payload bytes
        if file_ext in ['.png', '.jpg', '.jpeg', '.bmp', '.gif', '.tiff']:
            # IMAGE extraction
            image_array = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
            if image_array is None:
                raise HTTPException(status_code=400, detail="Invalid image file")
            
            steg = ImageSteganography(method=method if method != 'auto' else 'multi_layer')
            try:
                full_payload = steg.extract_lsb(image_array, seed=42)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Could not extract data from image: {str(e)}")
                
        elif file_ext in ['.wav', '.mp3', '.flac', '.ogg']:
            # AUDIO extraction
            audio_steg = AudioSteganography()
            file_path = _temp_file_from_bytes(contents, file_ext)
            temp_files.append(file_path)
            full_payload = audio_steg.extract_lsb(file_path, 1000)
            
        elif file_ext in ['.mp4', '.avi', '.mkv', '.mov']:
            # VIDEO extraction
            video_steg = VideoSteganography()
            file_path = _temp_file_from_bytes(contents, file_ext)
            temp_files.append(file_path)
            full_payload = video_steg.extract_lsb(file_path, 1000)
            
        elif file_ext == '.pdf':
            # PDF extraction
            pdf_steg = PDFSteganography()
            file_path = _temp_file_from_bytes(contents, '.pdf')
            temp_files.append(file_path)
            full_payload = pdf_steg.extract_from_metadata(file_path)
            
        elif file_ext in ['.docx', '.doc']:
            # DOCX extraction
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.docx')
            temp_files.append(file_path)
            full_payload = doc_steg.extract_from_docx(file_path)
            
        elif file_ext in ['.odt']:
            # ODT extraction
            doc_steg = DocumentSteganography()
            file_path = _temp_file_from_bytes(contents, '.odt')
            temp_files.append(file_path)
            full_payload = doc_steg.extract_from_odt(file_path)
            
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format: {file_ext}"
            )
        
        if not full_payload:
            raise HTTPException(status_code=400, detail="No embedded data found")
        
        # ---- Detect payload format ----
        payload_meta = None
        inner_payload = full_payload
        payload_hash = hashlib.sha256(full_payload).hexdigest()

        if full_payload[:2] == b'SG':
            # New PayloadStructure format
            try:
                payload_meta, inner_payload = PayloadStructure.decode(full_payload)
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Payload format error: {str(e)}")

            # Check expiration
            payload_meta.decode_count = _get_decode_count(payload_hash)
            is_expired, expire_reason = PayloadStructure.check_expiration(payload_meta)
            if is_expired:
                raise HTTPException(status_code=410, detail=f"Message expired: {expire_reason}")

            if not payload_meta.is_encrypted:
                # No encryption — inner_payload is already the content (possibly compressed)
                plaintext = inner_payload
                if payload_meta.compression:
                    try:
                        plaintext = ImageSteganography.decompress_payload(plaintext)
                    except Exception:
                        pass
                
                result_message = _decode_output(plaintext, payload_meta)
                payload_meta.decode_count = _increment_decode_count(payload_hash)
                return _build_extract_response(result_message, plaintext, payload_meta, file_ext)

            # Encrypted new format — determine key source
            if recovery_key:
                key = bytes.fromhex(recovery_key.replace('-', '').replace(' ', ''))
                nonce = inner_payload[:12]
                tag   = inner_payload[12:28]
                ciphertext = inner_payload[28:]
            elif password:
                salt = inner_payload[:16]
                nonce = inner_payload[16:28]
                tag   = inner_payload[28:44]
                ciphertext = inner_payload[44:]
                key, _ = derive_key_from_password(password, salt)
            else:
                raise HTTPException(
                    status_code=400,
                    detail="This message is encrypted. Provide the recovery_key or password."
                )
        else:
            # Legacy format — require key or password
            if not password and not recovery_key:
                raise HTTPException(
                    status_code=400,
                    detail="Either password or recovery_key must be provided"
                )
            if recovery_key:
                key = bytes.fromhex(recovery_key.replace('-', '').replace(' ', ''))
                nonce = inner_payload[:12]
                tag   = inner_payload[12:28]
                ciphertext = inner_payload[28:]
            elif password:
                if len(inner_payload) < 44:
                    raise HTTPException(status_code=400, detail="Invalid payload format — too small")
                salt = inner_payload[:16]
                nonce = inner_payload[16:28]
                tag   = inner_payload[28:44]
                ciphertext = inner_payload[44:]
                key, _ = derive_key_from_password(password, salt)

        # Decrypt
        try:
            plaintext = decrypt_aes_gcm(ciphertext, key, nonce, tag)
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail=f"Decryption failed. Invalid password/key or corrupted data: {str(e)}"
            )

        # Decompress
        try:
            if payload_meta is None or payload_meta.compression:
                plaintext = ImageSteganography.decompress_payload(plaintext)
        except Exception:
            pass  # Not compressed or already plain

        result_message = _decode_output(plaintext, payload_meta)
        if payload_meta:
            payload_meta.decode_count = _increment_decode_count(payload_hash)
        return _build_extract_response(result_message, plaintext, payload_meta, file_ext)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    finally:
        for temp_file in temp_files:
            if temp_file and os.path.exists(temp_file):
                os.remove(temp_file)


@app.post("/detect")
async def detect_hidden_data(
    file: UploadFile = File(...),
    sensitivity: str = Form(default="medium")
):
    """
    Analyze file for presence of hidden data.
    
    Uses statistical analysis, entropy metrics, and LSB distribution anomalies.
    Returns probability score and detailed analysis.
    """
    try:
        contents = await file.read()
        image_array = cv2.imdecode(np.frombuffer(contents, np.uint8), cv2.IMREAD_COLOR)
        
        if image_array is None:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Perform detection analysis
        detector = SteganalysisDetector()
        analysis = detector.detect_hidden_data(image_array, sensitivity)
        
        return {
            "status": "success",
            "analysis": analysis,
            "timestamp": datetime.now().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection analysis failed: {str(e)}")


@app.post("/generate-key")
async def generate_key(format_style: str = Form(default="hex")):
    """
    Generate a random recovery key for keyless mode.
    
    Formats: hex, base58, alphanumeric
    """
    try:
        from app.crypto import generate_keyless_mode_key
        
        key_bytes, key_string = generate_keyless_mode_key()
        
        return {
            "status": "success",
            "recovery_key": key_string,
            "key_bytes": key_bytes.hex(),
            "format": format_style,
            "security_level": "256-bit",
            "timestamp": datetime.now().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Key generation failed: {str(e)}")


@app.get("/download-stego")
async def download_stego(session_id: str, filename: str = "stego_output.png"):
    """Download generated stego file by session ID."""
    try:
        if not session_id or '/' in session_id or '\\' in session_id or '..' in session_id:
            raise HTTPException(status_code=400, detail="Invalid session ID")

        _prune_output_cache()
        cached_output = OUTPUT_CACHE.get(session_id)
        if not cached_output:
            raise HTTPException(status_code=404, detail="Stego file not found or already expired")

        response = Response(content=cached_output["data"], media_type=cached_output["media_type"])
        response.headers["Content-Disposition"] = f'attachment; filename="{cached_output["filename"]}"'
        return response

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
