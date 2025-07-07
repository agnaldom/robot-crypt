# Multi-stage build for Robot-Crypt FastAPI
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Production stage
FROM python:3.11-slim as production

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    curl \
    netcat-openbsd \
    jq \
    procps \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create app user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set work directory
WORKDIR /app

# Copy application code
COPY . .

# Copy entrypoint script and set permissions (before switching user)
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

# Change ownership to appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Default environment variables
ENV SIMULATION_MODE=true
ENV USE_TESTNET=false
ENV DEBUG=false
ENV HOST=0.0.0.0
ENV PORT=8080
# Log configuration
ENV LOG_LEVEL=info
ENV LOG_FORMAT=structured
ENV LOG_COLORS=true
ENV SHOW_SYSTEM_INFO=true

# Set entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (API mode)
CMD ["api"]
