# Centralized API Logging System

This document explains how to integrate the centralized API logging system across all Alchemist services.

## Overview

The centralized API logging system automatically logs all API requests and responses to a single Firestore collection (`api_logs`) for unified monitoring, debugging, and analytics.

## Features

- **Unified Logging**: All API calls across all services logged to single collection
- **Request Tracking**: Each request gets unique ID and correlation ID for tracing
- **Error Capture**: Automatic error message and stack trace logging
- **Performance Monitoring**: Response times, request/response sizes
- **Security**: Sensitive data filtering (passwords, tokens, etc.)
- **Batch Processing**: Efficient batch writes for performance
- **Rate Limiting**: Prevents log flooding
- **Configurable**: Exclude health checks, configure body logging, etc.

## Data Structure

All logs are stored in the `api_logs` Firestore collection with the following structure:

```json
{
  "req_id": "unique-request-id",
  "corr_id": "correlation-id",
  "svc": "service-name",
  "svc_ver": "service-version",
  "method": "GET",
  "endpoint": "/api/agents",
  "url": "https://service.com/api/agents?page=1",
  "ua": "user-agent-string",
  "ip": "client-ip",
  "uid": "user-id-if-authenticated",
  "ts": "2025-06-25T10:00:00Z",
  "resp_ms": 150.5,
  "status": 200,
  "resp_size": 1024,
  "err_msg": "error message if failed",
  "err_type": "ValidationError",
  "stack": "stack trace for server errors",
  "req_size": 512,
  "req_ct": "application/json",
  "meta": {
    "query_params": {"page": 1},
    "headers": {"content-type": "application/json"}
  }
}
```

## Integration Steps

### 1. Install Dependencies

Ensure your service has access to the shared library:

```python
from alchemist_shared.middleware.api_logging_middleware import (
    setup_api_logging_middleware,
    shutdown_api_logging
)
```

### 2. Update Service Main File

For each service's main.py (or app.py), make these changes:

#### A. Import the middleware

```python
try:
    from alchemist_shared.middleware.api_logging_middleware import (
        setup_api_logging_middleware,
        shutdown_api_logging
    )
    API_LOGGING_AVAILABLE = True
except ImportError:
    logging.warning("API logging middleware not available")
    API_LOGGING_AVAILABLE = False
```

#### B. Add middleware to FastAPI app

```python
# Add API logging middleware FIRST (before other middleware)
if API_LOGGING_AVAILABLE:
    setup_api_logging_middleware(
        app, 
        service_name="your-service-name",
        service_version="1.0.0",
        exclude_health_checks=True,      # Skip /health, /metrics, etc.
        log_request_body=False,          # Usually False for performance
        log_response_body=False,         # Usually False for performance
        max_body_size=1024              # Max bytes to log if body logging enabled
    )
```

#### C. Add shutdown handler

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code...
    yield
    
    # Shutdown
    if API_LOGGING_AVAILABLE:
        await shutdown_api_logging()
        logger.info("API logging shut down and logs flushed")
```

### 3. Service-Specific Integration

#### agent-engine
```python
setup_api_logging_middleware(app, "agent-engine", "1.0.0")
```

#### billing-service
```python
setup_api_logging_middleware(app, "billing-service", "1.0.0")
```

#### agent-tuning-service
```python
setup_api_logging_middleware(app, "agent-tuning-service", "1.0.0")
```

#### knowledge-vault
```python
setup_api_logging_middleware(app, "knowledge-vault", "1.0.0")
```

#### agent-bridge
```python
setup_api_logging_middleware(app, "agent-bridge", "1.0.0")
```

#### prompt-engine
```python
setup_api_logging_middleware(app, "prompt-engine", "1.0.0")
```

#### sandbox-console
```python
setup_api_logging_middleware(app, "sandbox-console", "1.0.0")
```

## Configuration Options

### Basic Configuration
```python
setup_api_logging_middleware(
    app,
    service_name="my-service",           # Required: Service name
    service_version="1.0.0",             # Optional: Service version
)
```

### Advanced Configuration
```python
setup_api_logging_middleware(
    app,
    service_name="my-service",
    service_version="1.0.0",
    exclude_paths={"/custom-health"},    # Additional paths to exclude
    exclude_health_checks=True,          # Skip standard health checks
    log_request_body=False,              # Log request bodies (use carefully)
    log_response_body=False,             # Log response bodies (use carefully)
    max_body_size=1024                   # Max body size to log (bytes)
)
```

### Security Configuration

The system automatically filters sensitive data:

**Sensitive Headers** (automatically redacted):
- `authorization`, `cookie`, `x-api-key`, `x-auth-token`, `bearer`

**Sensitive Query Parameters** (automatically redacted):
- `password`, `token`, `secret`, `key`, `credential`

## Usage in Endpoints

### Getting Request Information

```python
from fastapi import Request
from alchemist_shared.middleware.api_logging_middleware import (
    get_current_request_id,
    get_current_correlation_id_from_request
)

@app.get("/api/data")
async def get_data(request: Request):
    request_id = get_current_request_id(request)
    correlation_id = get_current_correlation_id_from_request(request)
    
    # Use these IDs for additional logging or tracing
    logger.info(f"Processing request {request_id}", extra={
        "request_id": request_id,
        "correlation_id": correlation_id
    })
    
    return {"data": "example"}
