# Use a minimal Python image
FROM python:3.10-slim

# Set a working directory
WORKDIR /app

# Install needed system dependencies (e.g. build tools)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY app/ ./app
COPY run.py credentials.json ./

# Create the media directory (and camera subfolders at runtime)
RUN mkdir -p media

# Expose the port that the Flask app will listen on
ARG PORT=5001
ENV PORT=${PORT}
EXPOSE ${PORT}

# Use Gunicorn to serve the run entrypoint; bind to 0.0.0.0:${PORT}
CMD ["gunicorn", "run:app", "-b", "0.0.0.0:5001", "--workers", "1", "--timeout", "120"]
