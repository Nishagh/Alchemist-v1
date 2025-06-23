# Universal Agent Deployment System

A unified, intelligent agent deployment system that dynamically loads configuration from Firestore and applies LLM-based optimizations for any domain.

## Key Features

- **Universal Agent Template**: Single template works for any agent type/domain
- **Dynamic Configuration Loading**: Loads config from Firestore at runtime
- **LLM-Based Optimizations**: Automatically optimizes tools and prompts based on domain
- **Simplified API**: Deploy with just `agent_id` parameter
- **Environment-Based Config**: Uses `.env` for sensitive settings
- **Single Deployment Flow**: One unified system instead of multiple deployers

## Quick Start

### 1. Environment Setup

The system is already configured with:

**`.env` file:**
```bash
OPENAI_API_KEY=your-openai-api-key
PROJECT_ID=alchemist-e69bb
```

**Firebase credentials:**

*The system supports both uppercase and lowercase variable names and automatically detects Firebase credentials in multiple locations.*

### 2. Deploy an Agent

```bash
# Simple CLI deployment
python deploy.py <agent_id>

# Example
python deploy.py 8e749a5b-91a3-4354-afdf-dc1d157e89fd
```

## Components

### Universal Agent Template (`universal-agent/`)

- **`main.py`**: Universal FastAPI application
- **`config_loader.py`**: Dynamic Firestore configuration loader with LLM optimizations
- **`agent_deployer.py`**: Unified deployment system
- **`mcp_tool.py`**: MCP integration with dynamic optimizations

### Deployment Service (`deployment_service/`)

- **Progress tracking**: Real-time deployment progress
- **Background processing**: Non-blocking deployments
- **Error handling**: Comprehensive error reporting

### CLI Tool (`deploy.py`)

Simple command-line interface for deployments.

### Universal Deployment Service (`universal-deployment-service/`)

REST API service for deployment orchestration:

- **Real-time progress tracking**: Monitor deployment steps and progress
- **Background processing**: Non-blocking deployment execution  
- **Firestore integration**: Updates agent status and deployment history
- **Error handling**: Detailed error reporting and logging

## LLM-Based Optimizations

The system automatically detects agent domains and applies optimizations:

- **Banking**: Enhanced tool descriptions for account operations
- **E-commerce**: Product and order management optimizations
- **Support**: Ticket handling and knowledge base guidance
- **Healthcare**: Patient data and treatment optimizations
- **Education**: Learning and course management enhancements

## API Usage

### Deploy via Universal Deployment Service

```bash
# Deploy an agent
curl -X POST "https://universal-deployment-service.run.app/api/deploy" \
  -H "Content-Type: application/json" \
  -d '{"agent_id": "your-agent-id"}'

# Check deployment status  
curl "https://universal-deployment-service.run.app/api/deployment/{deployment_id}/status"

# List all deployments
curl "https://universal-deployment-service.run.app/api/deployments"
```

### Deploy Universal Deployment Service

```bash
cd universal-deployment-service
./deploy-service.sh
```

The unified system automatically handles configuration loading, optimization application, and deployment to Google Cloud Run.