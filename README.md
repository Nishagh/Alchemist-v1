# Alchemist AI Platform

A comprehensive multi-agent AI platform for creating, deploying, and managing custom AI agents with advanced capabilities.

## 🏗️ Architecture

Alchemist follows a **microservices monorepo architecture** that enables:
- **Shared code management** across all services
- **Independent deployments** to Google Cloud Run
- **Coordinated development** with unified tooling
- **Scalable infrastructure** with proper service boundaries

## 📦 Services

### Core Services
- **Agent Engine** (`agent-engine/`) - Main API orchestration service
- **Knowledge Vault** (`knowledge-vault/`) - Document processing and semantic search
- **Agent Bridge** (`agent-bridge/`) - Direct WhatsApp Business API integration
- **Agent Launcher** (`agent-launcher/`) - Automated agent deployment to Cloud Run
- **Agent Studio** (`agent-studio/`) - React web application for creating and managing agents
- **Sandbox Console** (`sandbox-console/`) - Testing environment for agents before deployment
- **Tool Forge** (`tool-forge/`) - MCP configuration generator for agent capabilities

### Additional Services
- **Prompt Engine** (`prompt-engine/`) - AI prompt optimization service
- **Banking API Service** (`banking-api-service/`) - Example API integration service

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Node.js 18+
- Docker & Docker Compose
- Google Cloud SDK (for deployment)

### Local Development

```bash
# Install all dependencies
make install

# Start development environment
make dev-start

# View logs
make dev-logs

# Stop development environment
make dev-stop
```

### Individual Service Development

```bash
# Backend
make backend-dev

# Knowledge Base
make knowledge-base-dev

# WhatsApp Service
make whatsapp-dev

# Frontend
make frontend-dev
```

## 🔧 Development Workflow

### Available Commands

```bash
# Development
make help           # Show all available commands
make install        # Install all dependencies
make test          # Run all tests
make lint          # Run code linting
make format        # Format all code
make clean         # Clean build artifacts

# Deployment
make deploy-all              # Deploy all services
make deploy-backend          # Deploy backend service
make deploy-knowledge-base   # Deploy knowledge base service
make deploy-whatsapp        # Deploy WhatsApp service
make deploy-frontend        # Deploy frontend service

# Utilities
make check-changes  # Check which services have changes
make docker-build   # Build all Docker images
```

### Testing

```bash
# Run all tests
make test

# Test individual services
cd packages/backend && python -m pytest
cd packages/frontend && npm test
```

### Code Quality

```bash
# Format code
make format

# Lint code
make lint

# Type checking (where applicable)
mypy packages/backend packages/knowledge-base
```

## 📁 Project Structure

```
alchemist/
├── packages/
│   ├── shared/                    # Shared libraries and utilities
│   │   ├── alchemist_shared/
│   │   │   ├── auth/             # Authentication utilities
│   │   │   ├── config/           # Configuration management
│   │   │   ├── database/         # Database clients (Firebase)
│   │   │   ├── exceptions/       # Exception handling
│   │   │   ├── logging/          # Structured logging
│   │   │   ├── models/           # Shared data models
│   │   │   └── utils/            # Common utilities
│   │   └── setup.py
│   ├── backend/                   # Main API service
│   ├── knowledge-base/            # Document processing service
│   ├── whatsapp/                 # WhatsApp integration service
│   ├── frontend/                 # React web application
│   └── agent-deployment/         # Agent deployment service
├── deployment/
│   ├── scripts/                  # Deployment automation
│   ├── docker-compose/           # Local development setup
│   └── terraform/                # Infrastructure as code
├── .github/workflows/            # CI/CD pipelines
├── docs/                        # Documentation
├── tools/                       # Development tools
├── Makefile                     # Development commands
└── README.md
```

## 🌐 Deployment

### Cloud Run Deployment

Each service is deployed independently to Google Cloud Run:

