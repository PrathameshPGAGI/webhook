FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Install system dependencies for audio processing and ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application files
COPY . .

# Expose the port for WebSocket server (Render uses PORT env variable)
EXPOSE 3456

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Create a startup script to handle Render's PORT environment variable
RUN echo '#!/bin/bash\n\
PORT=${PORT:-3456}\n\
echo "Starting WebSocket server on port $PORT"\n\
python websocket.py --port $PORT --model base --device cpu\n\
' > /app/start.sh && chmod +x /app/start.sh

# Use the startup script as the entry point
CMD ["/app/start.sh"]
