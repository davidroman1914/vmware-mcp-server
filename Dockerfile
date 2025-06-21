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

# Copy pyproject.toml and lock file
COPY pyproject.toml uv.lock* ./

# Install Python dependencies using uv
RUN uv sync --frozen

# Copy the application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command to run the MCP server
CMD ["uv", "run", "python", "main.py"] 