
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install fastapi uvicorn

# Copy source code
COPY src /app/src
COPY deployment /app/deployment
COPY models /app/models

# Environment
ENV PYTHONPATH=/app
ENV MODEL_PATH=/app/models/constraint-reasoner-v1

# Expose port
EXPOSE 8000

# Run
CMD ["python", "deployment/app.py"]
