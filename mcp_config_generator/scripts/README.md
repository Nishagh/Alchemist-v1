# Utility Scripts

This directory contains utility scripts for managing the OpenAPI to MCP Config Converter deployment.

## Scripts Overview

### 🛠️ `setup-dev.sh`
Sets up the local development environment.

**Usage:**
```bash
./scripts/setup-dev.sh
```

**What it does:**
- Downloads Go dependencies
- Runs tests to verify everything works
- Builds the application locally
- Provides instructions for local development

### 📊 `monitor.sh`
Provides monitoring and management utilities for the deployed service.

**Usage:**
```bash
./scripts/monitor.sh [COMMAND]
```

**Commands:**
- `status` - Show service status and details
- `logs [LINES]` - Show service logs (default: 50 lines)
- `metrics` - Show service metrics and configuration
- `test` - Test all service endpoints
- `update` - Update service configuration
- `traffic` - Show traffic allocation
- `url` - Get service URL

**Examples:**
```bash
./scripts/monitor.sh status                    # Show service status
./scripts/monitor.sh logs 100                  # Show last 100 log entries
./scripts/monitor.sh test                      # Test all endpoints
```

### 🧹 `cleanup.sh`
Removes deployed resources and cleans up the project.

**Usage:**
```bash
./scripts/cleanup.sh [OPTIONS]
```

**Options:**
- `--force, -f` - Skip confirmation prompt
- `--service-only` - Only delete the Cloud Run service
- `--images-only` - Only delete container images
- `--local-only` - Only clean up local artifacts
- `--dry-run` - Show what would be deleted without actually deleting

**Examples:**
```bash
./scripts/cleanup.sh                          # Interactive cleanup with confirmation
./scripts/cleanup.sh --force                  # Cleanup without confirmation
./scripts/cleanup.sh --service-only           # Only delete the Cloud Run service
./scripts/cleanup.sh --dry-run                # Show what would be deleted
```

## Prerequisites

Before running these scripts, ensure you have:

1. **Google Cloud SDK** installed and configured
2. **Docker** installed (for local builds)
3. **Go** installed (for local development)
4. **Proper authentication** with Google Cloud

## Quick Start

1. **Setup development environment:**
   ```bash
   ./scripts/setup-dev.sh
   ```

2. **Deploy the service** (use the main deployment script):
   ```bash
   ./deploy.sh
   ```

3. **Monitor the service:**
   ```bash
   ./scripts/monitor.sh status
   ./scripts/monitor.sh test
   ```

4. **View logs:**
   ```bash
   ./scripts/monitor.sh logs 50
   ```

5. **Clean up when done:**
   ```bash
   ./scripts/cleanup.sh
   ```

## Integration with Main Scripts

These utility scripts are designed to work with:
- `../deploy.sh` - Main deployment script
- `../manage.sh` - Interactive management console

Use the management console for a user-friendly interface:
```bash
./manage.sh
```

## Error Handling

All scripts include:
- ✅ Prerequisites checking
- ✅ Error handling and validation
- ✅ Colored output for better readability
- ✅ Detailed logging and status messages
- ✅ Safe cleanup with confirmations

## Configuration

Scripts use these default values:
- **Service Name:** `openapi-mcp-converter`
- **Region:** `us-central1`
- **Memory:** `512Mi`
- **CPU:** `1`
- **Max Instances:** `10`

These can be modified in the individual scripts if needed.

## Troubleshooting

### Common Issues

1. **Permission denied**: Make sure scripts are executable
   ```bash
   chmod +x scripts/*.sh
   ```

2. **gcloud not authenticated**: 
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

3. **Missing APIs**: Scripts will automatically enable required APIs

4. **Service not found**: Check if the service is deployed
   ```bash
   ./scripts/monitor.sh status
   ```

### Getting Help

Each script supports the `--help` or `-h` flag:
```bash
./scripts/monitor.sh --help
./scripts/cleanup.sh --help
```

For the main deployment script:
```bash
./deploy.sh --help
``` 