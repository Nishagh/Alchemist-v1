# OpenAPI to MCP Config Converter - Cloud Run Service

A Google Cloud Run service that converts OpenAPI YAML/JSON specifications to Model Context Protocol (MCP) server configurations. This service provides both a beautiful web interface and REST API endpoints for easy conversion.

## Features

- 🌐 **Modern Web Interface**: Beautiful, responsive UI for uploading and converting OpenAPI files
- 🔄 **Multiple Input Methods**: Support for file upload or direct text paste
- 📁 **Format Support**: Handles both JSON and YAML OpenAPI specifications
- ⚙️ **Flexible Configuration**: Customizable server names, tool prefixes, and output formats
- ✅ **Validation**: Optional OpenAPI specification validation
- 📱 **Mobile Friendly**: Responsive design that works on all devices
- 🚀 **Cloud Native**: Designed for Google Cloud Run with automatic scaling

## API Endpoints

### Web Interface
- `GET /` - Main conversion interface

### REST API
- `POST /api/convert` - Convert OpenAPI spec to MCP config (JSON API)
- `POST /convert` - Convert and download file directly
- `GET /health` - Health check endpoint

## API Usage

### Convert via REST API

```bash
curl -X POST "https://your-service-url/api/convert" \
  -H "Content-Type: application/json" \
  -d '{
    "openapi_spec": "your-openapi-spec-here",
    "server_name": "my-api-server",
    "tool_prefix": "api_",
    "format": "yaml",
    "validate": true
  }'
```

**Request Body:**
```json
{
  "openapi_spec": "string (required) - OpenAPI specification content",
  "server_name": "string (optional) - Name for the MCP server (default: openapi-server)",
  "tool_prefix": "string (optional) - Prefix for tool names",
  "format": "string (optional) - Output format: yaml or json (default: yaml)",
  "validate": "boolean (optional) - Validate OpenAPI spec (default: false)",
  "template_config": "string (optional) - Template YAML for customization"
}
```

**Response:**
```json
{
  "success": true,
  "mcp_config": "generated MCP configuration",
  "format": "yaml",
  "server_name": "my-api-server"
}
```

## Deployment to Google Cloud Run

### 🚀 Quick Start (Recommended)

The easiest way to deploy is using the automated deployment scripts:

1. **Setup and deploy in one command:**
   ```bash
   ./manage.sh
   ```
   This launches an interactive management console with all deployment options.

2. **Or use the deployment script directly:**
   ```bash
   ./deploy.sh
   ```

### 📋 Prerequisites

1. Google Cloud Project with billing enabled
2. Google Cloud SDK (`gcloud`) installed and configured
3. Docker installed (for local builds)
4. Go installed (for local development)

The deployment scripts will automatically:
- ✅ Check prerequisites
- ✅ Enable required APIs
- ✅ Run tests
- ✅ Build and deploy the service
- ✅ Provide service URL and health check

### 🛠️ Deployment Scripts

#### Main Deployment Script (`deploy.sh`)
```bash
# Deploy using Cloud Build (recommended)
./deploy.sh

# Deploy with local Docker build
./deploy.sh --method local

# Deploy using service.yaml configuration
./deploy.sh --method yaml

# Deploy to specific region and project
./deploy.sh --project my-project --region us-west1

# Skip tests and deploy
./deploy.sh --skip-tests
```

#### Interactive Management Console (`manage.sh`)
```bash
./manage.sh
```
Provides a user-friendly menu for:
- 🚀 Deployment operations
- 📊 Monitoring and management
- 🧹 Cleanup operations
- ℹ️ Service information

#### Utility Scripts
- `scripts/setup-dev.sh` - Setup local development environment
- `scripts/monitor.sh` - Monitor and manage deployed service
- `scripts/cleanup.sh` - Clean up deployed resources

See [`scripts/README.md`](scripts/README.md) for detailed documentation.

### 🔧 Manual Deployment (Alternative)

If you prefer manual deployment:

#### Option 1: Deploy with Cloud Build (Recommended)

1. **Clone and setup:**
   ```bash
   git clone <your-repo-url>
   cd openapi-mcp-converter
   gcloud config set project your-google-cloud-project-id
   ```

2. **Deploy using Cloud Build:**
   ```bash
   gcloud builds submit --config cloudbuild.yaml
   ```

#### Option 2: Deploy with Local Build

1. **Build and push the Docker image:**
   ```bash
   export PROJECT_ID="your-google-cloud-project-id"
   docker build -t gcr.io/$PROJECT_ID/openapi-mcp-converter .
   docker push gcr.io/$PROJECT_ID/openapi-mcp-converter
   ```

2. **Deploy to Cloud Run:**
   ```bash
   gcloud run deploy openapi-mcp-converter \
     --image gcr.io/$PROJECT_ID/openapi-mcp-converter \
     --region us-central1 \
     --platform managed \
     --allow-unauthenticated \
     --memory 512Mi \
     --cpu 1 \
     --max-instances 10 \
     --port 8080
   ```

#### Option 3: One-Click Deploy

