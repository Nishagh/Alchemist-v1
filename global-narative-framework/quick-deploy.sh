#!/bin/bash
# Quick deployment script for Global Narrative Framework
# Use this for rapid deployments when secrets are already set up

set -e

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Quick deploying Global Narrative Framework...${NC}"

# Set project
FIREBASE_PROJECT_ID="alchemist-e69bb"
gcloud config set project $FIREBASE_PROJECT_ID

# Quick build and deploy
echo -e "${YELLOW}Starting build...${NC}"
gcloud builds submit --config=cloudbuild.yaml

echo -e "${GREEN}Quick deployment complete!${NC}"
echo -e "Service URL: https://global-narrative-framework-851487020021.us-central1.run.app"