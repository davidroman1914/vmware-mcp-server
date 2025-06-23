FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the mcp-server directory
COPY mcp-server/ ./mcp-server/

# Copy the main FastMCP server
COPY fastmcp_server.py .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the FastMCP server
CMD ["python", "fastmcp_server.py"] 