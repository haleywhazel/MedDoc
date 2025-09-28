# backend/Dockerfile
FROM python:3.13-slim

WORKDIR /app

# Install system dependencies including curl for health check
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from project root and install Python dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy the entire project structure to maintain imports
COPY . .

# Set Python path to include the project root
ENV PYTHONPATH=/app

# Create logs directory
RUN mkdir -p /app/logs

# Change working directory to backend
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Health check using the working endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Run the application from backend directory
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
