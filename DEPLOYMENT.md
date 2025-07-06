# Deployment Guide

This document provides detailed deployment instructions for different environments.

## Local Development

### Quick Start
```bash
# Linux/macOS
./setup.sh && ./start.sh

# Windows
setup.bat && start.bat
```

### Manual Setup
```bash
# 1. Install dependencies
npm install
pip install -r python-requirements.txt

# 2. Start development server
npm run dev

# 3. Open browser
open http://localhost:5000
```

## Production Deployment

### Docker Deployment (Recommended)

1. **Build and run with Docker Compose:**
```bash
docker-compose up -d
```

2. **Or build manually:**
```bash
docker build -t eeg-emotion-system .
docker run -p 5000:5000 -v $(pwd)/data:/app/data eeg-emotion-system
```

### Traditional Server Deployment

1. **Install dependencies:**
```bash
npm install --production
pip install -r python-requirements.txt
```

2. **Build the application:**
```bash
npm run build
```

3. **Start with PM2 (recommended for production):**
```bash
npm install -g pm2
pm2 start ecosystem.config.js
```

### Cloud Deployment

#### AWS EC2
```bash
# Update system
sudo yum update -y

# Install Node.js
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo yum install -y nodejs

# Install Python
sudo yum install -y python3 python3-pip

# Clone and setup
git clone <your-repo>
cd eeg-emotion-prediction
./setup.sh

# Start with PM2
npm install -g pm2
pm2 start npm --name "eeg-emotion" -- run dev
pm2 startup
pm2 save
```

#### Google Cloud Platform
```bash
# Create VM instance
gcloud compute instances create eeg-emotion-vm \
  --machine-type=e2-standard-2 \
  --image-family=ubuntu-2004-lts \
  --image-project=ubuntu-os-cloud

# SSH and setup
gcloud compute ssh eeg-emotion-vm
# ... follow standard setup instructions
```

#### Azure
```bash
# Create resource group
az group create --name eeg-emotion-rg --location eastus

# Create VM
az vm create \
  --resource-group eeg-emotion-rg \
  --name eeg-emotion-vm \
  --image UbuntuLTS \
  --admin-username azureuser \
  --generate-ssh-keys

# Setup application
# ... follow standard setup instructions
```

## Environment Configuration

### Required Environment Variables
```bash
# .env file
NODE_ENV=production
PORT=5000
PYTHON_PATH=/usr/bin/python3
MODEL_PATH=./model/va_regressor.onnx
```

### Production Security
1. **Use HTTPS in production:**
```javascript
// In server configuration
const https = require('https');
const fs = require('fs');

const options = {
  key: fs.readFileSync('path/to/private-key.pem'),
  cert: fs.readFileSync('path/to/certificate.pem')
};

https.createServer(options, app).listen(443);
```

2. **Set up reverse proxy with Nginx:**
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

## Monitoring and Maintenance

### Health Checks
```bash
# Check if service is running
curl http://localhost:5000/api/health

# Check logs
pm2 logs eeg-emotion
```

### Backup Strategy
```bash
# Backup training data and models
tar -czf backup-$(date +%Y%m%d).tar.gz data/ model/ model_training/
```

### Updates
```bash
# Update application
git pull origin main
npm install
pip install -r python-requirements.txt
pm2 restart eeg-emotion
```

## Troubleshooting

### Common Issues

1. **Port 5000 in use:**
```bash
sudo lsof -i :5000
sudo kill -9 <PID>
```

2. **Python dependencies:**
```bash
pip install --upgrade pip
pip install -r python-requirements.txt --force-reinstall
```

3. **Node.js memory issues:**
```bash
export NODE_OPTIONS="--max-old-space-size=4096"
npm run dev
```

4. **Permission issues:**
```bash
sudo chown -R $USER:$USER .
chmod +x *.sh *.py
```

### Performance Optimization

1. **Enable gzip compression:**
```javascript
const compression = require('compression');
app.use(compression());
```

2. **Use CDN for static assets**

3. **Optimize Docker image:**
```dockerfile
# Use multi-stage build
# Minimize layers
# Use .dockerignore
```

4. **Database optimization (if using persistent storage):**
```javascript
// Connection pooling
// Query optimization
// Indexing
```