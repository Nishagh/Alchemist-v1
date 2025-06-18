# Alchemist Monitor Service

A dedicated monitoring service for the Alchemist platform that continuously monitors all microservices and stores metrics in Firestore.

## Features

- **Automated Health Monitoring**: Checks all 9 Alchemist services every 30 seconds
- **Firestore Integration**: Stores metrics and health data for dashboard consumption
- **Scheduled Tasks**: Automated monitoring, summary generation, and data cleanup
- **REST API**: Endpoints for manual health checks and metrics retrieval
- **Real-time Monitoring**: Background scheduler ensures continuous monitoring

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Admin         │────│  Monitor Service │────│   Firestore     │
│   Dashboard     │    │                  │    │   Database      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                │ Health Checks
                                ▼
                       ┌─────────────────┐
                       │  Alchemist      │
                       │  Services (9)   │
                       └─────────────────┘
```

## API Endpoints

### Monitoring
- `GET /api/monitoring/health` - Monitor service health
- `GET /api/monitoring/services/health` - Get all service health status
- `GET /api/monitoring/summary` - Get monitoring summary
- `GET /api/monitoring/services/{name}/health` - Get specific service health
- `POST /api/monitoring/check/all` - Trigger manual health check
- `POST /api/monitoring/check/{name}` - Trigger service-specific check
- `GET /api/monitoring/services` - List all monitored services

### Scheduler
- `GET /api/scheduler/status` - Get scheduler status
- `POST /api/scheduler/trigger/{job_id}` - Manually trigger job

## Monitored Services

1. **Agent Engine** - Core orchestration service
2. **Knowledge Vault** - Document processing and search
3. **Agent Bridge** - WhatsApp integration
4. **Agent Launcher** - Deployment automation
5. **Tool Forge** - MCP server management
6. **Agent Studio** - Web interface
7. **Prompt Engine** - AI prompt processing
8. **Sandbox Console** - Testing environment
9. **MCP Config Generator** - Configuration service

## Scheduled Jobs

- **Health Check**: Every 30 seconds - Check all service health
- **Summary Generation**: Every 5 minutes - Generate monitoring summaries
- **Data Cleanup**: Daily at 2 AM - Remove old metrics data
- **Heartbeat**: Every minute - Scheduler health verification

## Configuration

### Environment Variables
- `GOOGLE_APPLICATION_CREDENTIALS` - Path to Firebase service account key
- `PORT` - Service port (default: 8080)
- `ENVIRONMENT` - Deployment environment

### Monitoring Configuration
- Check interval: 30 seconds
- Health check timeout: 10 seconds
- Data retention: 30 days
- Max retries: 3

## Deployment

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the service
python main.py
```

### Docker
```bash
# Build image
docker build -t alchemist-monitor-service .

# Run container
docker run -p 8080:8080 alchemist-monitor-service
```

### Google Cloud Run
```bash
# Deploy using Cloud Build
gcloud builds submit --config cloudbuild.yaml
```

## Data Storage

### Firestore Collections
- `monitoring/health_checks/results` - Individual health check results
- `monitoring/metrics/services` - Service metrics data
- `monitoring/summaries/daily` - Daily monitoring summaries
- `monitoring/scheduler` - Scheduler heartbeat data

### Data Retention
- Raw metrics: 30 days
- Health checks: 30 days
- Summaries: 90 days

## Benefits

- **Eliminates ping multiplication** - Single service monitors all others
- **Centralized metrics** - All data stored in Firestore
- **Real-time monitoring** - Continuous automated health checks
- **Dashboard integration** - Provides data for admin dashboard
- **Scalable architecture** - Independent monitoring service
- **Data persistence** - Historical metrics and trends
- **Automated cleanup** - Manages data retention automatically

## Integration with Admin Dashboard

The admin dashboard now consumes data from this monitor service instead of directly pinging services:

```javascript
// Old approach (multiple pings)
services.forEach(service => ping(service.url))

// New approach (single API call)
fetch('/api/monitoring/services/health')
```

This eliminates the N×M ping problem and provides richer monitoring data.