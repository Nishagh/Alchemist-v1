# Alchemist Smart Deployment System

This directory contains the intelligent deployment system for the Alchemist AI Platform, featuring automatic change detection, selective deployment, and comprehensive rollback capabilities.

## 🎯 Quick Start

### Basic Usage

```bash
# Auto-deploy changed services (recommended)
make deploy

# Deploy all services
make deploy-all

# Deploy specific group
make deploy-group GROUP=core

# Deploy specific services
make deploy-services SERVICES="agent-engine knowledge-vault"

# Check what would be deployed (dry run)
make deploy-diff

# Check deployment status
make deploy-status

# Rollback a service
make deploy-rollback SERVICE=agent-engine
```

### Direct Script Usage

```bash
# Change to project root first
cd /path/to/alchemist-project

# Auto-deploy changed services
./deployment/scripts/deploy-smart.sh auto

# Deploy all services with parallel execution
./deployment/scripts/deploy-smart.sh all --parallel

# Deploy core services group
./deployment/scripts/deploy-smart.sh group core

# Deploy specific services
./deployment/scripts/deploy-smart.sh services agent-engine knowledge-vault

# Dry run to see what would be deployed
./deployment/scripts/deploy-smart.sh auto --dry-run

# Check deployment status
./deployment/scripts/deploy-smart.sh status

# Validate configuration
./deployment/scripts/deploy-smart.sh validate

# Rollback a service
./deployment/scripts/deploy-smart.sh rollback agent-engine
```

## 📁 Directory Structure

```
deployment/scripts/
├── deploy-smart.sh              # Main smart deployment script
├── lib/                        # Library functions
│   ├── common.sh               # Common utilities and functions
│   ├── change-detector.sh      # Change detection engine
│   ├── state-manager.sh        # Deployment state management
│   ├── service-deps.sh         # Service dependency management
│   └── health-checker.sh       # Health checking and rollback
├── config/                     # Configuration files
│   ├── service-config.yaml     # Service definitions and metadata
│   └── deployment.yaml         # Global deployment configuration
├── legacy/                     # Legacy deployment scripts
│   └── deploy-*.sh             # Old deployment scripts
└── README.md                   # This file
```

## 🧠 Smart Features

### Automatic Change Detection

The system automatically detects changes using two methods:

1. **Git-based Detection**: Compares current commit with last deployment
2. **Fingerprint-based Detection**: Compares file hashes of service directories

```bash
# Use specific detection method
./deployment/scripts/deploy-smart.sh auto --git
./deployment/scripts/deploy-smart.sh auto --fingerprint
```

### Intelligent Dependency Management

Services are deployed in the correct order based on their dependencies:

- **Tier 1**: Core services (agent-engine, knowledge-vault, prompt-engine)
- **Tier 2**: Integration services (agent-bridge, banking-api-service)  
- **Tier 3**: Infrastructure services (billing, monitoring, gnf)
- **Tier 4**: Tool services (tool-forge, sandbox-console, etc.)
- **Tier 5**: Frontend services (agent-studio, admin-dashboard)

### Health Monitoring & Rollback

Each deployment includes:
- Automated health checks
- Service URL verification
- Automatic rollback on critical failures
- Manual rollback capabilities

## ⚙️ Configuration

### Service Configuration (`config/service-config.yaml`)

Defines all services with:
- Dependencies and deployment order
- Resource requirements (CPU, memory, scaling)
- Environment variables
- Health check settings
- Cloud Run configuration

### Global Configuration (`config/deployment.yaml`)

Defines environment-specific settings:
- Project IDs and regions for each environment
- Deployment policies and safety settings
- Notification and integration settings
- Resource limits and security policies

## 🔍 Change Detection

### How It Works

1. **Git Method**: Compares files changed between last deployment commit and current commit
2. **Fingerprint Method**: Calculates MD5 hashes of all relevant files in service directories
3. **Shared Library Detection**: Automatically includes all services that use shared libraries when shared code changes

### What Triggers Deployment

