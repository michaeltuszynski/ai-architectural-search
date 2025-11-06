# Multi-stage build for AI Architectural Search System
FROM python:3.9-slim as builder

# Set working directory
WORKDIR /app

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install runtime system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder stage
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p images logs

# Set environment variables for production
ENV PYTHONPATH=/app:/app/src
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Create entrypoint script that handles Railway's PORT variable and sets PYTHONPATH
RUN printf '#!/bin/sh\nexport PYTHONPATH=/app:/app/src\nexec streamlit run app.py --server.port=${PORT:-8501} --server.address=0.0.0.0\n' > /entrypoint.sh && chmod +x /entrypoint.sh

# Run the application using entrypoint script
ENTRYPOINT ["/entrypoint.sh"]