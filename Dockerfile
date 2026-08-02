FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application - invalidate cache on every deploy
COPY api/ .

# Create data directory
RUN mkdir -p /data && chmod +x entrypoint.sh

# Set environment
ENV DATA_DIR=/data
ENV FLASK_ENV=production
ENV PORT=5000

EXPOSE 5000

CMD ["./entrypoint.sh"]
