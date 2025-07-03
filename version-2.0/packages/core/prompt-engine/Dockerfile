FROM python:3.12-slim

WORKDIR /app

# Copy shared libraries first (for better caching)
COPY shared/ /app/shared/

# Install shared libraries
RUN cd /app/shared && pip install -e .

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=True
ENV ENVIRONMENT=production

# Run the service with uvicorn directly
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT
