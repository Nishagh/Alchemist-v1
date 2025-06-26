# Universal Agent Deployment Service

A Cloud Run service that orchestrates universal agent deployments with real-time progress tracking and LLM-based optimizations.

## Features

- **Universal Agent Deployment**: Deploy any agent type with automatic domain detection
- **LLM-Based Optimizations**: Automatic tool and prompt optimizations based on agent domain
- **Real-time Progress Tracking**: Live deployment status with detailed progress steps
- **Firestore Integration**: Updates agent status and deployment history
- **RESTful API**: Easy integration with existing systems
- **Background Processing**: Non-blocking deployment execution

## Quick Start

### 1. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Copy required files (done automatically by script)
cp ../.env .

# Run locally
python main.py
```

### 2. Deploy to Cloud Run

```bash
# Make deployment script executable
chmod +x deploy-service.sh

# Deploy the service
./deploy-service.sh
```

### 3. Test the Service

```bash
# Test locally
python test-local.py

# Test deployed service
curl https://your-service-url/healthz
```

## API Reference

### Deploy Agent

Start a new agent deployment:

```bash
curl -X POST "https://your-service-url/api/deploy" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "your-agent-id"}'
```

**Response:**
```json
{
  "deployment_id": "uuid",
  "status": "queued",
  "message": "Universal agent deployment queued successfully"
}
```

### Check Deployment Status

Monitor deployment progress:

```bash
curl "https://your-service-url/api/deployment/{deployment_id}/status"
```

**Response:**
```json
{
  "deployment_id": "uuid",
  "agent_id": "string",
  "status": "processing",
  "progress_percentage": 75,
  "current_step": "Deploying universal agent to Cloud Run",
  "deployment_type": "universal",
  "optimizations_applied": true,
  "created_at": "2025-06-13T10:00:00Z",
  "updated_at": "2025-06-13T10:05:00Z"
}
```

### List Deployments

Get deployment history with filtering:

```bash
# All deployments
curl "https://your-service-url/api/deployments"

# Filter by status
curl "https://your-service-url/api/deployments?status=completed"

# Filter by agent
curl "https://your-service-url/api/deployments?agent_id=your-agent-id"
```

### Agent Deployment Status

Get latest deployment for a specific agent:

```bash
curl "https://your-service-url/api/agent/{agent_id}/deployment-status"
```

## Deployment Steps

The service tracks detailed progress through these steps:

1. **Initializing universal deployment** (5%)
2. **Loading configuration with LLM optimizations** (15%)
3. **Validating agent configuration** (25%)
4. **Generating universal agent code with dynamic optimizations** (40%)
5. **Building universal container image** (60%)
6. **Deploying universal agent to Cloud Run** (80%)
7. **Universal deployment completed successfully** (100%)

## Configuration

### Environment Variables

Required in `.env` file:

```bash
PROJECT_ID=your-gcp-project-id
OPENAI_API_KEY=your-openai-api-key
REGION=us-central1
```

### Firebase Credentials

Place `firebase-credentials.json` in the service directory for Firestore access.

## Architecture

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│    Client/UI        │    │  Deployment Service  │    │  Universal Agent    │
│                     │    │                      │    │                     │
│ • REST API calls    │────│ • Progress tracking  │────│ • Dynamic config    │
│ • Status monitoring │    │ • Background tasks   │    │ • LLM optimizations │
│ • Error handling    │    │ • Firestore updates │    │ • Auto deployment   │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
                                       │
                                       ▼
                            ┌──────────────────────┐
                            │     Firestore        │
                            │                      │
                            │ • Deployment status  │
                            │ • Agent configs      │
                            │ • Progress tracking  │
                            └──────────────────────┘
```

## Firestore Schema

### Agent Deployments Collection

```javascript
// Collection: agent_deployments
{
  "deployment_id": "uuid",
  "agent_id": "string",
  "status": "queued|processing|completed|failed",
  "progress_percentage": 0-100,
  "current_step": "string",
  "deployment_type": "universal",
  "optimizations_applied": boolean,
  "service_url": "https://...",
  "error_message": "string",
  "created_at": timestamp,
  "updated_at": timestamp
}
```

### Agent Status Update

```javascript
// Collection: agents/{agent_id}
{
  "universal_deployment": {
    "deployment_id": "uuid",
    "status": "completed",
    "service_url": "https://...",
    "deployment_type": "universal",
    "optimizations_applied": true,
    "updated_at": timestamp
  }
}
```

## Error Handling

The service provides detailed error information:

- **Configuration errors**: Missing environment variables
- **Agent validation errors**: Invalid agent configurations
- **Build errors**: Container build failures
- **Deployment errors**: Cloud Run deployment issues
- **Firestore errors**: Database update failures

All errors are logged and returned in API responses with appropriate HTTP status codes.

## Monitoring

### Health Check

```bash
curl "https://your-service-url/healthz"
```

### Logs

```bash
# View deployment service logs
gcloud logs tail --project=$PROJECT_ID \
  --resource-name=universal-deployment-service

# View specific deployment logs
gcloud logs read --project=$PROJECT_ID \
  --filter='resource.type="cloud_run_revision" AND resource.labels.service_name="universal-deployment-service"'
```

### Metrics

- Deployment success rate
- Deployment duration
- Active deployments count
- Error rates by type

## Development

### Project Structure

```
universal-deployment-service/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── Dockerfile             # Container definition
├── deploy-service.sh      # Deployment script
├── test-local.py          # Local testing
├── firebase-credentials.json
├── .env
└── README.md
```

### Local Testing

1. Start the service locally:
   ```bash
   python main.py
   ```

2. Run tests:
   ```bash
   python test-local.py
   ```

3. Test API endpoints:
   ```bash
   curl http://localhost:8080/healthz
   ```

### Deployment

The deployment script handles:
- Building the container image
- Deploying to Cloud Run
- Setting environment variables
- Configuring service parameters

## Production Considerations

- **Resource Limits**: Service configured for 4Gi memory, 2 CPU
- **Concurrency**: Max 10 concurrent requests
- **Timeout**: 3600 seconds for long deployments
- **Auto-scaling**: 0-5 instances based on load
- **Authentication**: Currently allows unauthenticated access

## Troubleshooting

### Common Issues

1. **Import errors for universal-agent**:
   - Ensure universal-agent directory is copied correctly
   - Check Python path configuration

2. **Firebase permission errors**:
   - Verify firebase-credentials.json is present
   - Check IAM permissions for the service account

3. **Cloud Run deployment failures**:
   - Check gcloud authentication
   - Verify PROJECT_ID and region settings
   - Review Cloud Run quotas and limits

4. **Environment variable errors**:
   - Ensure .env file has required variables
   - Check variable names and values

### Debug Mode

Enable debug logging by setting:
```bash
export LOG_LEVEL=DEBUG
```

## License

MIT License - see parent directory LICENSE file for details.