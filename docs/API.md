# API Reference - SecureSteg

## Base URL

```
http://localhost:8000
```

## Authentication

Currently, the API is stateless and does not require authentication. All operations are based on provided credentials (password or recovery key).

## Endpoints

### 1. GET /

Health and status endpoint.

**Response:**
```json
{
  "name": "SecureSteg",
  "status": "active",
  "version": "1.0.0",
  "endpoints": {
    "embed": "POST /embed",
    "extract": "POST /extract",
    "detect": "POST /detect",
    "generate_key": "POST /generate-key",
    "capacity": "POST /capacity"
  }
}
```

### 2. GET /health

Quick health check.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-03-10T15:30:00.000000"
}
```

---

### 3. POST /embed

Hide encrypted data inside a media file.

**Request:**
```
Content-Type: multipart/form-data

Body:
- file: (File) - Cover image (PNG, JPEG, BMP)
- secret_message: (String) - Message to hide
- password: (String, optional) - Encryption password
- method: (String) - Embedding method (lsb|multi_layer|dct)
- compression: (Boolean) - Enable gzip compression (default: true)
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/embed \
  -F "file=@cover.png" \
  -F "secret_message=Hello Secret World" \
  -F "password=MySecretPassword123" \
  -F "method=multi_layer" \
  -F "compression=true"
```

**Response:**
```json
{
  "status": "success",
  "message": "Data embedded successfully",
  "session_id": "a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6",
  "embedding_method": "multi_layer",
  "payload_size_bytes": 156,
  "encrypted_size_bytes": 156,
  "password_protected": true,
  "recovery_key": null,
  "detectability": "VERY LOW",
  "capacity_utilization": "15.3%",
  "metadata": {
    "method": "multi_layer",
    "payload_size": 156,
    "seed": 42,
    "embedded_bits": 1248,
    "channels": 3
  }
}
```

**Error Responses:**
```json
{
  "detail": "Payload too large. Max: 262144 bytes, Got: 500000 bytes"
}
```

---

### 4. POST /extract

Extract hidden data from a steganographic image.

**Request:**
```
Content-Type: multipart/form-data

Body:
- file: (File) - Steganographic image
- password: (String, optional) - Decryption password
- recovery_key: (String, optional) - Recovery key from keyless mode
- method: (String) - Extraction method (default: auto)
```

**curl Example:**
```bash
# With password
curl -X POST http://localhost:8000/extract \
  -F "file=@stego.png" \
  -F "password=MySecretPassword123"

# With recovery key
curl -X POST http://localhost:8000/extract \
  -F "file=@stego.png" \
  -F "recovery_key=8F92-A1B2-77C9"
```

**Response:**
```json
{
  "status": "success",
  "message": "Data extracted successfully",
  "extracted_data": "Hello Secret World",
  "data_size_bytes": 18,
  "timestamp": "2024-03-10T15:31:00.000000"
}
```

**Error Responses:**
```json
{
  "detail": "Decryption failed. Invalid password or corrupted data: Authentication failed"
}
```

---

### 5. POST /detect

Analyze a file for presence of hidden data.

**Request:**
```
Content-Type: multipart/form-data

Body:
- file: (File) - Image to analyze
- sensitivity: (String) - Detection sensitivity (low|medium|high, default: medium)
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/detect \
  -F "file=@image.png" \
  -F "sensitivity=medium"
```

**Response:**
```json
{
  "status": "success",
  "analysis": {
    "hidden_data_detected": true,
    "probability": 0.72,
    "confidence": 0.85,
    "sensitivity": "medium",
    "recommendation": "Likely contains hidden data",
    "detailed_analysis": {
      "lsb_anomaly": 0.35,
      "channel_anomaly": 0.28,
      "entropy_anomaly": 0.09
    },
    "lsb_metrics": {
      "chi_square_statistic": 125.4,
      "lsb_ones_ratio": 0.45,
      "lsb_entropy": 0.92,
      "pair_correlation": -0.15,
      "anomaly_score": 0.30
    },
    "channel_metrics": {
      "r_g_correlation": 0.82,
      "r_b_correlation": 0.79,
      "g_b_correlation": 0.85,
      "mean_correlation": 0.82,
      "correlation_anomaly": 0.18
    },
    "entropy_metrics": {
      "shannon_entropy": 7.84,
      "normalized_entropy": 0.98,
      "histogram_max": 0.012,
      "histogram_min": 0.001,
      "uniformity_score": 0.989
    }
  },
  "timestamp": "2024-03-10T15:32:00.000000"
}
```

---

### 6. POST /capacity

Calculate maximum embedding capacity for an image.

**Request:**
```
Content-Type: multipart/form-data

Body:
- file: (File) - Image to analyze
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/capacity \
  -F "file=@image.png"
