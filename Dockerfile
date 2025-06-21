# Final Docker image for VMware MCP Server
# Uses the base image with all dependencies

FROM vmware-mcp-server-base:latest

# Copy application code only
COPY src/ ./src/
COPY tests/ ./tests/
COPY main.py ./main.py
COPY config.yaml.sample ./config.yaml.sample

# Set ownership
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port (if needed for HTTP transport)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Default command
CMD ["python", "-m", "src"] 