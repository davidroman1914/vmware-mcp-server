FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir fastmcp

# Copy the mcp-server directory
COPY mcp-server/ ./mcp-server/

# Copy additional test files
COPY minimal_mcp_server.py .
COPY test_mcp_client.py .
COPY fastmcp_server.py .
COPY simple_fastmcp_server.py .

# Make server executable
RUN chmod +x mcp-server/server.py

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server
CMD ["python", "mcp-server/server.py"] 