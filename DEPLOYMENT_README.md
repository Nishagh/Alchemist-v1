# Alchemist Services Deployment Guide

This directory contains deployment scripts for all Alchemist services that use the centralized `alchemist_shared` module.

## Prerequisites

1. **Google Cloud CLI** - Install from https://cloud.google.com/sdk/docs/install
2. **Docker** - Required for building container images
3. **Google Cloud Project** - Set to `alchemist-e69bb`
4. **Authentication** - Must be authenticated with `gcloud auth login`

## Available Services

The following services use the centralized `alchemist_shared` module and have deployment scripts:

| Service | Script | Description |
|---------|--------|-------------|
| `agent-engine` | `deploy-agent-engine.sh` | Core agent orchestration service |
| `billing-service` | `deploy-billing-service.sh` | Payment and credits management |
| `prompt-engine` | `deploy-prompt-engine.sh` | Prompt processing and optimization |
| `sandbox-console` | `deploy-sandbox-console.sh` | Testing and development console |
| `agent-tuning-service` | `deploy-agent-tuning-service.sh` | Fine-tuning and training service |
| `knowledge-vault` | `deploy-knowledge-vault.sh` | Document storage and retrieval |

## Usage

### Master Deployment Script

Use the master script `deploy-all-alchemist-services.sh` for convenient deployment management:

```bash
# Deploy all services
./deploy-all-alchemist-services.sh all

# Deploy specific service
./deploy-all-alchemist-services.sh agent-engine

# List available services
./deploy-all-alchemist-services.sh --list

# Show help
./deploy-all-alchemist-services.sh --help
```

### Individual Service Deployment

You can also run individual deployment scripts directly:

```bash
# Deploy agent engine
./deploy-agent-engine.sh

# Deploy billing service
./deploy-billing-service.sh

# Deploy knowledge vault
./deploy-knowledge-vault.sh
```

## Deployment Architecture

### Directory Structure
All deployment scripts must be run from the **root Alchemist-v1 directory** to ensure proper access to both the service directories and the centralized `shared/` module.

```
Alchemist-v1/
├── agent-engine/           # Service code
├── billing-service/        # Service code
├── shared/                 # Centralized alchemist_shared module
├── deploy-agent-engine.sh  # Deployment script
├── deploy-billing-service.sh
└── deploy-all-alchemist-services.sh
```

### Docker Build Process

Each deployment script follows this pattern:

1. **Validation** - Verify we're in the correct directory
2. **Authentication** - Check gcloud and Docker credentials
3. **Dockerfile Generation** - Create temporary service-specific Dockerfile
4. **Docker Context** - Build from root directory to include both service and shared module
5. **Container Build** - Build with proper shared module installation
6. **Cloud Deployment** - Deploy to Google Cloud Run
7. **Cleanup** - Remove temporary files and restore original state

### Key Features

- **Centralized Shared Module**: All services use the same `shared/alchemist_shared` module
- **Temporary Docker Files**: Scripts create and cleanup temporary build files
- **Backup & Restore**: Original `.dockerignore` files are preserved
- **Health Checks**: Automatic deployment verification
- **Error Handling**: Proper error reporting and logging guidance

## Docker Build Pattern

Each service follows this Dockerfile pattern:

```dockerfile
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y curl gcc

# Copy service requirements
COPY {service}/requirements.txt .
RUN pip install -r requirements.txt gunicorn

# Install centralized shared module
COPY shared /app/shared
RUN cd /app/shared && pip install -e .

# Copy service code
COPY {service} .

# Run application
CMD gunicorn --bind :$PORT main:app
```

## Environment Variables

Each service deployment sets these environment variables:

- `{SERVICE}_ENVIRONMENT=production`
- `FIREBASE_PROJECT_ID=alchemist-e69bb`
- `PORT=8080`

Additional service-specific environment variables can be set by creating `.env` files in the root directory or service subdirectories.

## Cloud Run Configuration

All services are deployed with these specifications:

- **Platform**: Google Cloud Run (managed)
- **Region**: us-central1
- **Memory**: 2Gi (4Gi for knowledge-vault)
- **CPU**: 2 cores
- **Timeout**: 3600 seconds
- **Concurrency**: 80 requests
- **Max Instances**: 5 (limited by Google Cloud quota)
- **Authentication**: Unauthenticated (public)

## Troubleshooting

### Common Issues

1. **Directory Error**: Must run scripts from `Alchemist-v1` root directory
2. **Missing Tools**: Install gcloud CLI and Docker
3. **Authentication**: Run `gcloud auth login`
4. **Build Context**: Scripts automatically handle Docker context and shared module inclusion
5. **Quota Limits**: Default Google Cloud quota allows 5 max instances per region
   - If deploying all 6 services, consider using different regions or requesting quota increase
   - Alternative: Deploy only critical services initially

### Viewing Logs

```bash
# View service logs
gcloud logs read --project=alchemist-e69bb --filter="resource.labels.service_name={SERVICE_NAME}"

# Tail live logs
gcloud logs tail --project=alchemist-e69bb --filter="resource.labels.service_name={SERVICE_NAME}"
```

### Health Checks

Each deployed service provides health check endpoints:

- `https://{service-url}/health` - Basic health check
- `https://{service-url}/docs` - API documentation (if available)

## Shared Module Integration

All services automatically get the `alchemist_shared` module installed with these components:

- **Database**: Firebase client and utilities
- **Models**: Pydantic models for API responses
- **Middleware**: API logging and metrics
- **Services**: Common business logic
- **Config**: Shared configuration management

The module is installed as an editable package (`pip install -e .`) ensuring services can import:

```python
from alchemist_shared.database.firebase_client import FirebaseClient
from alchemist_shared.models.agent_models import AgentResponse
from alchemist_shared.middleware.api_logging_middleware import setup_api_logging_middleware
```

## Security Notes

- Deployment scripts handle credential files safely
- Temporary build files are cleaned up automatically
- Original configuration files are preserved and restored
- No secrets are included in container images