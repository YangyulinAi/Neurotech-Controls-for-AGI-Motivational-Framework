# Multi-stage Dockerfile for EEG Emotion Prediction System

# Stage 1: Node.js dependencies and build
FROM node:18-alpine AS node-builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Python environment setup
FROM python:3.11-slim AS python-base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js in Python image
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs

WORKDIR /app

# Copy Python requirements and install
COPY python-requirements.txt ./
RUN pip install --no-cache-dir -r python-requirements.txt

# Copy Node.js build and dependencies from previous stage
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/package*.json ./

# Copy application source
COPY . .

# Create necessary directories
RUN mkdir -p data/training\ set model model_training

# Set permissions
RUN chmod +x analyze_set_file.py

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:5000/ || exit 1

# Start command
CMD ["npm", "start"]