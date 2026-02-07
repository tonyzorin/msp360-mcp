FROM python:3.12-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY msp360-mcp /app/msp360-mcp

# Ensure Docker sends SIGTERM on 'docker stop' (default, explicit for clarity)
STOPSIGNAL SIGTERM

# Default entry point for STDIO mode
ENTRYPOINT ["python", "msp360-mcp/main.py"]