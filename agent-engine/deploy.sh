#!/bin/bash
# Deployment script for Alchemist agent engine to Google Cloud Run

set -e

# Text colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying Alchemist agent engine to Google Cloud Run...${NC}"

# Check if .env file exists and load it
if [ -f ".env" ]; then
  echo -e "Loading environment variables from .env file..."
  source .env
else
  echo -e "${YELLOW}Warning: .env file not found. Will use default or provided values.${NC}"
fi

# Extract project ID from firebase-credentials.json
FIREBASE_PROJECT_ID="alchemist-e69bb"
echo -e "${YELLOW}Found Firebase project ID: ${FIREBASE_PROJECT_ID}${NC}"

# Set GOOGLE_CLOUD_PROJECT to the Firebase project ID if not already set
if [ -z "$GOOGLE_CLOUD_PROJECT" ]; then
  GOOGLE_CLOUD_PROJECT=$FIREBASE_PROJECT_ID
  echo -e "Setting GOOGLE_CLOUD_PROJECT to Firebase project ID: $GOOGLE_CLOUD_PROJECT"
fi

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
  echo -e "${RED}Error: gcloud CLI is not installed.${NC}"
  echo "Please install it from: https://cloud.google.com/sdk/docs/install"
  exit 1
fi

# Ensure user is authenticated with gcloud
echo -e "\n${YELLOW}Checking gcloud authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q "@"; then
  echo -e "You need to authenticate with Google Cloud first."
  gcloud auth login
fi

# Set default project
echo -e "\n${YELLOW}Setting Google Cloud project to: ${GOOGLE_CLOUD_PROJECT}${NC}"
gcloud config set project $GOOGLE_CLOUD_PROJECT

# Check for OpenAI API key
if [ -z "$OPENAI_API_KEY" ]; then
  read -p "Enter your OpenAI API key: " OPENAI_API_KEY
fi

# Create .gcloudignore file
echo -e "\n${YELLOW}Creating .gcloudignore file...${NC}"
cat > .gcloudignore << EOF
.git
.github
.gitignore
.env
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
.vscode/
*.db
*.sqlite
*.log
.DS_Store
deploy*.sh
cloudbuild*.yaml
EOF

# Update cloudbuild.yaml to remove firebase-api-key reference
echo -e "\n${YELLOW}Updating cloudbuild.yaml configuration...${NC}"
sed -i.bak 's/OPENAI_API_KEY=openai-api-key:latest,FIREBASE_API_KEY=firebase-api-key:latest/OPENAI_API_KEY=openai-api-key:latest/g' cloudbuild.yaml
rm -f cloudbuild.yaml.bak

# Start the build
echo -e "\n${YELLOW}Starting Cloud Build deployment...${NC}"
gcloud builds submit --config=cloudbuild.yaml

echo -e "\n${GREEN}Deployment initiated! Build and deployment progress can be monitored in the Google Cloud Console.${NC}"
echo -e "Once complete, your service will be available at: https://alchemist-agent-engine-[hash].run.app" 