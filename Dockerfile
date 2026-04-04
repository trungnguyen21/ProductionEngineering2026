FROM python:3.13-slim

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv for fast dependency management
RUN pip install --no-cache-dir uv

# Copy dependency files first for layer caching
COPY pyproject.toml uv.lock ./

# Install dependencies into the system Python (no venv needed in container)
RUN uv pip install --system --no-cache -r pyproject.toml

# Copy application code
COPY . .

EXPOSE 8000

# Use gunicorn for production (more stable than Flask dev server)
CMD ["python", "-m", "gunicorn", "--workers", "2", "--bind", "0.0.0.0:8000", "--timeout", "30", "run:app"]
