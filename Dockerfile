FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY api/ .

# Create data directory
RUN mkdir -p /data

# Set environment
ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=8080

EXPOSE 8080

CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--workers", "4", "--timeout", "120"]
