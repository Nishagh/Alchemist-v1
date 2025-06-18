FROM python:3.12-slim

WORKDIR /app

# Copy requirements first for better caching
COPY sandbox-console/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY sandbox-console/ .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the server with Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
