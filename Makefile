.PHONY: help install test lint format clean dev-start dev-stop deploy-all deploy-core deploy-frontend deploy-unified deploy-service docker-build validate-deployment status dashboard

# Default target
help:
	@echo "🧙‍♂️ Alchemist Monorepo - Available Commands:"
	@echo ""
	@echo "  📦 Development:"
	@echo "    install           - Install all dependencies"
	@echo "    test             - Run all tests"
	@echo "    lint             - Run linting for all packages"
	@echo "    format           - Format code for all packages"
	@echo "    clean            - Clean build artifacts"
	@echo ""
	@echo "  🐳 Local Development:"
	@echo "    dev-start        - Start all services locally"
	@echo "    dev-stop         - Stop all local services"
	@echo "    dev-logs         - Show logs from all services"
	@echo ""
	@echo "  🚀 Unified Deployment (Recommended):"
	@echo "    deploy-unified   - Deploy all services with unified system"
	@echo "    deploy-core      - Deploy core services only (agent-engine, knowledge-vault)"
	@echo "    deploy-frontend  - Deploy frontend services only"
	@echo "    validate-deployment - Validate deployment configuration"
	@echo "    status           - Check deployment status"
	@echo "    dashboard        - Launch deployment dashboard"
	@echo ""
	@echo "  📈 Legacy Deployment:"
	@echo "    deploy-all       - Deploy all services (legacy)"
	@echo "    deploy-agent-engine - Deploy agent engine service"
	@echo "    deploy-knowledge-vault - Deploy knowledge vault service"
	@echo "    deploy-agent-bridge - Deploy agent bridge service"
	@echo "    deploy-agent-studio - Deploy agent studio service"
	@echo ""
	@echo "  🛠️ Utilities:"
	@echo "    docker-build     - Build all Docker images"
	@echo "    check-changes    - Check which services have changes"
	@echo ""
	@echo "  📚 Documentation:"
	@echo "    See UNIFIED_DEPLOYMENT_GUIDE.md for comprehensive deployment guide"
	@echo "    See deployment-config.yaml for configuration options"

# Install dependencies
install:
	@echo "Installing agent-engine dependencies..."
	cd agent-engine && pip install -r requirements.txt
	@echo "Installing knowledge-vault dependencies..."
	cd knowledge-vault && pip install -r requirements.txt
	@echo "Installing agent-bridge dependencies..."
	cd agent-bridge && pip install -r requirements.txt
	@echo "Installing agent-studio dependencies..."
	cd agent-studio && npm install
	@echo "Installing development dependencies..."
	pip install pytest black flake8 mypy

# Run tests
test:
	@echo "Running agent-engine tests..."
	cd agent-engine && python -m pytest tests/ || true
	@echo "Running knowledge-vault tests..."
	cd knowledge-vault && python -m pytest tests/ || true
	@echo "Running agent-bridge tests..."
	cd agent-bridge && python -m pytest tests/ || true
	@echo "Running agent-studio tests..."
	cd agent-studio && npm test -- --watchAll=false || true

# Lint code
lint:
	@echo "Linting Python services..."
	flake8 agent-engine --exclude=venv,__pycache__
	flake8 knowledge-vault --exclude=venv,__pycache__
	flake8 agent-bridge --exclude=venv,__pycache__
	@echo "Linting agent-studio..."
	cd agent-studio && npm run lint || true

# Format code
format:
	@echo "Formatting Python code..."
	black agent-engine --exclude=venv
	black knowledge-vault --exclude=venv
	black agent-bridge --exclude=venv
	@echo "Formatting agent-studio code..."
	cd agent-studio && npm run format || true

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd agent-studio && rm -rf build/ node_modules/.cache/ || true

# Start development environment
dev-start:
	@echo "Starting development environment..."
	docker-compose -f deployment/docker-compose/docker-compose.dev.yml up -d

# Stop development environment
dev-stop:
	@echo "Stopping development environment..."
	docker-compose -f deployment/docker-compose/docker-compose.dev.yml down

# Show development logs
dev-logs:
	docker-compose -f deployment/docker-compose/docker-compose.dev.yml logs -f

# Unified Deployment System (Recommended)
deploy-unified:
	@echo "🚀 Deploying all services with unified system..."
	./deploy-unified.sh all

deploy-core:
	@echo "🔧 Deploying core services..."
	./deploy-unified.sh core

deploy-frontend:
	@echo "🎨 Deploying frontend services..."
	./deploy-unified.sh frontend

validate-deployment:
	@echo "🔍 Validating deployment configuration..."
	./scripts/validate-deployment.sh

status:
	@echo "📊 Checking deployment status..."
	./deploy-unified.sh status

dashboard:
	@echo "📊 Launching deployment dashboard..."
	./scripts/deployment-dashboard.sh --watch

# Legacy Deployment (Maintained for backward compatibility)
deploy-all:
	@echo "Deploying all services (legacy)..."
	./deployment/scripts/deploy-all.sh

# Deploy individual services
deploy-agent-engine:
	./deployment/scripts/deploy-service.sh agent-engine

deploy-knowledge-vault:
	./deployment/scripts/deploy-service.sh knowledge-vault

deploy-agent-bridge:
	./deployment/scripts/deploy-service.sh agent-bridge

deploy-agent-studio:
	./deployment/scripts/deploy-service.sh agent-studio

deploy-agent-launcher:
	./deployment/scripts/deploy-service.sh agent-launcher

# Enhanced individual service deployment
deploy-service:
	@if [ -z "$(SERVICE)" ]; then \
		echo "❌ Error: SERVICE parameter required"; \
		echo "Usage: make deploy-service SERVICE=agent-engine"; \
		echo "Available services: agent-engine, knowledge-vault, agent-bridge, agent-studio, agent-launcher, tool-forge, sandbox-console, prompt-engine, mcp-config-generator, banking-api-service, admin-dashboard"; \
		exit 1; \
	fi
	@echo "🚀 Deploying $(SERVICE) with enhanced deployment..."
	./scripts/deploy-service-enhanced.sh $(SERVICE)

# Build Docker images
docker-build:
	@echo "Building Docker images..."
	docker build -t agent-engine agent-engine/
	docker build -t knowledge-vault knowledge-vault/
	docker build -t agent-bridge agent-bridge/
	docker build -t agent-studio-web agent-studio/

# Check which services have changes
check-changes:
	@echo "Checking for changes in services..."
	@if git diff --quiet HEAD~1 agent-engine/; then echo "agent-engine: No changes"; else echo "agent-engine: CHANGED"; fi
	@if git diff --quiet HEAD~1 knowledge-vault/; then echo "knowledge-vault: No changes"; else echo "knowledge-vault: CHANGED"; fi
	@if git diff --quiet HEAD~1 agent-bridge/; then echo "agent-bridge: No changes"; else echo "agent-bridge: CHANGED"; fi
	@if git diff --quiet HEAD~1 agent-studio/; then echo "agent-studio: No changes"; else echo "agent-studio: CHANGED"; fi

# Service-specific commands
agent-engine-dev:
	cd agent-engine && python main.py

knowledge-vault-dev:
	cd knowledge-vault && python app/main.py

agent-bridge-dev:
	cd agent-bridge && python app.py

agent-studio-dev:
	cd agent-studio && npm start