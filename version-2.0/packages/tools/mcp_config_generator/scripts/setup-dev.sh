#!/bin/bash

# Development Setup Script
# Sets up the local development environment

set -e

# Color codes
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo "🛠️  Setting up local development environment"
echo "============================================="
echo ""

# Download Go dependencies
print_status "Downloading Go dependencies..."
go mod download
go mod tidy

# Run tests
print_status "Running tests..."
if go test -v; then
    print_success "All tests passed!"
else
    echo "Tests failed. Please check the errors above."
    exit 1
fi

# Build the application
print_status "Building application..."
if go build -o converter main.go; then
    print_success "Application built successfully!"
else
    echo "Build failed. Please check the errors above."
    exit 1
fi

echo ""
print_success "🎉 Development environment is ready!"
echo ""
echo "To start the development server:"
echo "  go run main.go"
echo ""
echo "To run tests:"
echo "  go test -v"
echo ""
echo "To test the service:"
echo "  curl http://localhost:8080/health"
echo "  curl http://localhost:8080/" 