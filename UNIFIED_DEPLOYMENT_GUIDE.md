# Alchemist Unified Deployment Guide

## 🧙‍♂️ Welcome to the Unified Deployment System

The Alchemist Unified Deployment System provides a comprehensive, automated, and intelligent deployment solution for all Alchemist services. This guide will walk you through everything you need to know to deploy and manage your Alchemist platform.

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [System Overview](#system-overview)
3. [Prerequisites](#prerequisites)
4. [Configuration](#configuration)
5. [Deployment Modes](#deployment-modes)
6. [Service Management](#service-management)
7. [Monitoring & Debugging](#monitoring--debugging)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Advanced Usage](#advanced-usage)

## 🚀 Quick Start

### One-Command Full Deployment

```bash
# Deploy everything to production
./deploy-unified.sh all

# Deploy to a specific project
./deploy-unified.sh -p your-project-id all

# Deploy core services only
./deploy-unified.sh core

# Deploy with debug logging
./deploy-unified.sh -d all
```

### Check Deployment Status

```bash
# Real-time dashboard
./scripts/deployment-dashboard.sh --watch

# Quick status check
./scripts/deployment-dashboard.sh

# JSON output for automation
./scripts/deployment-dashboard.sh --format json
```

### Deploy Individual Services

```bash
# Deploy a specific service
./scripts/deploy-service-enhanced.sh agent-engine

# Deploy with automatic rollback on failure
./scripts/deploy-service-enhanced.sh --rollback-on-fail knowledge-vault

# Dry run to see what would be deployed
./scripts/deploy-service-enhanced.sh --dry-run agent-studio
```

## 🏗️ System Overview

### Architecture

The unified deployment system consists of several components:

```
├── deploy-unified.sh              # Main deployment orchestrator
├── deployment-config.yaml         # Configuration management
├── scripts/
│   ├── validate-deployment.sh     # Pre/post deployment validation
│   ├── deploy-service-enhanced.sh # Individual service deployment
│   └── deployment-dashboard.sh    # Real-time monitoring
└── UNIFIED_DEPLOYMENT_GUIDE.md   # This guide
```

### Service Tiers

Services are deployed in a specific order based on their tier:

**Tier 1 (Core Infrastructure):**
- `knowledge-vault` - Document processing and vector storage
- `agent-engine` - Main API orchestrator and business logic

**Tier 2 (Integration Services):**
- `agent-bridge` - WhatsApp and messaging integrations
- `tool-forge` - MCP server management and API tooling
- `mcp-config-generator` - OpenAPI to MCP conversion service

**Tier 3 (Application Services):**
- `agent-launcher` - Dynamic agent deployment service
- `prompt-engine` - Prompt management and optimization
- `sandbox-console` - Testing and development environment

**Tier 4 (External Services):**
- `banking-api-service` - Demo banking API service
- `agent-studio` - Frontend web application
- `admin-dashboard` - Administrative monitoring interface

## 📋 Prerequisites

### Required Tools

1. **Google Cloud SDK**
   ```bash
   # Install gcloud CLI
   curl https://sdk.cloud.google.com | bash
   exec -l $SHELL
   
   # Authenticate
   gcloud auth login
   gcloud auth application-default login
   ```

2. **Project Setup**
   ```bash
   # Set your project
   gcloud config set project YOUR_PROJECT_ID
   
   # Enable required APIs (done automatically)
   gcloud services enable run.googleapis.com cloudbuild.googleapis.com
   ```

3. **API Keys and Secrets**
   ```bash
   # Store OpenAI API key
   echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-
   
   # Verify secret
   gcloud secrets versions access latest --secret="openai-api-key"
   ```

### Optional Tools

- **Docker** (for local development and testing)
- **curl** (for health checks and API testing)
- **jq** (for JSON processing in scripts)

## ⚙️ Configuration

### Environment Variables

Set these environment variables to customize deployment:

```bash
# Project configuration
export ALCHEMIST_PROJECT_ID="your-project-id"
export ALCHEMIST_REGION="us-central1"
export ALCHEMIST_ENV="production"

# API keys (store in Secret Manager instead)
export OPENAI_API_KEY="your-openai-api-key"

# Deployment options
export DEBUG="true"                    # Enable debug logging
export SKIP_CONFIRMATIONS="true"      # Skip interactive prompts
```

### Configuration File

Edit `deployment-config.yaml` to customize service settings:

```yaml
# Environment-specific settings
environments:
  production:
    project_id: "your-project-id"
    region: "us-central1"
    min_instances: 1
    max_instances: 10

# Service-specific configurations
services:
  agent-engine:
    memory: "2Gi"
    cpu: "2"
    max_instances: 15
    environment_variables:
      - "CUSTOM_SETTING=value"
```

## 🎯 Deployment Modes

### 1. Full Deployment

Deploy all services in the correct order:

```bash
./deploy-unified.sh all
```

**What it does:**
- Validates prerequisites
- Sets up environment and secrets
- Deploys all services in tier order
- Configures inter-service communication
- Runs health checks
- Provides deployment summary

### 2. Core Services Only

Deploy just the essential services:

```bash
./deploy-unified.sh core
```

**Includes:**
- knowledge-vault
- agent-engine

### 3. Specific Services

Deploy only selected services:

```bash
./deploy-unified.sh services agent-engine knowledge-vault agent-studio
```

### 4. Frontend Only

Deploy just the frontend services:

```bash
./deploy-unified.sh frontend
```

**Includes:**
- agent-studio
- admin-dashboard

### 5. Validation Mode

Check configuration without deploying:

```bash
./deploy-unified.sh validate
```

### 6. Status Check

View current deployment status:

```bash
./deploy-unified.sh status
```

### 7. Rollback

Rollback a specific service:

```bash
./deploy-unified.sh rollback agent-engine
```

## 🔧 Service Management

### Deploy Individual Services

Use the enhanced service deployment script for fine-grained control:

```bash
# Basic deployment
./scripts/deploy-service-enhanced.sh agent-engine

# Advanced options
./scripts/deploy-service-enhanced.sh \
  --project-id my-project \
  --environment staging \
  --force \
  --rollback-on-fail \
  --debug \
  knowledge-vault
```

### Available Options

- `--force` - Force rebuild even if no changes detected
- `--skip-health` - Skip health checks after deployment
- `--dry-run` - Show what would be deployed without executing
- `--rollback-on-fail` - Automatically rollback on failure
- `--debug` - Enable detailed logging

### Service Health Checks

The system automatically performs health checks:

1. **Endpoint Health**: Checks `/health` endpoint
2. **Root Response**: Falls back to root endpoint if no health endpoint
3. **Retry Logic**: Multiple attempts with exponential backoff
4. **Timeout Handling**: Configurable timeouts per service

## 📊 Monitoring & Debugging

### Real-time Dashboard

Launch the interactive dashboard:

```bash
# Watch mode with auto-refresh
./scripts/deployment-dashboard.sh --watch

# Include logs and metrics
./scripts/deployment-dashboard.sh --watch --logs --metrics

# Custom refresh interval
./scripts/deployment-dashboard.sh --watch --interval 10
```

**Dashboard Features:**
- Real-time service status
- Health check results
- Service URLs and revisions
- Resource usage metrics
- Recent log entries
- Interactive keyboard shortcuts

### Validation Tools

Comprehensive deployment validation:

```bash
# Full validation
./scripts/validate-deployment.sh

# Configuration only
./scripts/validate-deployment.sh --config-only

# Services only
./scripts/validate-deployment.sh --services-only

# Health checks only
./scripts/validate-deployment.sh --health-only
```

### Logging

All deployment activities are logged:

```bash
# Main deployment log
tail -f deployment.log

# Service-specific deployment log
tail -f service-deployment.log

# Validation log
tail -f validation.log
```

### Debugging

Enable debug mode for detailed output:

```bash
# Environment variable
export DEBUG=true

# Command line option
./deploy-unified.sh -d all

# Service deployment
./scripts/deploy-service-enhanced.sh --debug agent-engine
```

## 🔍 Troubleshooting

### Common Issues

#### 1. Authentication Errors

```bash
# Re-authenticate
gcloud auth login
gcloud auth application-default login

# Check current authentication
gcloud auth list
```

#### 2. API Not Enabled

```bash
# Enable required APIs
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

# Check enabled APIs
gcloud services list --enabled
```

#### 3. Secret Manager Issues

```bash
# Check secret exists
gcloud secrets describe openai-api-key

# Recreate secret
gcloud secrets delete openai-api-key
echo -n "your-api-key" | gcloud secrets create openai-api-key --data-file=-
```

#### 4. Build Failures

```bash
# Check build logs
gcloud builds list --limit=5

# View specific build
gcloud builds log BUILD_ID
```

#### 5. Service Not Responding

```bash
# Check service logs
gcloud run services logs read SERVICE_NAME --region=us-central1

# Check service configuration
gcloud run services describe SERVICE_NAME --region=us-central1
```

### Debug Commands

```bash
# Validate everything before deployment
./scripts/validate-deployment.sh

# Check specific service health
curl -v https://your-service-url/health

# View Cloud Run services
gcloud run services list --region=us-central1

# Check recent deployments
gcloud run revisions list --service=SERVICE_NAME --region=us-central1
```

## 📚 Best Practices

### 1. Pre-deployment Validation

Always validate before deploying:

```bash
./scripts/validate-deployment.sh
```

### 2. Incremental Deployment

Deploy core services first, then expand:

```bash
# Start with core
./deploy-unified.sh core

# Add integration services
./deploy-unified.sh services agent-bridge tool-forge

# Finally, frontend
./deploy-unified.sh frontend
```

### 3. Environment Management

Use different projects for different environments:

```bash
# Staging
./deploy-unified.sh -p alchemist-staging -e staging all

# Production
./deploy-unified.sh -p alchemist-prod -e production all
```

### 4. Monitoring

Set up continuous monitoring:

```bash
# Background dashboard
./scripts/deployment-dashboard.sh --watch > dashboard.log &

# Regular health checks
while true; do
  ./scripts/validate-deployment.sh --health-only
  sleep 300
done
```

### 5. Backup and Recovery

Before major deployments:

```bash
# Tag current state
git tag "pre-deployment-$(date +%Y%m%d-%H%M%S)"

# Enable automatic rollback
./scripts/deploy-service-enhanced.sh --rollback-on-fail agent-engine
```

## 🔬 Advanced Usage

### Custom Service Configurations

Modify `deployment-config.yaml` for specific needs:

```yaml
services:
  agent-engine:
    memory: "4Gi"
    cpu: "4"
    max_instances: 20
    environment_variables:
      - "CUSTOM_MODEL=gpt-4-turbo"
      - "MAX_TOKENS=32000"
    secrets:
      - "custom-api-key"
```

### CI/CD Integration

Use in GitHub Actions:

```yaml
- name: Deploy Alchemist
  run: |
    ./deploy-unified.sh -y all
  env:
    ALCHEMIST_PROJECT_ID: ${{ secrets.PROJECT_ID }}
    OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
```

### Multi-region Deployment

Deploy to multiple regions:

```bash
# Primary region
./deploy-unified.sh -r us-central1 all

# Secondary region
./deploy-unified.sh -r europe-west1 all
```

### Custom Build Configurations

Override Docker build settings:

```bash
# Custom timeout
./deploy-unified.sh -t 7200s all

# Force rebuild all services
for service in agent-engine knowledge-vault agent-bridge; do
  ./scripts/deploy-service-enhanced.sh --force $service
done
```

### Health Check Customization

Customize health check endpoints in `deployment-config.yaml`:

```yaml
services:
  agent-engine:
    health_path: "/api/health"
    health_timeout: 60
    health_retries: 5
```

## 🆘 Getting Help

### Documentation

- **This Guide**: Complete deployment documentation
- **DEPLOYMENT_GUIDE.md**: Original deployment guide
- **deployment-config.yaml**: Configuration reference
- **Service READMEs**: Individual service documentation

### Command Help

```bash
# Main deployment script help
./deploy-unified.sh --help

# Service deployment help
./scripts/deploy-service-enhanced.sh --help

# Dashboard help
./scripts/deployment-dashboard.sh --help

# Validation help
./scripts/validate-deployment.sh --help
```

### Support Commands

```bash
# Generate support information
./scripts/validate-deployment.sh > support-info.txt
./scripts/deployment-dashboard.sh --format json >> support-info.txt

# Export configuration
cp deployment-config.yaml config-backup-$(date +%Y%m%d).yaml
```

## 🎉 Success!

Once deployment is complete, you should see:

```
🎉 All services deployed successfully!

🧪 Test your deployment:
  curl https://your-agent-engine-url/health
  open https://your-agent-studio-url

📊 Monitor your services:
  ./scripts/deployment-dashboard.sh --watch
```

Your Alchemist platform is now running and ready to transform conversations into intelligent interactions! 🧙‍♂️✨

---

**Happy Deploying!** 🚀

For issues or improvements, please check the logs and validation output, or refer to the troubleshooting section above.