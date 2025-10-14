# Use Python 3.9 slim image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 8080 (Cloud Run default)
ENV PORT=8080
EXPOSE 8080

# Run the server directly with src.api module
CMD exec uvicorn src.api:app --host 0.0.0.0 --port ${PORT}

