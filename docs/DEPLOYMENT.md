# Deployment Guide - SecureSteg

## Production Deployment

Comprehensive guide to deploy SecureSteg in production environment.

---

## Prerequisites

### System Requirements

- **OS**: Linux (Ubuntu 20.04+ recommended) or Windows Server 2019+
- **CPU**: 2+ cores
- **RAM**: 4GB minimum, 8GB recommended
- **Storage**: 50GB minimum (for uploads)
- **Network**: Stable internet connection, ports 80/443 open

### Software Requirements

- Python 3.8+
- Node.js 16+
- Nginx or Apache (reverse proxy)
- SSL/TLS certificate
- Docker (optional, for containerization)

---

## Option 1: Manual Deployment

### Step 1: Server Setup

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install dependencies
sudo apt-get install -y python3-pip nodejs npm nginx certbot python3-certbot-nginx

# Create application user
sudo useradd -m -s /bin/bash securesteg
sudo su - securesteg
```

### Step 2: Backend Setup

```bash
# Clone/download repository
git clone <repo> securesteg
cd securesteg/backend

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Create uploads directory
mkdir -p uploads
chmod 755 uploads

# Test the backend
python run.py  # Should start on localhost:8000
```

### Step 3: Frontend Setup

```bash
cd ../frontend

# Install Node dependencies
npm install

# Build for production
npm run build

# Output in dist/ directory
```

### Step 4: Configure Nginx

```nginx
# /etc/nginx/sites-available/securesteg

upstream backend {
    server localhost:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name steg.yourdomain.com;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name steg.yourdomain.com;
    
    # SSL configuration
    ssl_certificate /etc/letsencrypt/live/steg.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/steg.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    
    # GZip compression
    gzip on;
    gzip_types text/plain text/css text/js text/xml text/javascript application/json application/javascript application/xml+rss;
    gzip_min_length 1000;
    
    # Frontend
    root /home/securesteg/securesteg/frontend/dist;
    
    location / {
        try_files $uri /index.html;
    }
    
    # API proxy
    location /api/ {
        proxy_pass http://backend/;
        proxy_http_version 1.1;
        proxy_set_header Connection "";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for file uploads
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
        
        # Large file upload
        client_max_body_size 100M;
    }
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=embed_limit:10m rate=10r/m;
    location /api/embed {
        limit_req zone=embed_limit burst=20 nodelay;
        proxy_pass http://backend;
    }
    
    # Cache static files
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Disable direct access to uploads
    location /uploads/ {
        deny all;
    }
}
```

### Step 5: SSL Certificate

```bash
# Using Let's Encrypt (free)
sudo certbot certonly --nginx -d steg.yourdomain.com

# Auto-renewal
sudo systemctl enable certbot.timer
sudo systemctl start certbot.timer
```

### Step 6: Systemd Service

```ini
# /etc/systemd/system/securesteg-backend.service

[Unit]
Description=SecureSteg Backend
After=network.target

[Service]
Type=notify
User=securesteg
WorkingDirectory=/home/securesteg/securesteg/backend
Environment="PYTHONUNBUFFERED=1"
Environment="ENVIRONMENT=production"
ExecStart=/home/securesteg/securesteg/backend/venv/bin/python run.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

### Step 7: Start Services

```bash
# Backend
sudo systemctl start securesteg-backend
sudo systemctl enable securesteg-backend

# Nginx
sudo systemctl restart nginx
sudo systemctl enable nginx

# Verify
sudo systemctl status securesteg-backend
curl https://steg.yourdomain.com/api/health
```

---

## Option 2: Docker Deployment

### Dockerfile (Backend)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-libsm6 libxext6 libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY backend/requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY backend/app ./app
COPY backend/run.py .

# Create uploads directory
RUN mkdir -p uploads && chmod 755 uploads

# Expose port
EXPOSE 8000

# Run application
CMD ["python", "run.py"]
```

### Dockerfile (Frontend)

```dockerfile
FROM node:18-alpine AS builder

WORKDIR /app

COPY frontend/package*.json ./
RUN npm install

COPY frontend .
RUN npm run build

# Production stage
FROM node:18-alpine

RUN npm install -g serve

WORKDIR /app

COPY --from=builder /app/dist ./dist

EXPOSE 3000