```bash
# Deploy individual service
./deployment/scripts/deploy-service.sh backend

# Deploy all services
./deployment/scripts/deploy-all.sh

# Deploy to specific environment
./deployment/scripts/deploy-service.sh backend staging
```

### Environment Configuration

Services are configured through environment variables:

```bash
# Required for all services
ENVIRONMENT=production|staging|development
FIREBASE_PROJECT_ID=your-project-id
GOOGLE_CLOUD_PROJECT=your-project-id

# Service-specific
OPENAI_API_KEY=your-openai-key
CORS_ORIGINS=https://your-domain.com

# Service URLs (auto-configured in production)
KNOWLEDGE_BASE_URL=https://alchemist-knowledge-vault-url
WHATSAPP_SERVICE_URL=https://whatsapp-service-url
```

## 🔒 Security

### Authentication & Authorization
- Firebase Authentication for user management
- JWT tokens for API authentication
- Role-based access control (RBAC)

### API Security
- CORS configuration for cross-origin requests
- Rate limiting on API endpoints
- Input validation and sanitization
- Structured error handling

### Infrastructure Security
- Non-root containers
- Security headers
- Encrypted communications (HTTPS)
- Secret management through Google Cloud

## 📊 Monitoring & Observability

### Logging
- Structured JSON logging
- Correlation IDs for request tracing
- Centralized log aggregation

### Health Checks
- Service health endpoints (`/health`)
- Load balancer health checks
- Dependency health validation

### Metrics
- Request/response metrics
- Error rates and latency
- Resource utilization

## 🧪 Testing Strategy

### Test Types
- **Unit Tests** - Individual component testing
- **Integration Tests** - Service interaction testing
- **End-to-End Tests** - Complete workflow testing
- **Performance Tests** - Load and stress testing

### Test Execution
- Automated testing in CI/CD pipeline
- Pre-deployment quality gates
- Branch protection with required tests

## 📚 Documentation

### Service Documentation
- Each service has its own README in `packages/{service}/`
- API documentation available at `/docs` endpoints
- Architecture documentation in `docs/`

### Development Guides
- [Deployment Guide](docs/deployment/)
- [Development Setup](docs/development/)
- [API Reference](docs/apis/)

## 🤝 Contributing

### Development Process
1. Create feature branch from `develop`
2. Make changes with tests
3. Ensure code quality checks pass
4. Submit pull request to `develop`
5. Deploy to staging for testing
6. Merge to `main` for production deployment

### Code Standards
- Python: Black formatting, flake8 linting
- JavaScript: ESLint + Prettier
- Commit messages: Conventional commits
- Documentation: Keep README files updated

## 📈 Performance

### Optimization Features
- **Build-time optimization** - Services configured at build time
- **Shared dependencies** - Reduced duplication across services
- **Container optimization** - Multi-stage builds and minimal images
- **Auto-scaling** - Cloud Run automatic scaling based on demand

### Benchmarks
- 60-80% faster response times vs. runtime configuration
- Minimal cold start times with optimized containers
- Efficient resource utilization across services

## 🔄 CI/CD Pipeline

### Automated Workflows
- **Change Detection** - Only deploy services with changes
- **Quality Gates** - Tests and linting must pass
- **Environment Promotion** - Staging → Production workflow
- **Rollback Capability** - Automated rollback on failures

### Deployment Stages
1. **Code Quality** - Linting, formatting, security scans
2. **Testing** - Unit, integration, and E2E tests
3. **Build** - Docker image creation and optimization
4. **Deploy** - Selective service deployment
5. **Verify** - Health checks and smoke tests

## 📞 Support

For questions, issues, or contributions:
- **Issues** - Use GitHub Issues for bug reports and feature requests
- **Discussions** - Use GitHub Discussions for questions and ideas
- **Documentation** - Check the `docs/` directory for detailed guides

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Alchemist AI Platform** - Building the future of intelligent agent deployment and management.