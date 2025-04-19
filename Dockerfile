FROM ghcr.io/astral-sh/uv:latest

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

RUN uv sync


# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Set environment variables
ENV PORT=5000

# Expose the port
EXPOSE 5000

RUN uv run download_whisper.py

RUN chmod +x start.sh


ENTRYPOINT ["./start.sh"]

