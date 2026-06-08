FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for pyswisseph and geopy
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libffi-dev \
    libssl-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir $(grep -v '^#' requirements.txt | grep -v '^$') && \
    pip install --no-cache-dir pyswisseph || echo "pyswisseph not available, using fallback"

# Copy application code
COPY . .

# Create non-root user
RUN adduser --disabled-password --gecos "" stellarium && \
    chown -R stellarium:stellarium /app

USER stellarium

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