```

### Adding Custom Metadata

You can add custom metadata to specific endpoints by storing it in request state:

```python
@app.post("/api/agents")
async def create_agent(request: Request, agent_data: AgentData):
    # Add custom metadata that will be included in logs
    if not hasattr(request.state, 'api_log_metadata'):
        request.state.api_log_metadata = {}
    
    request.state.api_log_metadata.update({
        "agent_type": agent_data.type,
        "user_plan": "premium"
    })
    
    # Your endpoint logic...
    return {"id": "agent-123"}
```

## Querying Logs

### Using the API Logging Service

```python
from alchemist_shared.services.api_logging_service import get_api_logging_service
from alchemist_shared.models.api_log_models import APILogQuery
from datetime import datetime, timedelta

# Get the logging service
logging_service = get_api_logging_service()

# Query recent errors
query = APILogQuery(
    service_name="agent-engine",
    errors_only=True,
    start_time=datetime.utcnow() - timedelta(hours=1),
    limit=50
)

recent_errors = await logging_service.query_logs(query)

# Get performance stats
stats = await logging_service.get_api_stats(
    start_time=datetime.utcnow() - timedelta(hours=24),
    end_time=datetime.utcnow(),
    service_name="agent-engine"
)
```

### Common Queries

#### All errors in last hour
```python
query = APILogQuery(
    errors_only=True,
    start_time=datetime.utcnow() - timedelta(hours=1)
)
```

#### Slow requests (>1 second)
```python
query = APILogQuery(
    min_response_time_ms=1000,
    start_time=datetime.utcnow() - timedelta(hours=1)
)
```

#### Specific user's requests
```python
query = APILogQuery(
    user_id="user-123",
    start_time=datetime.utcnow() - timedelta(days=1)
)
```

#### Specific endpoint performance
```python
query = APILogQuery(
    service_name="agent-engine",
    endpoint="/api/agents",
    method="POST"
)
```

## Performance Considerations

### Batch Processing
- Logs are batched for efficient Firestore writes
- Default batch size: 100 requests
- Default flush interval: 5 seconds

### Rate Limiting
- Maximum 1000 logs per minute per service
- Prevents log flooding during traffic spikes

### Storage Optimization
- Field names are abbreviated in Firestore for efficiency
- Automatic log retention (30 days default, 90 days for errors)

### Exclusions
- Health check endpoints excluded by default
- Request/response bodies not logged by default
- Sensitive data automatically redacted

## Monitoring and Alerting

### Key Metrics to Monitor

1. **Error Rate**: Percentage of 4xx/5xx responses
2. **Response Time**: P95 and P99 response times
3. **Request Volume**: Requests per minute/hour
4. **Service Health**: Availability per service

### Sample Monitoring Queries

```python
# Daily error rate
stats = await logging_service.get_api_stats(
    start_time=datetime.utcnow() - timedelta(days=1),
    end_time=datetime.utcnow()
)
error_rate = stats.error_rate_percent

# Service performance comparison
for service in ["agent-engine", "billing-service", "knowledge-vault"]:
    service_stats = await logging_service.get_api_stats(
        start_time=datetime.utcnow() - timedelta(hours=1),
        end_time=datetime.utcnow(),
        service_name=service
    )
    print(f"{service}: {service_stats.avg_response_time_ms}ms avg")
```

## Maintenance

### Log Cleanup

Automatically clean up old logs:

```python
# Clean up logs older than 30 days
await logging_service.cleanup_old_logs(retention_days=30)
```

### Manual Cleanup for Specific Services

```python
# Clean up specific service logs
from alchemist_shared.constants.collections import Collections
from alchemist_shared.database.firebase_client import get_firestore_client

db = get_firestore_client()
old_logs = db.collection(Collections.API_LOGS)\
    .where("svc", "==", "old-service")\
    .where("ts", "<", cutoff_date)\
    .limit(1000)

# Delete in batches...
```

## Troubleshooting

### Common Issues

1. **Logs not appearing**: Check Firestore permissions and service account
2. **High storage usage**: Reduce retention period or disable body logging
3. **Performance impact**: Ensure batching is enabled and exclude high-frequency endpoints
4. **Missing correlation IDs**: Check if middleware is added before other middleware

### Debug Logging

Enable debug logging to see middleware activity:

```python
import logging
logging.getLogger("alchemist_shared.middleware.api_logging_middleware").setLevel(logging.DEBUG)
logging.getLogger("alchemist_shared.services.api_logging_service").setLevel(logging.DEBUG)
```

## Example Firestore Query

To query logs directly in Firestore:

```javascript
// Get all errors from agent-engine in last hour
db.collection('api_logs')
  .where('svc', '==', 'agent-engine')
  .where('status', '>=', 400)
  .where('ts', '>=', new Date(Date.now() - 3600000))
  .orderBy('ts', 'desc')
  .limit(50)
```

## Security Notes

- All sensitive data is automatically redacted
- Request/response bodies are not logged by default
- User IDs are logged but not personal information
- IP addresses are logged for debugging but should comply with privacy policies
- Consider data retention policies for compliance