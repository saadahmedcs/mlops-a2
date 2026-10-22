# Use lightweight official Python image
FROM python:3.11-slim

# Set working directory inside container
WORKDIR /app

# Install git (required for cloning target repositories during audits)
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Default command entry point
ENTRYPOINT ["python", "agent.py"]