- Source code changes (`.py`, `.js`, `.ts`, `.go`, etc.)
- Configuration changes (`Dockerfile`, `requirements.txt`, `package.json`)
- Shared library changes (affects all dependent services)
- Manual force deployment

### What's Ignored

- Documentation files (`.md`, `README`, etc.)
- Log files and temporary files
- Node modules and Python cache directories
- Git metadata

## 📊 State Management

### Deployment State

The system maintains comprehensive state in `.deployment/state.json`:

```json
{
  "version": "1.0",
  "project_id": "alchemist-e69bb",
  "region": "us-central1", 
  "environment": "production",
  "last_deployment": {
    "commit": "abc123...",
    "timestamp": "2025-01-03 10:30:00",
    "user": "deploy-user"
  },
  "services": {
    "agent-engine": {
      "status": "success",
      "fingerprint": "d41d8cd98f00b204e9800998ecf8427e",
      "url": "https://agent-engine-service-url",
      "last_deployed": "2025-01-03 10:25:00"
    }
  },
  "deployment_history": [...]
}
```

### Backup Management

- Automatic backups before each deployment
- Configurable retention (default: 10 backups)
- Export/import capabilities for disaster recovery

### Deployment History

Complete audit trail of all deployments:
- Service name and status
- Deployment timestamp and commit
- Error messages and rollback actions
- Performance metrics

## 🏥 Health Checking

### Service Health Checks

Each service has configurable health checks:

```yaml
health_check:
  path: "/health"           # Health check endpoint
  timeout: 30              # Request timeout in seconds
  retries: 3               # Number of retry attempts
  expected_status: "200"   # Expected HTTP status code
  expected_content: ""     # Optional content validation
```

### Health Check Types

1. **HTTP/HTTPS**: Checks service endpoints
2. **TCP**: Checks port connectivity
3. **Command**: Runs custom health check commands

### Automatic Rollback

Services are automatically rolled back if:
- Health checks fail after deployment
- Response times exceed thresholds
- Error rates are too high
- Service becomes unresponsive

## 🔄 Rollback System

### Automatic Rollback

```bash
# Enable automatic rollback monitoring (default: 3 minutes)
./deployment/scripts/deploy-smart.sh auto --auto-rollback

# Custom monitoring duration
./deployment/scripts/deploy-smart.sh auto --auto-rollback --monitor-duration 300
```

### Manual Rollback

```bash
# Rollback to previous revision
./deployment/scripts/deploy-smart.sh rollback agent-engine

# Rollback to specific revision
./deployment/scripts/deploy-smart.sh rollback agent-engine --revision revision-name

# Rollback multiple services
./deployment/scripts/deploy-smart.sh rollback agent-engine knowledge-vault
```

### Snapshots

Create and restore service snapshots:

```bash
# Create snapshot before risky deployment
./deployment/scripts/deploy-smart.sh snapshot agent-engine

# List available snapshots
./deployment/scripts/deploy-smart.sh list-snapshots

# Restore from snapshot
./deployment/scripts/deploy-smart.sh restore snapshot-name
```

## 🚀 Advanced Usage

### Environment Variables

```bash
# Override project settings
export ALCHEMIST_PROJECT_ID="my-project"
export ALCHEMIST_REGION="us-west1"
export ALCHEMIST_ENV="staging"

# Skip confirmations (useful for CI/CD)
export SKIP_CONFIRMATIONS="true"

# Enable debug logging
export DEBUG="true"
```

### Parallel Deployment

```bash
# Enable parallel deployment within tiers
./deployment/scripts/deploy-smart.sh all --parallel --max-parallel 3

# Deploy specific group in parallel
./deployment/scripts/deploy-smart.sh group tools --parallel
```

### Force Deployment

```bash
# Force deploy all services (ignore change detection)
./deployment/scripts/deploy-smart.sh all --force

# Force deploy specific services
./deployment/scripts/deploy-smart.sh services agent-engine --force
```

### Custom Timeouts

```bash
# Custom deployment timeout
./deployment/scripts/deploy-smart.sh all --timeout 7200s

# Skip health checks for faster deployment
./deployment/scripts/deploy-smart.sh auto --skip-health-check
```

## 🔧 Troubleshooting