CMD ["serve", "-s", "dist", "-l", "3000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    volumes:
      - ./backend/uploads:/app/uploads
    environment:
      - ENVIRONMENT=production
    restart: always

  frontend:
    build: ./frontend
    ports:
      - "3000:3000"
    depends_on:
      - backend
    environment:
      - REACT_APP_API_URL=http://backend:8000
    restart: always

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
      - ./ssl:/etc/nginx/ssl:ro
    depends_on:
      - backend
      - frontend
    restart: always
```

### Deploy

```bash
docker-compose build
docker-compose up -d

# Verify
docker-compose ps
docker-compose logs backend
```

---

## Option 3: Kubernetes Deployment

### Deployment Manifest

```yaml
# deployment.yaml

apiVersion: apps/v1
kind: Deployment
metadata:
  name: securesteg-backend
spec:
  replicas: 3
  selector:
    matchLabels:
      app: securesteg-backend
  template:
    metadata:
      labels:
        app: securesteg-backend
    spec:
      containers:
      - name: backend
        image: securesteg:backend-1.0.0
        ports:
        - containerPort: 8000
        env:
        - name: ENVIRONMENT
          value: "production"
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: uploads
          mountPath: /app/uploads
      volumes:
      - name: uploads
        persistentVolumeClaim:
          claimName: securesteg-uploads

---
apiVersion: v1
kind: Service
metadata:
  name: securesteg-backend
spec:
  selector:
    app: securesteg-backend
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
```

### Deploy to K8s

```bash
kubectl apply -f deployment.yaml
kubectl get deployments
kubectl logs deployment/securesteg-backend
```

---

## Monitoring & Logging

### Prometheus Metrics

```python
# Add to fastapi app
from prometheus_client import Counter, Histogram
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

### ELK Stack (Elasticsearch, Logstash, Kibana)

```python
# Structured logging
import logging
from pythonjsonlogger import jsonlogger

logHandler = logging.StreamHandler()
formatter = jsonlogger.JsonFormatter()
logHandler.setFormatter(formatter)
logger = logging.getLogger("securesteg")
logger.addHandler(logHandler)
```

### Health Checks

```yaml
# Kubernetes liveness probe
livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 30
  periodSeconds: 10

# Kubernetes readiness probe
readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
```

---

## Database Integration (Optional)

### SQLAlchemy Setup

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "mysql+pymysql://user:password@localhost/securesteg"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Usage in API
@app.post("/embed")
async def embed_data(db: Session = Depends(get_db)):
    # Log to database (never plaintext messages!)
    db_entry = EmbeddingLog(
        timestamp=datetime.now(),
        payload_size=len(payload),
        detectability=cap_info['estimated_detectability']
    )
    db.add(db_entry)
    db.commit()
```

---

## Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="/backup/securesteg"
DATE=$(date +%Y%m%d_%H%M%S)

# Backup application
tar -czf $BACKUP_DIR/app_$DATE.tar.gz /home/securesteg/securesteg/

# Backup uploads (encrypted)
gpg --encrypt -r backup@example.com \
  /backup/securesteg/app_$DATE.tar.gz

# Upload to S3
aws s3 cp $BACKUP_DIR/app_$DATE.tar.gz.gpg s3://securesteg-backups/
```

### Cron Job

```bash
0 2 * * * /home/securesteg/backup.sh  # Daily at 2 AM
```

---

## Performance Optimization

### Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def calculate_capacity(image_hash: str):
    # Cache expensive calculations
    pass
```

### Async Processing

```python
@app.post("/embed")
async def embed_data(background_tasks: BackgroundTasks):
    # Process in background
    background_tasks.add_task(cleanup_temp_files)
    return response
```

### CDN Integration

```nginx
# CloudFlare or similar
# Cache static frontend files
# Accelerate API calls globally
```

---

## Troubleshooting

### Backend Connection Issues

```bash
# Test connection
curl http://localhost:8000/health

# Check logs
tail -f /var/log/securesteg-backend.log

# Verify firewall
sudo ufw status
sudo ufw allow 8000/tcp
```

### SSL Certificate Issues

```bash
# Verify certificate
openssl s_client -connect steg.yourdomain.com:443

# Renew certificate
sudo certbot renew --dry-run

# Check renewal status
sudo systemctl status certbot.timer
```

### Upload Size Issues

```nginx
# Increase upload limit in nginx.conf
client_max_body_size 100M;

# Increase in FastAPI
@app.post("/embed")
async def embed_data(file: UploadFile = File(...)):
    # Default max size is 100MB
    pass
```

---

## Security Hardening

### Firewall Rules

```bash
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
sudo ufw enable
```

### Fail2Ban

```bash
sudo apt-get install fail2ban

# /etc/fail2ban/jail.local
[sshd]
enabled = true
port = ssh
filter = sshd
logpath = /var/log/auth.log
maxretry = 5
findtime = 600
bantime = 3600
```

### Secrets Management

```bash
# Use environment variables
export API_KEY=$(openssl rand -hex 32)
export DB_PASSWORD=$(openssl rand -base64 32)

# Or use secret manager
vault write secret/securesteg \
  api_key=value \
  db_password=value
```

---

## Scaling Strategies

### Horizontal Scaling

1. Multiple backend instances behind load balancer
2. Shared upload storage (NFS or S3)
3. Redis cache for session management
4. Read replicas for database

### Load Balancing

```nginx
upstream backend_cluster {
    server 192.168.1.10:8000;
    server 192.168.1.11:8000;
    server 192.168.1.12:8000;
    keepalive 32;
}

server {
    location /api/ {
        proxy_pass http://backend_cluster;
        proxy_set_header Connection "";
    }
}
```

---

## Maintenance

### Monthly Tasks

- [ ] Update all packages
- [ ] Review logs for errors
- [ ] Backup verification
- [ ] Security scanning

### Annual Tasks

- [ ] Security audit
- [ ] Capacity planning
- [ ] Disaster recovery drill
- [ ] Performance benchmarking

---

## Support & Resources

- Deployment questions: Check main README
- Technical issues: Review documentation
- Security concerns: See SECURITY.md
- API help: See API.md

---

Last Updated: 2024-03-10
