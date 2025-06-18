# Prompt Engineer Service Deployment Guide

This guide provides instructions for deploying the Prompt Engineer service to Google Cloud Run using Cloud Build. The service follows Alchemist's conversation-centric architecture and is designed to be a stateless component that interacts with Firestore for data persistence.

## Alchemist Architecture Integration

The Prompt Engineer service is designed to align with Alchemist's conversation-centric architecture:

1. **Stateless Component**: The service operates as a stateless microservice, following the architectural shift from agent-state-centric to conversation-centric design.

2. **Firestore Data Model**: Uses the established data model for storing prompts:
   - `alchemist_agents/{agent_id}/system_prompt` collection for storing prompt versions

3. **OpenAI Integration**: Uses the centralized OpenAI service for API key management to ensure consistency across all components.

4. **Error Handling**: Includes proper serialization of agent thought processes when storing in Firestore.

## Prerequisites

Before deploying the service, ensure you have:

1. Google Cloud SDK installed and configured
2. Access to the Google Cloud project
3. Firebase service account credentials for Firestore access
4. OpenAI API key

## Deployment Steps

### 1. Set Up Google Cloud Project

If you haven't already set up a Google Cloud project:

```bash
# Create a new project
gcloud projects create alchemist-prompt-engineer --name="Alchemist Prompt Engineer"

# Set it as the current project
gcloud config set project alchemist-prompt-engineer
```

### 2. Enable Required APIs

The deployment script will handle this automatically, but you can also enable them manually:

```bash
# Enable required APIs
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. Set Up Secret Manager for API Keys

```bash
# Create secret for OpenAI API key
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Grant access to the service account (this is handled by the deployment script but shown here for reference)
gcloud iam service-accounts create prompt-engineer-service-sa \
    --display-name="Prompt Engineer Service Account"

# Grant Secret Manager access
gcloud projects add-iam-policy-binding alchemist-prompt-engineer \
    --member="serviceAccount:prompt-engineer-service-sa@alchemist-prompt-engineer.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"

# Grant Firestore access
gcloud projects add-iam-policy-binding alchemist-prompt-engineer \
    --member="serviceAccount:prompt-engineer-service-sa@alchemist-prompt-engineer.iam.gserviceaccount.com" \
    --role="roles/datastore.user"
```

### 4. Set Up Firebase Service Account

1. Go to the Firebase console and download your service account key JSON file
2. Store it as a secret in Google Secret Manager:

```bash
# Create secret from file
gcloud secrets create firebase-credentials --data-file=path/to/your-firebase-credentials.json

# Grant access to the service account
gcloud secrets add-iam-policy-binding firebase-credentials \
    --member="serviceAccount:prompt-engineer-service-sa@alchemist-prompt-engineer.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 5. Deploy Using Cloud Build

The provided `deploy.sh` script handles the entire deployment process using Google Cloud Build:

```bash
# Make the script executable
chmod +x deploy.sh

# Run the deployment script
./deploy.sh
```

This script will:
1. Enable necessary Google Cloud APIs
2. Create and configure the service account if needed
3. Submit the build to Cloud Build using the `cloudbuild.yaml` configuration
4. Deploy the container to Cloud Run

## Integration with Alchemist

The Prompt Engineer service is designed to work with Alchemist's conversation-centric architecture:

### API Endpoints

The service exposes the following API endpoints:

- `POST /api/prompt-engineer/update-prompt`: Create or update an agent's prompt based on instructions

### Authentication

The prompt engineer service uses the same authentication method as the Banking Agent:

```
Authorization: Bearer {api_key}
```

### Environment Variables

The service requires the following environment variables:

- `OPENAI_API_KEY`: API key for OpenAI
- `GOOGLE_APPLICATION_CREDENTIALS`: Path to Firebase credentials file
- `ENVIRONMENT`: Set to 'production' for deployed services

In Cloud Run, these are set via secrets and environment variables in the `cloudbuild.yaml` configuration.

## Monitoring and Maintenance

### Viewing Logs

```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=prompt-engineer-service" --limit 50
```

### Viewing Build Status

```bash
# List recent builds
gcloud builds list --limit=5

# View details of a specific build
gcloud builds describe BUILD_ID
```

### Updating the Service

To update the service after making changes:

1. Make your changes to the code
2. Run the deployment script again:

```bash
./deploy.sh
```

Cloud Build will handle rebuilding and redeploying the service.

## Troubleshooting

### Common Issues

1. **Firebase Authentication Failed**: Ensure the Firebase credentials are correctly set up and the service account has the necessary permissions.

2. **OpenAI API Key Invalid**: Check that the OpenAI API key is correctly stored in Secret Manager and accessible to the service.

3. **Build Failures**: Check the Cloud Build logs for details about build failures:

```bash
gcloud builds log BUILD_ID
```

4. **Serialization Errors**: If you encounter errors related to serializing data for Firestore, ensure proper handling of Firestore's SERVER_TIMESTAMP sentinel value and complex nested structures in the agent's thought process.

### Getting Help

If you encounter issues not covered in this guide, check:

1. Cloud Run logs for detailed error messages
2. Cloud Build logs for build and deployment issues
3. Google Cloud documentation for Cloud Run, Cloud Build, and Secret Manager
4. Firebase documentation for Firestore access from Google Cloud services

## Security Considerations

The service is currently configured to allow unauthenticated access. For production environments, consider:

1. Restricting access using Identity and Access Management (IAM)
2. Setting up a proper authentication mechanism
3. Configuring network policies to restrict access to the service
4. Implementing rate limiting to prevent abuse
