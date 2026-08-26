FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for OpenCV, EasyOCR, and model compiling
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install Python packages
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY . .

# Set Python Path
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run entry point
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
