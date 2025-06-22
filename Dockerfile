FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install uv for dependency management
RUN pip install uv

# Copy pyproject.toml and lock file from mcp-server
COPY mcp-server/pyproject.toml mcp-server/uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy all Python modules and files from mcp-server
COPY mcp-server/*.py ./

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Create non-root user
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# Expose port (if needed for debugging)
EXPOSE 8000

# Run the MCP server using uv
CMD ["uv", "run", "python", "server.py"] 