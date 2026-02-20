FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    openjdk-17-jdk \
    wget \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install PMD
RUN wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F7.0.0/pmd-dist-7.0.0-bin.zip \
    && unzip pmd-dist-7.0.0-bin.zip -d /opt \
    && rm pmd-dist-7.0.0-bin.zip \
    && ln -s /opt/pmd-bin-7.0.0/bin/pmd /usr/local/bin/pmd

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p data/raw data/processed data/sample results/charts results/reports logs

# Set entrypoint
ENTRYPOINT ["python", "run_pipeline.py"]
CMD ["--all"]
