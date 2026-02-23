FROM python:3.11-slim

# Link package to GitHub repository (required for GITHUB_TOKEN push permissions)
LABEL org.opencontainers.image.source=https://github.com/elpatron68/mattermost-update-notifier
LABEL org.opencontainers.image.description="Mattermost Update Notifier - Web admin interface and automatic update checker"
LABEL org.opencontainers.image.licenses=MIT

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
