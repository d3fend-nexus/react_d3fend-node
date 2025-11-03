FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    yara \
    libyara-dev \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY yara_service.py .
COPY . .

# Create data directories
RUN mkdir -p /data/yara/rules /data/yara/samples /data/yara/cache

# Expose API port
EXPOSE 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8001/api/yara/health || exit 1

# Run YARA service
CMD ["python", "yara_service.py"]
