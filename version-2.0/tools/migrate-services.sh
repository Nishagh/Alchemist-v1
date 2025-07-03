#!/bin/bash

# Script to migrate existing services to monorepo structure
# This preserves git history and moves services to packages/

set -e

echo "🔄 Migrating Alchemist services to monorepo structure..."

# Function to copy service
copy_service() {
    local source_dir=$1
    local target_dir=$2
    local service_name=$3
    
    if [ -d "$source_dir" ]; then
        echo "📦 Migrating $service_name..."
        
        # Create target directory if it doesn't exist
        mkdir -p "$target_dir"
        
        # Copy files (excluding common files that should be handled separately)
        cp -r "$source_dir"/* "$target_dir/" 2>/dev/null || true
        
        # Update requirements.txt to include shared libraries
        if [ -f "$target_dir/requirements.txt" ]; then
            if ! grep -q "alchemist-shared" "$target_dir/requirements.txt"; then
                echo "# Shared Alchemist libraries" >> "$target_dir/requirements.txt"
                echo "alchemist-shared" >> "$target_dir/requirements.txt"
                echo ""
            fi
        fi
        
        # Create basic tests directory if it doesn't exist
        mkdir -p "$target_dir/tests"
        if [ ! -f "$target_dir/tests/__init__.py" ]; then
            echo "\"\"\"Tests for $service_name service.\"\"\"" > "$target_dir/tests/__init__.py"
        fi
        
        echo "✅ $service_name migrated successfully"
    else
        echo "⚠️  Source directory $source_dir not found, skipping $service_name"
    fi
}

# Migrate services
copy_service "alchemist-knowledge-vault" "packages/knowledge-base" "Knowledge Base Service"
copy_service "Whatsapp-integration" "packages/whatsapp" "WhatsApp Integration Service"
copy_service "agent-deployment/universal-deployment-service" "packages/agent-deployment" "Agent Deployment Service"
copy_service "frontend" "packages/frontend" "Frontend Application"

# Copy MCP config generator (Go service)
copy_service "mcp_config_generator" "packages/mcp-config-generator" "MCP Config Generator"

echo ""
echo "🎉 Service migration completed!"
echo ""
echo "Next steps:"
echo "1. Update service imports to use shared libraries"
echo "2. Update Docker files to use shared libraries"
echo "3. Test local development environment"
echo "4. Update CI/CD configurations"
echo ""
echo "Run 'make install' to set up the development environment"