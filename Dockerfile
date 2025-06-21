FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install VMware vSphere Automation SDK for Python from GitHub
RUN pip install --no-cache-dir git+https://github.com/vmware/vsphere-automation-sdk-python.git

# Copy the script
COPY list_vms.py .

# Make the script executable
RUN chmod +x list_vms.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "list_vms.py", "--help"] 