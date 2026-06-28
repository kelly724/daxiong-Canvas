FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Pillow
RUN apt-get update && apt-get install -y --no-install-recommends \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    pillow \
    requests \
    pydantic \
    python-dotenv \
    python-multipart \
    websockets \
    watchfiles

# Copy application code (data/assets are runtime-generated, not in repo)
COPY main.py .
COPY static/ static/
COPY workflows/ workflows/
COPY tools/ tools/
COPY VERSION .
COPY LICENSE .

# Ensure runtime directories exist
RUN mkdir -p data assets/output output API

# Expose port (cloud platforms override via PORT env var)
EXPOSE 3000
ENV PORT=3000

# Start the server
CMD ["python", "main.py"]