```

**Response:**
```json
{
  "status": "success",
  "image_dimensions": "1920x1080",
  "image_channels": 3,
  "recommendations": {
    "recommended_method": "multi_layer",
    "reason": "Best balance of capacity and stealthiness"
  },
  "capacities": {
    "lsb": {
      "method": "lsb",
      "image_size": "1920x1080",
      "channels": 3,
      "max_capacity_bytes": 186432,
      "max_capacity_kb": 181.86,
      "max_capacity_mb": 0.18,
      "theoretical_bits": 1491456,
      "entropy": 7.24,
      "safety_margin": 80,
      "estimated_detectability": "MEDIUM"
    },
    "multi_layer": {
      "method": "multi_layer",
      "image_size": "1920x1080",
      "channels": 3,
      "max_capacity_bytes": 262144,
      "max_capacity_kb": 256.0,
      "max_capacity_mb": 0.25,
      "theoretical_bits": 2097152,
      "entropy": 7.24,
      "safety_margin": 80,
      "estimated_detectability": "VERY LOW"
    },
    "dct": {
      "method": "dct",
      "image_size": "1920x1080",
      "channels": 3,
      "max_capacity_bytes": 52428,
      "max_capacity_kb": 51.2,
      "max_capacity_mb": 0.05,
      "theoretical_bits": 419424,
      "entropy": 7.24,
      "safety_margin": 80,
      "estimated_detectability": "LOW"
    }
  }
}
```

---

### 7. POST /generate-key

Generate a random recovery key for keyless mode.

**Request:**
```
Content-Type: application/x-www-form-urlencoded

Body:
- format_style: (String) - Key format (hex|base58|alphanumeric, default: hex)
```

**curl Example:**
```bash
curl -X POST http://localhost:8000/generate-key \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "format_style=hex"
```

**Response:**
```json
{
  "status": "success",
  "recovery_key": "8F92-A1B2-77C9-D4E5",
  "key_bytes": "8f92a1b277c9d4e5a1b2c3d4e5f6a7b8",
  "format": "hex",
  "security_level": "256-bit",
  "timestamp": "2024-03-10T15:33:00.000000"
}
```

---

### 8. POST /download-stego

Download the generated steganographic image.

**Request:**
```
Query Parameter:
- session_id: (String) - Session ID from /embed response
```

**curl Example:**
```bash
curl http://localhost:8000/download-stego?session_id=a1b2c3d4-e5f6-g7h8-i9j0-k1l2m3n4o5p6 \
  -o stego_output.png
```

**Response:**
- Binary PNG image file

---

## Error Handling

### Common Error Codes

| Code | Error | Description |
|------|-------|-------------|
| 400 | Bad Request | Invalid file format or missing required parameters |
| 401 | Unauthorized | Incorrect password or invalid recovery key |
| 413 | Payload Too Large | Payload exceeds image capacity |
| 404 | Not Found | Resource (session, file) not found |
| 500 | Internal Server Error | Server-side processing error |

### Error Response Format
```json
{
  "detail": "Error description or message"
}
```

---

## Rate Limiting

Currently not implemented. Future versions will include:
- 10 extraction attempts per minute per IP
- 60 embedding operations per hour per IP
- 429 Too Many Requests response

---

## Pagination & Filtering

Not applicable for current version (stateless operations)

---

## Data Types

### Embedding Methods
- `lsb` - Least Significant Bit (LSB)
- `multi_layer` - Multi-layer LSB with randomization
- `dct` - Discrete Cosine Transform

### Detection Sensitivity
- `low` - 60% threshold (fewer false positives)
- `medium` - 45% threshold (balanced)
- `high` - 30% threshold (more detections)

### Detectability Levels
- `VERY LOW` - <1% detectability risk
- `LOW` - 1-5% detectability risk
- `MEDIUM` - 5-15% detectability risk
- `HIGH` - 15-30% detectability risk
- `VERY HIGH` - >30% detectability risk

---

## Examples

### Complete Embedding Workflow

```bash
# 1. Calculate capacity
curl -X POST http://localhost:8000/capacity \
  -F "file=@nature.png" > capacity.json

# 2. Embed data with keyless mode
curl -X POST http://localhost:8000/embed \
  -F "file=@nature.png" \
  -F "secret_message=Meet at the old place at midnight" \
  -F "method=multi_layer" \
  -F "compression=true" > embed_result.json

# 3. Parse recovery key from response
RECOVERY_KEY=$(jq -r '.recovery_key' embed_result.json)
SESSION_ID=$(jq -r '.session_id' embed_result.json)

# 4. Download stego image
curl "http://localhost:8000/download-stego?session_id=$SESSION_ID" \
  -o stego.png

# 5. Later - Extract data
curl -X POST http://localhost:8000/extract \
  -F "file=@stego.png" \
  -F "recovery_key=$RECOVERY_KEY"
```

### Complete Detection Workflow

```bash
# 1. Detect hidden data with high sensitivity
curl -X POST http://localhost:8000/detect \
  -F "file=@suspicious.png" \
  -F "sensitivity=high" > detection.json

# 2. Parse results
PROBABILITY=$(jq -r '.analysis.probability' detection.json)
DETECTED=$(jq -r '.analysis.hidden_data_detected' detection.json)

echo "Hidden data probability: $PROBABILITY"
echo "Detected: $DETECTED"
```

---

## Webhooks

Not currently supported. Planned for future versions.

---

## Versioning

Current API Version: **1.0.0**

Backward compatibility will be maintained for minor versions (1.x.x).

---

## Support

For API issues and feature requests, refer to the main README and documentation.
