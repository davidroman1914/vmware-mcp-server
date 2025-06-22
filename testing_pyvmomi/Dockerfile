FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy test scripts
COPY *.py ./

# Set environment variables for vCenter connection (non-sensitive)
ENV VCENTER_HOST=vcenter.example.com
ENV VCENTER_USER=administrator@vsphere.local
ENV VCENTER_INSECURE=false

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Default command
CMD ["python", "test_vm_operations.py"] 