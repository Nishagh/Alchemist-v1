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
	@echo "  🚀 Smart Deployment (Recommended):"
	@echo "    deploy           - Auto-deploy changed services (smart deployment)"
	@echo "    deploy-all       - Deploy all services with smart system"
	@echo "    deploy-group     - Deploy services by group (core, tools, frontend, etc.)"
	@echo "    deploy-services  - Deploy specific services"
	@echo "    deploy-diff      - Show what would be deployed (dry run)"
	@echo "    deploy-status    - Check deployment status"
	@echo "    deploy-rollback  - Rollback service to previous version"
	@echo "    validate-deployment - Validate deployment configuration"
	@echo ""
	@echo "  📈 Legacy Deployment:"
	@echo "    deploy-unified   - Deploy all services with unified system (legacy)"
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
	@echo "Installing core services dependencies..."
	cd packages/core/agent-engine && pip install -r requirements.txt
	cd packages/core/knowledge-vault && pip install -r requirements.txt
	cd packages/core/prompt-engine && pip install -r requirements.txt
	@echo "Installing integration services dependencies..."
	cd packages/integrations/agent-bridge && pip install -r requirements.txt
	cd packages/integrations/banking-api-service && pip install -r requirements.txt
	@echo "Installing frontend dependencies..."
	cd packages/frontend/agent-studio && npm install
	cd packages/frontend/admin-dashboard && npm install
	@echo "Installing shared library..."
	cd packages/shared && pip install -e .
	@echo "Installing development dependencies..."
	pip install pytest black flake8 mypy

# Run tests
test:
	@echo "Running core services tests..."
	cd packages/core/agent-engine && python -m pytest tests/ || true
	cd packages/core/knowledge-vault && python -m pytest tests/ || true
	cd packages/core/prompt-engine && python -m pytest tests/ || true
	@echo "Running integration services tests..."
	cd packages/integrations/agent-bridge && python -m pytest tests/ || true
	cd packages/integrations/banking-api-service && python -m pytest tests/ || true
	@echo "Running frontend tests..."
	cd packages/frontend/agent-studio && npm test -- --watchAll=false || true

# Lint code
lint:
	@echo "Linting Python services..."
	flake8 packages/core --exclude=venv,__pycache__,node_modules
	flake8 packages/integrations --exclude=venv,__pycache__,node_modules
	flake8 packages/infrastructure --exclude=venv,__pycache__,node_modules
	flake8 packages/tools --exclude=venv,__pycache__,node_modules
	@echo "Linting frontend services..."
	cd packages/frontend/agent-studio && npm run lint || true

# Format code
format:
	@echo "Formatting Python code..."
	black packages/core --exclude=venv
	black packages/integrations --exclude=venv
	black packages/infrastructure --exclude=venv
	black packages/tools --exclude=venv
	@echo "Formatting frontend code..."
	cd packages/frontend/agent-studio && npm run format || true

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	cd packages/frontend/agent-studio && rm -rf build/ node_modules/.cache/ || true

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

# Smart Deployment System (Recommended)
deploy:
	@echo "🔍 Auto-deploying changed services..."
	./deployment/scripts/deploy-smart.sh auto

deploy-all:
	@echo "🚀 Deploying all services with smart system..."
	./deployment/scripts/deploy-smart.sh all

deploy-group:
	@if [ -z "$(GROUP)" ]; then \
		echo "❌ Error: GROUP parameter required"; \
		echo "Usage: make deploy-group GROUP=core"; \
		echo "Available groups: core, integrations, infrastructure, tools, frontend"; \
		exit 1; \
	fi
	@echo "🔧 Deploying group: $(GROUP)..."
	./deployment/scripts/deploy-smart.sh group $(GROUP)

deploy-services:
	@if [ -z "$(SERVICES)" ]; then \
		echo "❌ Error: SERVICES parameter required"; \
		echo "Usage: make deploy-services SERVICES=\"agent-engine knowledge-vault\""; \
		exit 1; \
	fi
	@echo "🎯 Deploying services: $(SERVICES)..."
	./deployment/scripts/deploy-smart.sh services $(SERVICES)

deploy-diff:
	@echo "🔍 Showing deployment diff (dry run)..."
	./deployment/scripts/deploy-smart.sh auto --dry-run

deploy-status:
	@echo "📊 Checking deployment status..."
	./deployment/scripts/deploy-smart.sh status

deploy-rollback:
	@if [ -z "$(SERVICE)" ]; then \
		echo "❌ Error: SERVICE parameter required"; \
		echo "Usage: make deploy-rollback SERVICE=agent-engine"; \
		exit 1; \
	fi
	@echo "🔄 Rolling back service: $(SERVICE)..."
	./deployment/scripts/deploy-smart.sh rollback $(SERVICE)

validate-deployment:
	@echo "🔍 Validating deployment configuration..."
	./deployment/scripts/deploy-smart.sh validate

# Legacy Deployment (Maintained for backward compatibility)
deploy-unified:
	@echo "🚀 Deploying all services with unified system (legacy)..."
	./deployment/scripts/legacy/deploy-unified.sh all

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
	docker build -t agent-engine packages/core/agent-engine/
	docker build -t knowledge-vault packages/core/knowledge-vault/
	docker build -t prompt-engine packages/core/prompt-engine/
	docker build -t agent-bridge packages/integrations/agent-bridge/
	docker build -t alchemist-agent-studio packages/frontend/agent-studio/

# Check which services have changes
check-changes:
	@echo "Checking for changes in services..."
	@if git diff --quiet HEAD~1 packages/core/agent-engine/; then echo "agent-engine: No changes"; else echo "agent-engine: CHANGED"; fi
	@if git diff --quiet HEAD~1 packages/core/knowledge-vault/; then echo "knowledge-vault: No changes"; else echo "knowledge-vault: CHANGED"; fi
	@if git diff --quiet HEAD~1 packages/integrations/agent-bridge/; then echo "agent-bridge: No changes"; else echo "agent-bridge: CHANGED"; fi
	@if git diff --quiet HEAD~1 packages/frontend/agent-studio/; then echo "agent-studio: No changes"; else echo "agent-studio: CHANGED"; fi

# Service-specific commands
agent-engine-dev:
	cd packages/core/agent-engine && python main.py

knowledge-vault-dev:
	cd packages/core/knowledge-vault && python main.py

prompt-engine-dev:
	cd packages/core/prompt-engine && python main.py

agent-bridge-dev:
	cd packages/integrations/agent-bridge && python app.py

agent-studio-dev:
	cd packages/frontend/agent-studio && npm start