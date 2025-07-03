#!/bin/bash

# Build and Test Docker Script for Accountable AI Agent
# This script builds the Docker image and tests it locally

set -e

# Configuration
AGENT_ID="9cb4e76c-28bf-45d6-a7c0-e67607675457"
IMAGE_NAME="accountable-agent"
TAG="latest"
CONTAINER_NAME="accountable-agent-test"
PORT="8000"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    docker stop $CONTAINER_NAME 2>/dev/null || true
    docker rm $CONTAINER_NAME 2>/dev/null || true
}

# Set trap for cleanup on exit
trap cleanup EXIT

# Main script
main() {
    print_status "🚀 Building and Testing Accountable AI Agent Docker Image"
    echo "============================================================"
    
    # Check if we're in the right directory
    if [ ! -f "agent-launcher/agent-template/main.py" ]; then
        print_error "Please run this script from the Alchemist-v1 directory"
        exit 1
    fi
    
    # Check if alchemist-shared exists
    if [ ! -d "shared" ]; then
        print_error "alchemist-shared not found at ./shared"
        print_error "Please ensure alchemist-shared is available in the current directory"
        exit 1
    fi
    
    print_status "✅ Environment checks passed"
    
    # Build Docker image
    print_status "🔨 Building Docker image..."
    print_status "Image: $IMAGE_NAME:$TAG"
    print_status "Agent ID: $AGENT_ID"
    
    # Build from current directory to include alchemist-shared
    docker build -t $IMAGE_NAME:$TAG -f agent-launcher/agent-template/Dockerfile .
    
    if [ $? -eq 0 ]; then
        print_success "Docker image built successfully"
    else
        print_error "Failed to build Docker image"
        exit 1
    fi
    
    # Test Docker image locally
    print_status "🧪 Testing Docker image locally..."
    
    # Stop any existing container
    cleanup
    
    # Run container with environment variables
    print_status "Starting container on port $PORT..."
        
    docker run -d \
        --name $CONTAINER_NAME \
        -p $PORT:8000 \
        -e AGENT_ID=$AGENT_ID \
        -e ENVIRONMENT=development \
        -e USE_ALCHEMIST_SHARED=true \
        -e ENABLE_GNF=true \
        -e DEBUG=false \
        $IMAGE_NAME:$TAG
    
    if [ $? -eq 0 ]; then
        print_success "Container started successfully"
    else
        print_error "Failed to start container"
        exit 1
    fi
    
    # Wait for container to be ready
    print_status "⏳ Waiting for container to be ready..."
    sleep 10

    docker logs -f $CONTAINER_NAME &
    LOG_PID=$!
    sleep 10
    kill $LOG_PID 2>/dev/null || true
    
    # Test health endpoint
    print_status "🏥 Testing health endpoint..."
    for i in {1..30}; do
        if curl -s -f http://localhost:$PORT/health > /dev/null; then
            print_success "Health endpoint responding"
            break
        fi
        if [ $i -eq 30 ]; then
            print_error "Health endpoint not responding after 30 attempts"
            docker logs $CONTAINER_NAME
            exit 1
        fi
        sleep 2
    done
    
    # Get detailed health information
    print_status "📊 Getting health information..."
    health_response=$(curl -s http://localhost:$PORT/health)
    echo "$health_response" | python3 -m json.tool
    
    # Test agent info endpoint
    print_status "🤖 Testing agent info endpoint..."
    agent_info=$(curl -s http://localhost:$PORT/agent/info)
    echo "$agent_info" | python3 -m json.tool
    
    # Test basic chat functionality
    print_status "💬 Testing basic chat functionality..."
    chat_response=$(curl -s -X POST http://localhost:$PORT/chat \
        -H "Content-Type: application/json" \
        -d '{
            "message": "Hello, can you introduce yourself?",
            "user_id": "test-user",
            "session_id": "test-session"
        }')
    
    if [ $? -eq 0 ]; then
        print_success "Chat endpoint responding"
        echo "$chat_response" | python3 -m json.tool | head -20
    else
        print_warning "Chat endpoint test failed"
    fi
    
    # Show container logs
    print_status "📋 Container logs (last 20 lines):"
    docker logs --tail 20 $CONTAINER_NAME
    
    # Performance information
    print_status "📈 Container performance:"
    docker stats --no-stream $CONTAINER_NAME
    
    # Image information
    print_status "🖼️ Image information:"
    docker images $IMAGE_NAME:$TAG
    
    print_success "✅ Docker build and test completed successfully!"
    echo ""
    echo "🎯 Container is running on: http://localhost:$PORT"
    echo "🏥 Health check: http://localhost:$PORT/health"
    echo "🤖 Agent info: http://localhost:$PORT/agent/info"
    echo "💬 Chat endpoint: http://localhost:$PORT/chat"
    echo ""
    echo "🔧 To interact with the container:"
    echo "  - View logs: docker logs $CONTAINER_NAME"
    echo "  - Stop container: docker stop $CONTAINER_NAME"
    echo "  - Remove container: docker rm $CONTAINER_NAME"
    echo "  - Shell into container: docker exec -it $CONTAINER_NAME /bin/bash"
    echo ""
    echo "🚀 Ready for deployment to Google Cloud Run!"
    
    # Ask if user wants to stop the container
    read -p "Do you want to stop the test container? (y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        cleanup
        print_success "Container stopped and removed"
    else
        print_status "Container left running for further testing"
    fi
}

# Run main function
main "$@"