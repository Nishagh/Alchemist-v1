FROM python:3.12-slim

WORKDIR /app

# Copy shared libraries first (for better caching)
COPY shared/ /app/shared/

# Install shared libraries
RUN cd /app/shared && pip install -e .

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Set environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1

# Run the server with Uvicorn
CMD exec uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1
