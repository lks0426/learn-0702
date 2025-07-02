# Stage 1: Build stage (if needed for compilation or installing build dependencies)
# For a simple Python app, this might not be strictly necessary, but good practice for complex apps.
# For now, we'll use a single stage for simplicity.

# Stage 2: Runtime stage
FROM python:3.9-slim

WORKDIR /app

# Set environment variables (can be overridden by Docker Compose or runtime)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install system dependencies if any (e.g., for psycopg2, you might need libpq-dev)
# RUN apt-get update && apt-get install -y some-package

# Copy requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY ./app /app/app

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
# Note: For development, uvicorn app.main:app --reload is fine.
# For production, gunicorn is often preferred.
# Example with gunicorn:
# CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "-w", "4", "-b", "0.0.0.0:8000", "app.main:app"]
# For now, using uvicorn for simplicity, matching local development.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
