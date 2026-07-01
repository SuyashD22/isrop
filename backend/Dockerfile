FROM python:3.10-slim

WORKDIR /app

# Install system dependencies (only curl is needed for healthcheck)
# OpenCV is headless, so it doesn't need libgl1/libglib
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for runtime use
RUN mkdir -p /app/checkpoints/inpainting /app/checkpoints/cloud_seg /app/uploads

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Run with uvicorn — use $PORT from Render (falls back to 8000 for local Docker Compose)
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}"]