### Common Issues

1. **Prerequisites Not Met**
   ```bash
   # Install required tools
   # - gcloud CLI
   # - jq for JSON processing
   # - yq for YAML processing
   # - curl for health checks
   
   # Check authentication
   gcloud auth list
   ```

2. **Service Configuration Errors**
   ```bash
   # Validate configuration
   ./deployment/scripts/deploy-smart.sh validate
   
   # Check service dependencies
   yq eval '.services' deployment/scripts/config/service-config.yaml
   ```

3. **Deployment Failures**
   ```bash
   # Check deployment logs
   tail -f .deployment/logs/deployment.log
   
   # Check deployment status
   ./deployment/scripts/deploy-smart.sh status
   
   # Manual rollback if needed
   ./deployment/scripts/deploy-smart.sh rollback SERVICE_NAME
   ```

4. **Change Detection Issues**
   ```bash
   # Force fingerprint recalculation
   rm -f .deployment/state.json
   ./deployment/scripts/deploy-smart.sh auto --fingerprint
   
   # Check what would be deployed
   ./deployment/scripts/deploy-smart.sh diff
   ```

### Debug Mode

Enable debug logging for detailed information:

```bash
export DEBUG=true
./deployment/scripts/deploy-smart.sh auto
```

### Log Files

- **Deployment logs**: `.deployment/logs/deployment.log`
- **State file**: `.deployment/state.json`
- **Backups**: `.deployment/backups/`
- **Snapshots**: `.deployment/snapshots/`

## 📚 Integration

### CI/CD Integration

```yaml
# GitHub Actions example
- name: Deploy Changed Services
  run: |
    export SKIP_CONFIRMATIONS=true
    make deploy
    
# GitLab CI example
deploy:
  script:
    - export SKIP_CONFIRMATIONS=true
    - ./deployment/scripts/deploy-smart.sh auto
```

### Monitoring Integration

The system supports integration with:
- Slack notifications
- Email alerts
- Custom webhooks
- Prometheus metrics
- Datadog monitoring

### Custom Scripts

Extend the system with custom scripts:

```bash
# Add custom pre-deployment script
echo "#!/bin/bash" > .deployment/hooks/pre-deploy.sh
echo "echo 'Running custom pre-deployment tasks'" >> .deployment/hooks/pre-deploy.sh
chmod +x .deployment/hooks/pre-deploy.sh

# Add custom post-deployment script
echo "#!/bin/bash" > .deployment/hooks/post-deploy.sh
echo "echo 'Running custom post-deployment tasks'" >> .deployment/hooks/post-deploy.sh
chmod +x .deployment/hooks/post-deploy.sh
```

## 🔒 Security

### Secrets Management

- OpenAI API keys stored in Google Secret Manager
- Service-to-service authentication via Cloud Run IAM
- Environment-specific secret access policies

### Access Control

- Deployment requires appropriate Google Cloud permissions
- Production deployments can require approval (configurable)
- Audit trail of all deployment activities

### Network Security

- Services deployed with appropriate CORS settings
- Environment-specific security policies
- Secrets never logged or exposed

## 📈 Performance

### Optimization Features

- **Selective Deployment**: Only deploy changed services
- **Parallel Execution**: Deploy independent services simultaneously
- **Efficient Change Detection**: Fast git and fingerprint-based detection
- **Smart Caching**: Reuse build artifacts when possible

### Monitoring

- Deployment duration tracking
- Service health metrics
- Success/failure rates
- Rollback frequency analysis

## 🤝 Contributing

### Adding New Services

1. Add service definition to `config/service-config.yaml`
2. Ensure service has proper Dockerfile and health endpoint
3. Update service dependencies if needed
4. Test deployment in development environment

### Modifying Detection Logic

Edit `lib/change-detector.sh` to customize:
- File patterns to include/exclude
- Dependency detection logic
- Service fingerprinting algorithm

### Custom Health Checks

Modify `lib/health-checker.sh` to add:
- New health check types
- Custom validation logic
- Integration with monitoring systems

---

For more information, see the main project documentation in `ALCHEMIST.md`.