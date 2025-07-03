#!/bin/bash
echo "Testing build process..."
npm ci
echo "Dependencies installed successfully"
npm run build
echo "Build completed successfully"