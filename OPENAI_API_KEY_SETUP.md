# OpenAI API Key Configuration

This document explains how OpenAI API keys are managed across all Alchemist services.

## Overview

All services now use a centralized approach for OpenAI API key management:
- **Local Development**: Use the centralized `.env.local` file or set `OPENAI_API_KEY` directly
- **Cloud Deployment**: Uses Google Secret Manager with the secret name `OPENAI_API_KEY`

## Local Development Setup

### Option 1: Use Centralized Configuration
1. Copy the API key from `.env.local` to your service-specific `.env` file:
   ```bash
   # In your service directory (e.g., agent-engine/)
   echo "OPENAI_API_KEY=$(grep OPENAI_API_KEY ../.env.local | cut -d'=' -f2)" >> .env
   ```

### Option 2: Direct Environment Variable
Set the environment variable directly:
```bash
export OPENAI_API_KEY="your-api-key-here"
```

### Option 3: Service-Specific .env
Uncomment and set the OPENAI_API_KEY in each service's `.env` file:
```bash
# Uncomment and set your API key
OPENAI_API_KEY=your-api-key-here
```

## Cloud Deployment

All services are configured to use the Google Secret Manager secret named `OPENAI_API_KEY`.

### Verify Secret Exists
```bash
gcloud secrets describe OPENAI_API_KEY --project=your-project-id
```

### Update Secret (if needed)
```bash
echo -n "your-new-api-key" | gcloud secrets versions add OPENAI_API_KEY --data-file=-
```

## Service-Specific Configuration

### Agent Tuning Service
- **Local**: Supports both `OPENAI_API_KEY` and `TUNING_OPENAI_API_KEY` (for backward compatibility)
- **Cloud**: Uses `OPENAI_API_KEY` from Google Secret Manager

### All Other Services
- **Local**: Uses `OPENAI_API_KEY` environment variable
- **Cloud**: Uses `OPENAI_API_KEY` from Google Secret Manager

## Deployment Scripts Updated

The following deployment configurations have been updated:

### Cloud Build Files
- `agent-engine/cloudbuild.yaml` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`
- `agent-tuning-service/cloudbuild.yaml` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`
- `prompt-engine/cloudbuild.yaml` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`
- `global-narative-framework/cloudbuild.yaml` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`

### Deploy Scripts
- `sandbox-console/deploy.sh` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`
- `knowledge-vault/deploy.sh` - Uses `OPENAI_API_KEY=OPENAI_API_KEY:latest`

## Security Notes

1. **Never commit API keys to git**: All service `.env` files now have API keys commented out
2. **Use Google Secret Manager for production**: All cloud deployments use secrets, not environment variables
3. **Rotate keys regularly**: Update the secret in Google Secret Manager and redeploy services
4. **Monitor usage**: Use OpenAI's dashboard to monitor API usage and costs

## Troubleshooting

### Local Development Issues
1. **"No API key found"**: Ensure `OPENAI_API_KEY` is set in your environment or `.env` file
2. **"Invalid API key"**: Verify the key is correct and not expired
3. **"Rate limit exceeded"**: Check OpenAI usage limits and quotas

### Cloud Deployment Issues
1. **"Secret not found"**: Ensure the `OPENAI_API_KEY` secret exists in Google Secret Manager
2. **"Permission denied"**: Verify the Cloud Run service account has `secretmanager.secretAccessor` role
3. **"Invalid secret version"**: Use `:latest` or specify a valid version number

## Migration from Old Setup

If you're migrating from the old setup:

1. **Remove hardcoded keys**: API keys have been removed from all `.env` files
2. **Update local development**: Use `.env.local` or set `OPENAI_API_KEY` directly
3. **Verify cloud deployment**: All deployment scripts now use the centralized secret
4. **Test thoroughly**: Verify all services can access the OpenAI API after migration