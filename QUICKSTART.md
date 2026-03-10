# Quick Start Guide - SecureSteg

## 🚀 Start using SecureSteg in 5 minutes

### Prerequisites

- Python 3.8+
- Node.js 16+
- pip and npm installed

### Installation

#### 1. Backend

```bash
cd backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start backend
python run.py
```

**Output:**
```
╔════════════════════════════════════════════════════════╗
║         SecureSteg - Steganography Platform            ║
║              Starting Backend Server                   ║
╚════════════════════════════════════════════════════════╝

INFO:     Uvicorn running on http://0.0.0.0:8000
```

#### 2. Frontend

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

**Output:**
```
  VITE v5.0.8  ready in 342 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

#### 3. Access the Application

Open browser to: **http://localhost:5173**

---

## 💻 Usage Examples

### Example 1: Hide a Message in an Image

1. **Select Mode**: Click "Hide" tab
2. **Select Image**: Upload cover.png
3. **Enter Message**: "Meet at the concert"
4. **Security**:
   - Enter password: "MySecure123Pass"
   - Or use Keyless Mode (auto-generate key)
5. **Embed**: Click "Hide Data in Image"
6. **Download**: Get stego_output.png

### Example 2: Extract Hidden Data

1. **Select Mode**: Click "Extract" tab
2. **Select Image**: Upload stego_output.png
3. **Unlock**:
   - Enter same password, OR
   - Paste recovery key
4. **Extract**: Watch message appear!

### Example 3: Detect Hidden Data

1. **Select Mode**: Click "Detect" tab
2. **Select Image**: Upload any image
3. **Analyze**: Click "Analyze Image"
4. **Results**: See probability percentage

---

## 📊 Capacity Guide

Depends on image size and quality:

| Image Size | Multi-Layer Capacity | Detection Risk |
|------------|--------------------|-|
| 800x600 | ~100 KB | VERY LOW |
| 1920x1080 | ~260 KB | VERY LOW |
| 4K (3840x2160) | ~1 MB | VERY LOW |

**Tip**: Larger, complex images work better than small or uniform images.

---

## 🔐 Security Tips

### Password
- Use 16+ characters
- Mix uppercase, lowercase, numbers, symbols
- Example: `Th!s1sMyStr0ngP@ss`

### Recovery Key (Keyless Mode)
- Save securely (password manager)
- Never share publicly
- Lost key = Lost access

### Cover Image
- Use natural photos with lots of detail
- Avoid simple graphics or flat colors
- Larger is always better

---

## 🛠️ API Tests (curl)

### Capacity Check

```bash
curl -X POST http://localhost:8000/capacity \
  -F "file=@image.png"
```

### Embed with Password

```bash
curl -X POST http://localhost:8000/embed \
  -F "file=@image.png" \
  -F "secret_message=Test message" \
  -F "password=MyPassword123" \
  -F "method=multi_layer"
```

### Extract

```bash
curl -X POST http://localhost:8000/extract \
  -F "file=@stego.png" \
  -F "password=MyPassword123"
```

### Detect

```bash
curl -X POST http://localhost:8000/detect \
  -F "file=@image.png" \
  -F "sensitivity=medium"
```

---

## 🐛 Common Issues

### "Backend not responding"

```bash
# Check if backend is running
curl http://localhost:8000/health

# If not, start it:
cd backend
python run.py
```

### "Invalid image format"

- Use PNG, JPEG, or BMP
- File must be a valid image
- Test with: `file image.png`

### "Payload too large"

- Message is too big for image
- Use larger image, or
- Compress message before hiding

### "Extraction fails with 'Invalid password'"

- Password must match exactly
- Check caps lock
- Copy-paste recovery key without spaces

---

## 🔄 Workflow Examples

### Scenario: Sending Secure Messages

```
Alice                                  Bob
   │
   ├─ Takes photo.png
   ├─ Enters secret message
   ├─ Sets password: "abc123"
   ├─ Gets stego.png
   │
   └─ Sends stego.png via email ─────────>
                                      ├─ Downloads stego.png
                                      ├─ Uses Extract mode
                                      ├─ Enters password: "abc123"
                                      └─ Reads secret message ✓
```

### Scenario: Anonymous Secure Channel

```
Alice (Keyless Mode)               Bob
   │
   ├─ Hides message in image
   ├─ Gets auto recovery key
   │   "8F92-A1B2-77C9"
   │
   └─ Sends via:
      - Email (image)              ──────> ├─ Downloads image
      - Public message (recovery key) ──>  ├─ Pastes recovery key
                                           ├─ Extracts message ✓
```

---

## 📈 Performance

### Timing (approximate)

| Operation | Time | CPU | RAM |
|-----------|------|-----|-----|
| Capacity calculation | 200ms | Low | 50MB |
| Embedding (1920x1080) | 2-5s | Medium | 200MB |
| Extraction (1920x1080) | 1-3s | Medium | 200MB |
| Detection analysis | 1-2s | Medium | 150MB |

### Optimization

- Larger images = slower (more data to process)
- Compression enabled = faster
- Multi-layer method = slightly slower but safer

---

## Next Steps

### Learn More

1. **Read Full Documentation**
   - [README.md](../README.md)
   - [API.md](./docs/API.md)

2. **Security Deep Dive**
   - [SECURITY.md](./docs/SECURITY.md)

3. **Production Deployment**
   - [DEPLOYMENT.md](./docs/DEPLOYMENT.md)

### Integrate with Your Project

```python
import requests

API_URL = 'http://localhost:8000'

# Calculate capacity
response = requests.post(f'{API_URL}/capacity', files={'file': open('image.png', 'rb')})
capacity = response.json()

# Embed data
response = requests.post(f'{API_URL}/embed', 
    files={'file': open('image.png', 'rb')},
    data={
        'secret_message': 'My secret',
        'password': 'password123',
        'method': 'multi_layer'
    }
)
result = response.json()
```

---

## ⚠️ Important Notes

- **Legal**: Use only for authorized purposes
- **Backup**: Keep recovery keys safe
- **Testing**: Start with small messages
- **Production**: Review DEPLOYMENT.md

---

## Getting Help

- **Docs**: Check [docs/](./docs/) folder
- **GitHub**: Open an issue
- **Email**: Submit question in documentation

---

**Happy hiding! 🔐**