[![Run on Google Cloud](https://deploy.cloud.run/button.svg)](https://deploy.cloud.run)

### Environment Variables

The service supports the following environment variables:

- `PORT` - Port to run the service on (default: 8080)

### Configuration Options

You can customize the Cloud Run deployment in `cloudbuild.yaml`:

- **Memory**: Adjust `--memory` (256Mi, 512Mi, 1Gi, 2Gi, 4Gi)
- **CPU**: Adjust `--cpu` (1, 2, 4)
- **Region**: Change `--region` to your preferred region
- **Max Instances**: Adjust `--max-instances` for scaling
- **Authentication**: Remove `--allow-unauthenticated` to require authentication

## Local Development

1. **Start the existing OpenAPI to MCP converter:**
   ```bash
   cd openapi-to-mcpserver
   go mod download
   ```

2. **Run the web service:**
   ```bash
   cd ..
   go mod download
   go run main.go
   ```

3. **Access the service:**
   Open http://localhost:8080 in your browser

## Usage Examples

### Example 1: Converting Petstore API

1. Visit the web interface
2. Upload the [Petstore OpenAPI spec](https://petstore.swagger.io/v2/swagger.json)
3. Set server name to "petstore"
4. Choose YAML format
5. Click "Convert to MCP Config"
6. Download the generated configuration

### Example 2: API Usage

```javascript
const response = await fetch('/api/convert', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    openapi_spec: `
      openapi: 3.0.0
      info:
        title: Sample API
        version: 1.0.0
      paths:
        /users:
          get:
            summary: List users
            responses:
              '200':
                description: OK
    `,
    server_name: 'sample-api',
    format: 'yaml'
  })
});

const result = await response.json();
console.log(result.mcp_config);
```

## Cost Estimation

Google Cloud Run pricing (as of 2024):
- **CPU**: $0.00002400 per vCPU-second
- **Memory**: $0.00000250 per GiB-second
- **Requests**: $0.40 per million requests
- **Free tier**: 2 million requests, 400,000 GiB-seconds, 200,000 vCPU-seconds per month

For typical usage (converting a few OpenAPI specs per day), the service will likely fall within the free tier.

## Security Considerations

- The service runs with `--allow-unauthenticated` by default for easy access
- Consider enabling authentication for production use:
  ```bash
  gcloud run services remove-iam-policy-binding openapi-mcp-converter \
    --region=us-central1 \
    --member="allUsers" \
    --role="roles/run.invoker"
  ```
- Input validation is performed on OpenAPI specifications
- Temporary files are cleaned up automatically
- No persistent storage of uploaded files

## Monitoring and Management

### 📊 Using the Monitoring Script

The easiest way to monitor your deployed service:

```bash
# Check service status
./scripts/monitor.sh status

# View recent logs
./scripts/monitor.sh logs 50

# Test all endpoints
./scripts/monitor.sh test

# View service metrics
./scripts/monitor.sh metrics

# Update service configuration
./scripts/monitor.sh update

# Get service URL
./scripts/monitor.sh url
```

### 🔧 Manual Monitoring

View logs:
```bash
gcloud logs read "resource.type=cloud_run_revision AND resource.labels.service_name=openapi-mcp-converter" --limit 50
```

Monitor performance:
```bash
gcloud run services describe openapi-mcp-converter --region=us-central1
```

### 🧹 Cleanup

When you're done with the service:

```bash
# Interactive cleanup (recommended)
./scripts/cleanup.sh

# Quick cleanup without confirmation
./scripts/cleanup.sh --force

# Only remove the service (keep images)
./scripts/cleanup.sh --service-only

# See what would be deleted (dry run)
./scripts/cleanup.sh --dry-run
```

## Troubleshooting

### Common Issues

1. **Build Fails**: Ensure Docker is running and you have proper permissions
2. **Deployment Fails**: Check that required APIs are enabled
3. **Service Unreachable**: Verify the service is deployed and accessible:
   ```bash
   gcloud run services list --region=us-central1
   ```

### Debug Mode

To enable verbose logging, redeploy with debug environment variable:
```bash
gcloud run deploy openapi-mcp-converter \
  --image gcr.io/$PROJECT_ID/openapi-mcp-converter \
  --set-env-vars="DEBUG=true" \
  --region=us-central1
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally
5. Submit a pull request

## License

This project is licensed under the same license as the underlying OpenAPI to MCP Server converter.

## Support

For issues and questions:
- Check the [existing issues](../../issues)
- Create a new issue with detailed information
- Include sample OpenAPI specifications that cause problems

## 🗂️ Project Structure

```
openapi-mcp-converter/
├── main.go                 # Main web service
├── main_test.go           # Test suite
├── go.mod                 # Go dependencies
├── Dockerfile             # Container configuration
├── cloudbuild.yaml        # Cloud Build configuration
├── service.yaml           # Cloud Run service definition
├── deploy.sh              # 🚀 Main deployment script
├── manage.sh              # 📊 Interactive management console
├── scripts/               # Utility scripts
│   ├── setup-dev.sh      # Local development setup
│   ├── monitor.sh        # Service monitoring
│   ├── cleanup.sh        # Resource cleanup
│   └── README.md         # Scripts documentation
├── openapi-to-mcpserver/  # Conversion logic
└── README.md             # This file
```

## 🎯 Summary

This project provides a complete, production-ready solution for converting OpenAPI specifications to MCP configurations:

✅ **Easy Deployment** - Automated scripts handle everything  
✅ **Beautiful Web UI** - Modern, responsive interface  
✅ **REST API** - Programmatic access for integration  
✅ **Comprehensive Monitoring** - Built-in monitoring and management tools  
✅ **Cost Effective** - Optimized for Google Cloud's free tier  
✅ **Production Ready** - Includes testing, cleanup, and best practices  

### Quick Commands Reference

```bash
# 🚀 Deploy everything
./manage.sh                 # Interactive menu
./deploy.sh                 # Direct deployment

# 📊 Monitor service
./scripts/monitor.sh status # Check status
./scripts/monitor.sh test   # Test endpoints

# 🧹 Clean up
./scripts/cleanup.sh        # Remove all resources
```

---

**Built with ❤️ for the MCP community** 