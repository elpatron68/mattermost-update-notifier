FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy application files
COPY requirements.txt /app
COPY main.py /app
COPY webapp.py /app
COPY templates/ /app/templates/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Create data directory
RUN mkdir -p /app/data

# Default command (can be overridden in docker-compose.yml)
CMD ["python", "webapp.py"]
