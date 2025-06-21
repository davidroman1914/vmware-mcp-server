FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements for VMware SDK
COPY requirements.txt .

# Install VMware vSphere SDK dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir git+https://github.com/vmware/vsphere-automation-sdk-python.git

# Copy scripts for standalone testing
COPY scripts/ ./scripts/

# Copy MCP server files
COPY mcp-server/ ./mcp-server/

# Install MCP server dependencies directly
RUN pip install --no-cache-dir mcp>=1.9.4

# Make scripts executable
WORKDIR /app
RUN chmod +x scripts/*.py
RUN chmod +x mcp-server/server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command - show help
CMD ["python", "scripts/list_vms.py", "--help"] 