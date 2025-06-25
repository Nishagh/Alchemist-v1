# Firebase Credentials Setup Guide

This guide explains how to set up Firebase credentials for local development while ensuring they are never included in cloud deployments.

## Overview

The Alchemist platform uses a centralized Firebase credentials management system that:
- **Local Development**: Uses `firebase-credentials.json` file in the project root
- **Cloud Deployment**: Uses Application Default Credentials (ADC) automatically
- **Security**: Prevents credential files from being included in Docker images or deployments

## Local Development Setup

### 1. Obtain Firebase Credentials

1. Go to the [Firebase Console](https://console.firebase.google.com/)
2. Select the `alchemist-e69bb` project
3. Navigate to Project Settings > Service Accounts
4. Click "Generate new private key"
5. Save the downloaded file as `firebase-credentials.json`

### 2. Place Credentials File

**Important**: Place the `firebase-credentials.json` file in the **project root directory** (same level as this README).

```
Alchemist-v1/
├── firebase-credentials.json  ← Place here (project root)
├── agent-engine/
├── agent-studio/
├── billing-service/
├── knowledge-vault/
├── shared/
└── ...
```

### 3. Environment Variables (Optional)

You can also use environment variables for more control:

```bash
# Option 1: Explicit path to credentials file
export FIREBASE_CREDENTIALS_PATH="/path/to/your/firebase-credentials.json"

# Option 2: Standard Google Cloud credentials
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your/firebase-credentials.json"
```

### 4. Verification

Run any service locally to verify the setup:

```bash
cd billing-service
python main.py
```

You should see log messages like:
```
INFO: Using centralized Firebase credentials from project root: /path/to/firebase-credentials.json
INFO: Firebase client initialized successfully
```

## How It Works

### Credential Discovery Priority

The centralized Firebase client looks for credentials in this order:

1. **`FIREBASE_CREDENTIALS_PATH`** environment variable
2. **`GOOGLE_APPLICATION_CREDENTIALS`** environment variable  
3. **Project root** `firebase-credentials.json` (automatic discovery)
4. **Legacy locations** (with deprecation warnings)

### Cloud Deployment

In cloud environments (Google Cloud Run), the system automatically:
- Detects cloud environment using `K_SERVICE`, `GOOGLE_CLOUD_PROJECT`, etc.
- Uses Application Default Credentials (ADC)
- Validates that no credential files are present in the deployment

### Security Features

- **Docker exclusion**: All `.dockerignore` files exclude credential files
- **Git exclusion**: `.gitignore` prevents credential files from being committed (except root)
- **Deployment validation**: Deploy scripts check for and reject credential files
- **Runtime validation**: Services warn if credential files are found in cloud deployments

## Troubleshooting

### "Firebase credentials file not found"

1. Ensure `firebase-credentials.json` is in the project root
2. Check file permissions (should be readable)
3. Verify the file is valid JSON

### "Using legacy Firebase credentials location"

This warning means credentials were found in a deprecated location. Move them to the project root:

```bash
# Move from service directory to project root
mv billing-service/firebase-credentials.json ./firebase-credentials.json
```

### "Security Alert: Credential files found in cloud deployment"

This error occurs when credential files are accidentally included in a cloud deployment:

1. Check that `.dockerignore` files are properly configured
2. Ensure deploy scripts are running the security validation
3. Remove any credential files from service directories

### Services Not Using Centralized Client

If you see services initializing Firebase directly instead of using the shared client:

1. Check that the service imports `from alchemist_shared.database.firebase_client import FirebaseClient`
2. Ensure the service uses `FirebaseClient()` instead of `firebase_admin.initialize_app()`
3. Update the service to use centralized collection constants

## Best Practices

### For Developers

1. **Never commit credentials**: The `.gitignore` prevents this, but be mindful
2. **Use project root**: Always place `firebase-credentials.json` in the project root
3. **Check logs**: Look for Firebase initialization messages to verify correct setup
4. **Clean up**: Remove any old credential files from service directories

### For Services

1. **Use centralized client**: Import and use `FirebaseClient` from shared module
2. **Use collection constants**: Import from `alchemist_shared.constants.collections`
3. **Handle errors gracefully**: Catch and log Firebase initialization errors
4. **Test both environments**: Verify service works locally and in cloud

### For Deployments

1. **Run security checks**: Deploy scripts automatically validate credential exclusion
2. **Monitor logs**: Check for security warnings in cloud deployments
3. **Use proper service accounts**: Ensure Cloud Run services have appropriate Firebase permissions
4. **Test ADC**: Verify Application Default Credentials work in cloud environment

## File Structure

```
Alchemist-v1/
├── firebase-credentials.json                    # ✅ Local development (git ignored)
├── shared/alchemist_shared/database/
│   └── firebase_client.py                       # ✅ Centralized client
├── agent-engine/
│   └── alchemist/config/firebase_config.py      # ✅ Uses centralized client
├── prompt-engine/
│   └── config/firebase_config.py                # ✅ Uses centralized client
├── sandbox-console/
│   └── config/firebase_config.py                # ✅ Uses centralized client
├── alchemist-agent-tuning/
│   └── app/services/firebase_service.py         # ✅ Uses centralized client
├── billing-service/
│   ├── .dockerignore                            # ✅ Excludes credentials
│   └── app/services/firebase_service.py         # ✅ Uses centralized client
├── knowledge-vault/
│   ├── .dockerignore                            # ✅ Excludes credentials
│   └── app/services/firebase_service.py         # ✅ Uses centralized client
└── alchemist-monitor-service/
    ├── .dockerignore                            # ✅ Excludes credentials
    └── src/services/firebase_client.py          # ✅ Uses centralized client
```

## ✅ Successfully Migrated Services

The following services have been successfully updated to use centralized Firebase authentication:

**Core Services:**
- ✅ **agent-engine** - Central agent orchestration
- ✅ **prompt-engine** - Prompt processing and management  
- ✅ **alchemist-agent-tuning** - Agent training and fine-tuning
- ✅ **billing-service** - User credits and payment processing
- ✅ **knowledge-vault** - File storage and embeddings
- ✅ **alchemist-monitor-service** - System monitoring and metrics
- ✅ **sandbox-console** - Development environment

**Frontend:**
- ✅ **agent-studio** - React frontend (uses Firebase Web SDK properly)

All services now use the centralized `FirebaseClient` from `alchemist_shared.database.firebase_client` for consistent authentication and security.

## Support

If you encounter issues with Firebase credentials setup:

1. Check the service logs for specific error messages
2. Verify your Firebase project permissions
3. Ensure you're using the correct project ID: `alchemist-e69bb`
4. Contact the development team with specific error messages and steps to reproduce