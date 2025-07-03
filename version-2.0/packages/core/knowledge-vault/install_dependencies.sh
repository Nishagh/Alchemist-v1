#!/bin/bash

# Script to install dependencies for Knowledge Base Service
# This script handles common dependency issues and ensures smooth installation

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Setting up Knowledge Base Service dependencies...${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Upgrade basic tools first to avoid common issues
echo -e "${YELLOW}Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel

# Install dependencies in the correct order to avoid issues
echo -e "${YELLOW}Installing core dependencies...${NC}"
pip install fastapi uvicorn python-multipart python-dotenv pydantic httpx tenacity gunicorn

echo -e "${YELLOW}Installing Google Cloud dependencies...${NC}"
pip install firebase-admin google-cloud-storage

echo -e "${YELLOW}Installing document processing libraries...${NC}"
pip install pypdf docx2txt beautifulsoup4

echo -e "${YELLOW}Installing vector search dependencies...${NC}"
pip install numpy scikit-learn

echo -e "${YELLOW}Installing OpenAI and LangChain...${NC}"
pip install langchain langchain-openai

echo -e "${GREEN}All dependencies installed successfully!${NC}"
echo -e "${YELLOW}You can now run the service with:${NC}"
echo -e "${GREEN}./run_local.sh${NC}"
