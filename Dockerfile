FROM python:3.12-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/


# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    redis-server \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app


# Copy the rest of the application
COPY . .

RUN uv sync --frozen


# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV PORT=5000
ENV REDIS_HOST=localhost
ENV REDIS_PORT=6379

# Expose the ports
EXPOSE 5000
EXPOSE 6379

RUN uv run download_whisper.py

RUN chmod +x start.sh

# Create a new script to start both Redis and the application
RUN echo '#!/bin/bash\nservice redis-server start\n./start.sh' > /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

