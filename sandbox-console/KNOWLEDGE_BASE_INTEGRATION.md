# Knowledge Base Service Integration for Standalone Agent

This document explains how to use the Knowledge Base Service integration with the standalone agent. The integration provides semantic search capabilities that allow agents to search through their knowledge base for relevant information.

## Overview

The standalone agent can now access the Knowledge Base Service to perform semantic searches across documents that have been uploaded to the agent's knowledge base. This follows the conversation-centric architecture of the Alchemist system, where each agent has its own knowledge base without needing to retain state.

## Components

1. **Knowledge Base Service Client (`knowledge_service.py`)**: 
   - Provides a client for interacting with the Knowledge Base Service
   - Focuses solely on semantic search functionality

2. **Knowledge Base Tool (`knowledge_base_tool.py`)**: 
   - Implements a LangChain tool for searching the agent's knowledge base
   - Formats search results for the agent to use in responses

3. **Agent Integration (`agent.py`)**: 
   - Adds the Knowledge Base Search tool to the agent
   - Ensures the agent can use the correct agent_id for knowledge base searches

## Prerequisites

Before using the Knowledge Base Service integration, ensure:

1. The Knowledge Base Service is deployed and accessible
2. You have an agent ID that has documents uploaded to its knowledge base
3. The necessary environment variables are set (see Environment Variables section)

## Environment Variables

The following environment variables are required for the Knowledge Base Service integration:

- `KNOWLEDGE_BASE_URL`: URL of the Knowledge Base Service (default: "https://knowledge-base-service-b3hpe34qdq-uc.a.run.app")
- `DEFAULT_AGENT_ID`: ID of the agent to use for knowledge base searches
- `OPENAI_API_KEY`: OpenAI API key for the agent
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to the service account credentials file for Firebase

## Deployment

The deployment script supports both local deployment and cloud deployment to Google Cloud Run.

### Local Deployment

1. Run the deployment script and select local deployment:
   ```bash
   ./deploy.sh
   ```

2. Follow the prompts to provide any missing environment variables.

3. The script will:
   - Check for required environment variables
   - Install dependencies
   - Update the .env file
   - Verify the Knowledge Base Service connection

### Google Cloud Deployment

1. Set the following environment variables (or you'll be prompted for them):
   ```bash
   export GCP_PROJECT_ID="your-gcp-project-id"
   export SERVICE_NAME="standalone-agent" # Optional, default is standalone-agent
   export REGION="us-central1" # Optional, default is us-central1
   ```

2. Run the deployment script and select Google Cloud Run deployment:
   ```bash
   ./deploy.sh
   ```

3. Choose your preferred build method:
   - Local Docker build and push to Google Container Registry
   - Google Cloud Build (build in the cloud)

4. The script will:
   - Verify the existing Dockerfile in the project
   - Build the Docker image (locally or in the cloud)
   - Deploy the service to Google Cloud Run
   - Configure environment variables for the Cloud Run service

## Usage

Once deployed, the agent will automatically have access to its knowledge base through the search tool. The agent can use this tool to search for relevant information in response to user queries.

### Example Usage in Agent Conversations

When a user asks a question that might be answered using information from the knowledge base, the agent will:

1. Recognize that the Knowledge Base Search tool should be used
2. Call the tool with an appropriate search query
3. Process the search results
4. Incorporate the relevant information into its response

## Testing

To test the Knowledge Base Service integration:

```bash
python3 test_knowledge_base.py
```

This will:
1. Search the knowledge base for a test query
2. Test the agent with a knowledge base query

## Troubleshooting

If you encounter issues with the Knowledge Base Service integration:

1. **Knowledge Base Service Connection**:
   - Ensure the Knowledge Base Service URL is correct
   - Verify the Knowledge Base Service is running and accessible

2. **Agent ID Issues**:
   - Confirm the agent ID has documents uploaded to its knowledge base
   - Check that the agent_id is passed correctly through the environment

3. **Search Results**:
   - If search results show "No text content available", the documents might still be processing
   - Check the indexing status of documents in the Knowledge Base Service

4. **Authorization Issues**:
   - Ensure the GOOGLE_APPLICATION_CREDENTIALS file is valid and has the necessary permissions
   - Check that the OpenAI API key is valid

## Limitations

The current integration has the following limitations:

1. Only provides semantic search functionality (file upload and management are handled by the main Alchemist system)
2. Depends on documents being pre-uploaded to the agent's knowledge base
3. Search quality depends on the quality and relevance of uploaded documents

## Future Improvements

Potential future improvements for the Knowledge Base Service integration:

1. Implement advanced search filtering options
2. Add content extraction capabilities for better result formatting
3. Improve search result ranking based on relevance to the conversation context
4. Add support for conversational search refinement
