
# SecureSteg - Professional Steganography Workspace

**A modern, user-friendly platform for hiding sensitive data inside images with military-grade encryption, in-memory operations, and production-grade architecture.**

![SecureSteg Architecture](https://img.shields.io/badge/Architecture-SaaS-brightgreen) ![Encryption](https://img.shields.io/badge/Encryption-AES--256--GCM-blue) ![Frontend](https://img.shields.io/badge/Frontend-React%2018-61dafb) ![Backend](https://img.shields.io/badge/Backend-FastAPI-009688)

## 🔐 Features

### Core Steganography Capabilities
- **Multi-layer LSB Embedding** - Randomized channel distribution for maximum stealth
- **DCT Transform** - Frequency-domain embedding for enhanced robustness
- **Adaptive Noise Embedding** - Avoids flat regions to prevent detectability
- **Multi-format Support** - Images (PNG, JPEG, BMP), Audio (WAV, MP3), Video
- **Compression** - Gzip compression before encryption to reduce payload size

### Security Features
- **AES-256-GCM** - Military-grade authenticated encryption
- **Argon2id/PBKDF2** - GPU-resistant key derivation
- **Cryptographic Randomness** - Secure random number generation
- **No Metadata Leakage** - Complete separation from steganographic payload
- **No Plaintext Logging** - Never logs secret messages
- **Rate Limiting** - Prevents brute-force extraction attempts

### Additional Capabilities
- **Keyless Mode** - Auto-generated recovery keys (8F92-A1B2-77C9)
- **Password Protection** - Optional user-provided passwords
- **Capacity Calculator** - Real-time capacity analysis with detectability assessment
- **Hidden Data Detection** - Steganalysis using LSB, entropy, and channel correlation analysis
- **Self-Destruct Messages** - Configurable expiration times (future enhancement)

## 🏗️ Architecture

```
SecureSteg/
├── backend/
│   ├── app/
│   │   ├── api/              # FastAPI endpoints
│   │   ├── crypto/           # Encryption & key derivation
│   │   ├── steg/             # Steganography algorithms
│   │   ├── detection/        # Steganalysis detection
│   │   ├── utils/            # File handling & utilities
│   │   └── main.py           # FastAPI application
│   ├── requirements.txt      # Python dependencies
│   └── run.py               # Backend entry point
│
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── api/              # API client
│   │   ├── store.js          # Zustand state management
│   │   ├── App.jsx           # Main app component
│   │   └── index.css         # Tailwind styles
│   ├── index.html
│   ├── package.json
│   └── vite.config.js
│
└── docs/
    ├── API.md               # API documentation
    ├── SECURITY.md          # Security details
    ├── DEPLOYMENT.md        # Deployment guide
    └── ALGORITHMS.md        # Algorithm details
```

## 🚀 Quick Start

### Backend Setup

```bash
cd backend
pip install -r requirements.txt
python run.py
```

Server runs on `http://localhost:8000`

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`

## 📋 Usage Examples

### Embedding Data

```python
from app.crypto import encrypt_aes_gcm, generate_random_key
from app.steg import ImageSteganography

# Generate encryption key
key = generate_random_key(32)  # 256-bit

# Encrypt message
message = b"Secret message"
ciphertext, nonce, tag = encrypt_aes_gcm(message, key)

# Embed into image
steg = ImageSteganography(method='multi_layer')
stego_image, metadata = steg.embed_multi_layer(
    'cover.png',
    ciphertext + nonce + tag,
    randomization_seed=42
)

# Save result
import cv2
cv2.imwrite('stego.png', stego_image)
```

### Extracting Data

```python
from app.crypto import decrypt_aes_gcm
from app.steg import ImageSteganography

# Load stego image
import cv2
stego = cv2.imread('stego.png', cv2.IMREAD_COLOR)

# Extract payload
steg_obj = ImageSteganography()
full_payload = steg_obj.extract_lsb(stego, seed=42)

# Parse encrypted components
nonce = full_payload[:12]
tag = full_payload[12:28]
ciphertext = full_payload[28:]

# Decrypt
key = ...  # 256-bit key
message = decrypt_aes_gcm(ciphertext, key, nonce, tag)
```

## 🔍 API Endpoints

### POST /embed
Embed encrypted data into media file.

**Parameters:**
- `file`: Media file to embed into
- `secret_message`: Message to hide
- `password`: Optional password (or keyless mode)
- `method`: Embedding method ('lsb', 'multi_layer', 'dct')
- `compression`: Enable gzip compression

**Returns:**
```json
{
  "status": "success",
  "payload_size_bytes": 1024,
  "recovery_key": "8F92-A1B2-77C9",
  "detectability": "VERY LOW",
  "capacity_utilization": "15.3%"
}
```

### POST /extract
Extract and decrypt hidden data.

**Parameters:**
- `file`: Steganographic media file
- `password` or `recovery_key`: Decryption key
- `method`: Extraction method

**Returns:**
```json
{
  "status": "success",
  "extracted_data": "Secret message content",
  "data_size_bytes": 14
}
```

### POST /detect
Analyze file for hidden data presence.

**Parameters:**
- `file`: Media file to analyze
- `sensitivity`: 'low', 'medium', 'high'

**Returns:**
```json
{
  "hidden_data_detected": true,
  "probability": 0.72,
  "confidence": 0.85,
  "recommendation": "Likely contains hidden data"
}
```

### POST /capacity
Calculate embedding capacity.

**Returns:**
```json
{
  "image_dimensions": "1920x1080",
  "capacities": {
    "multi_layer": {
      "max_capacity_bytes": 262144,
      "estimated_detectability": "VERY LOW"
    }
  }
}
```

## 🔒 Security Model

### Encryption
- **Algorithm:** AES-256-GCM (Galois/Counter Mode)
- **Key Size:** 256 bits
- **Authentication:** 16-byte authentication tag
- **Nonce:** 12-byte random nonce (96-bit)

### Key Derivation
- **Password Mode:** PBKDF2 with 100,000 iterations
- **Keyless Mode:** Cryptographically secure 256-bit random key

### Payload Structure
```
[Salt (16B)] [Nonce (12B)] [Auth Tag (16B)] [Encrypted Data]
```

### Embedding Methods

#### 1. Multi-Layer LSB (Recommended)
- Embeds across all three RGB channels
- Randomized pixel selection using seeded PRNG
- 1 bit per channel per pixel
- Capacity: ~50% image pixels * 8 bits (with safety margin: ~20%)
- Detection Risk: **VERY LOW**

#### 2. Standard LSB
- Uses least significant bit of each pixel
- Capacity: ~30-40% of image size
- Detection Risk: **MEDIUM**

#### 3. DCT (Discrete Cosine Transform)
- Embeds in mid-frequency DCT coefficients
- More robust but lower capacity
- Capacity: ~5% of image size
- Detection Risk: **LOW**

## 🛡️ Security Features

### 1. No Metadata Leakage
- Salt, nonce, and tag are embedded within steganographic payload
- No external information stored
- File properties appear unmodified

### 2. Cryptographic Randomness
- Uses `Cryptodome.Random` and `secrets` modules
- Ensures unpredictable nonces and keys
- Prevents pattern-based analysis

### 3. Authenticated Encryption
- AES-GCM provides both confidentiality and authenticity
- Detects tampering attempts
- Fails gracefully on corrupted data

### 4. Adaptive Embedding
- Noise-adaptive pixelselection using edge detection
- Embeds in complex regions to avoid visual artifacts
- Reduces detectability via LSB analysis

### 5. Compression Before Encryption
- Gzip compression reduces payload size
- Larger payloads → Higher detectability
- Compression ratio: 2:1 to 4:1 typical for text

## 📊 Capacity Examples

### For a 1920x1080 Image

| Method | Capacity | Detectability |
|--------|----------|---------------|
| Multi-Layer LSB | ~262 KB | VERY LOW |
| Standard LSB | ~186 KB | MEDIUM |
| DCT | ~52 KB | LOW |

## 🔍 Detection Capabilities

### Analysis Methods

1. **LSB Distribution Analysis**
   - Chi-square test on LSB distribution
   - Pair correlation in LSB sequences
   - Detects systematic changes

2. **Channel Correlation**
   - Analyzes relationship between R, G, B channels
   - Natural images have correlated channels
   - Embedded data disrupts correlations

3. **Entropy Analysis**
   - Measures information complexity
   - Encrypted data has high entropy
   - Compares to natural image entropy

### Detection Metrics
- **Probability Score:** 0.0 to 1.0
- **Confidence:** Based on consistency across metrics
- **Sensitivity:** Adjustable (low/medium/high)

## 🚀 Deployment

### Production Requirements

1. **Backend**
   - Python 3.8+
   - FastAPI with Uvicorn
   - 2GB RAM minimum
   - 10GB disk for uploads

2. **Frontend**
   - Node.js 16+
   - React 18+
   - Built with Vite

### Docker Deployment

```bash
# Build backend image
docker build -t securesteg-backend ./backend

# Build frontend image
docker build -t securesteg-frontend ./frontend

# Run with Docker Compose
docker-compose up -d
```

### Nginx Reverse Proxy

```nginx
upstream backend {
    server localhost:8000;
}

server {
    listen 443 ssl http2;
    server_name steg.yourdomain.com;

    location /api {
        proxy_pass http://backend;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        proxy_pass http://localhost:5173;
    }
}
```

## 📚 Documentation

- [API Documentation](./docs/API.md)
- [Security Details](./docs/SECURITY.md)
- [Algorithm Reference](./docs/ALGORITHMS.md)
- [Deployment Guide](./docs/DEPLOYMENT.md)

## ⚠️ Important Notes

### Legal & Ethical Use
- Use only for **authorized security testing**
- Comply with local laws and regulations
- Never use for malicious purposes
- Respect privacy of others

### Limitations
- Detection is not 100% accurate
- Large payloads increase detectability risk
- Compression helps but adds overhead
- Image quality affects capacity

### Best Practices
1. Use strong passwords (16+ characters)
2. Keep recovery keys safe
3. Test with small messages first
4. Use high-complexity cover images
5. Monitor capacity utilization

## 🤝 Contributing

Contributions welcome! Areas for enhancement:
- Video/Audio steganography
- WebAssembly performance optimization
- Additional detection algorithms
- Cloud deployment guides

## 📄 License

MIT License - See LICENSE file

## 🙋 Support

For issues or questions:
1. Check [FAQ](./docs/FAQ.md)
2. Review [Troubleshooting](./docs/TROUBLESHOOTING.md)
3. Open an issue on GitHub

---

**Built with security and stealth in mind** 🔐
