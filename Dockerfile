FROM python:3.14-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY msp360-mcp /app/msp360-mcp
COPY docs/rmm-openapi.json /app/docs/rmm-openapi.json
COPY scripts /app/scripts
COPY test_mcp_v2.py /app/test_mcp_v2.py

STOPSIGNAL SIGTERM

ENTRYPOINT ["python", "msp360-mcp/main.py"]
