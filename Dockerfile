# Dockerfile
FROM python:3.12-slim

# Set workdir
WORKDIR /app

# Install dependencies + pg_dump
RUN apt-get update && apt-get install -y postgresql-client && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Create dumps folder
RUN mkdir -p dumps

# Run scraper (scheduler will run in background)
CMD ["python", "main.py"]