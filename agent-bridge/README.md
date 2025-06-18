# WhatsApp BSP Service

A direct WhatsApp Business API integration service for AI agents. No third-party providers like Twilio needed!

## Features

- **Managed Account Creation**: Automatically create and manage WhatsApp Business accounts
- **Phone Number Verification**: SMS and voice verification for phone numbers
- **Message Routing**: Route incoming WhatsApp messages to AI agents
- **Webhook Processing**: Handle WhatsApp webhooks and message status updates
- **Direct WhatsApp API**: Native WhatsApp Business API integration (no Twilio required)
- **Firebase Integration**: Store account data and webhook logs in Firestore
- **Test Messaging**: Send test messages to verify integrations
- **Health Monitoring**: Account health checks and analytics

## Quick Start

### 1. Environment Setup

```bash
# Clone and navigate to the project
cd /path/to/Whatsapp-integration

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### 2. Firebase Setup

1. Create a Firebase project
2. Generate service account credentials
3. Download the JSON file to `./credentials/firebase-credentials.json`
4. Update `FIREBASE_PROJECT_ID` in `.env`

### 3. WhatsApp Business API Setup

1. Create a Facebook Business account at [business.facebook.com](https://business.facebook.com)
2. Set up WhatsApp Business API access through Meta Business Manager
3. Create a Facebook App and get your App ID, App Secret, and Access Token
4. Update WhatsApp credentials in `.env`
5. Note: WhatsApp numbers are now configured per agent during account creation

### 4. Run with Docker

```bash
# Build and run
docker-compose up -d

# Check logs
docker-compose logs -f whatsapp-bsp

# Stop
docker-compose down
```

### 5. Run Locally

```bash
# Install dependencies
pip install -r requirements.txt

# Run the server
uvicorn app:app --host 0.0.0.0 --port 8000 --reload
```

## WhatsApp Business API Benefits

✅ **50-70% Cost Savings** - No Twilio markup fees  
✅ **Latest Features** - Direct access to newest WhatsApp features  
✅ **Better Control** - Full control over verification and messaging  
✅ **Higher Limits** - Better rate limits and quotas  
✅ **Official Support** - Direct relationship with Meta/WhatsApp

## API Endpoints

### Account Management

- `POST /api/bsp/create-account` - Create managed WhatsApp account
- `POST /api/bsp/verify-phone` - Verify phone number
- `POST /api/bsp/request-verification` - Request verification code
- `GET /api/bsp/account-health/{deployment_id}` - Get account health
- `DELETE /api/bsp/delete-account/{deployment_id}` - Delete account

### Messaging

- `POST /api/bsp/send-test-message` - Send test message
- `POST /api/bsp/send-message` - Send WhatsApp message

### Webhooks

- `GET /api/webhook/whatsapp` - Webhook verification
- `POST /api/webhook/whatsapp` - Webhook message handler

### Health

- `GET /health` - Service health check

## Usage Example

### Create Account

```bash
curl -X POST "http://localhost:8000/api/bsp/create-account" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "deployment_123",
    "phone_number": "+1234567890",
    "business_profile": {
      "name": "My AI Agent",
      "industry": "technology",
      "description": "AI-powered customer service"
    },
    "webhook_config": {
      "url": "https://your-domain.com/api/webhook/whatsapp",
      "events": ["message.received", "message.delivered"]
    },
    "agent_webhook_url": "https://your-agent-api.com/webhook/whatsapp"
  }'
```

### Verify Phone Number

```bash
curl -X POST "http://localhost:8000/api/bsp/verify-phone" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "deployment_123",
    "verification_code": "123456",
    "verification_method": "sms"
  }'
```

### Send Test Message

```bash
curl -X POST "http://localhost:8000/api/bsp/send-test-message" \
  -H "Content-Type: application/json" \
  -d '{
    "account_id": "deployment_123",
    "to": "+1987654321",
    "message": "Hello! This is a test from your AI agent."
  }'
```

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Frontend      │───▶│   BSP Service    │───▶│  WhatsApp API   │
│   (React)       │    │   (FastAPI)      │    │    (Meta)       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        │
                       ┌──────────────────┐              │
                       │   Firebase       │              │
                       │   (Firestore)    │              │
                       └──────────────────┘              │
                                                         │
                       ┌──────────────────┐              │
                       │   AI Agent       │◀─────────────┘
                       │   (Your API)     │ WhatsApp Messages
                       └──────────────────┘ via Webhook
```

## Agent Integration

### How It Works

The BSP service integrates with AI agents through webhooks, eliminating the need for a centralized agent URL:

1. **Account Creation**: When creating a WhatsApp account, you provide the `agent_webhook_url` specific to that deployment
2. **Message Routing**: Incoming WhatsApp messages are automatically routed to the agent's webhook URL
3. **Response Handling**: The agent responds with a message that gets sent back to the WhatsApp user

### Agent Webhook Format

Your AI agent should provide a webhook endpoint that:

**Receives POST requests with this payload:**
```json
{
  "message_id": "wamid.xxx",
  "from": "+1234567890",
  "content": "User's message text",
  "message_type": "text",
  "timestamp": "2024-01-01T12:00:00Z",
  "context": null,
  "business_info": {
    "name": "Your Business",
    "phone": "+0987654321"
  },
  "metadata": {
    "deployment_id": "deployment_123",
    "account_id": "account_456"
  }
}
```

**Returns a response like:**
```json
{
  "message": "Hello! How can I help you today?",
  "message_type": "text",
  "context": null
}
```

### Example Agent Implementation

```python
from fastapi import FastAPI

app = FastAPI()

@app.post("/webhook/whatsapp")
async def handle_whatsapp_message(payload: dict):
    user_message = payload["content"]
    from_number = payload["from"]
    
    # Process with your AI agent
    response = await your_ai_agent.process(user_message)
    
    return {
        "message": response,
        "message_type": "text"
    }
```

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FIREBASE_PROJECT_ID` | Firebase project ID | Yes |
| `FIREBASE_CREDENTIALS_PATH` | Path to Firebase credentials JSON | Yes |
| `WHATSAPP_ACCESS_TOKEN` | WhatsApp Business API access token | Yes |
| `WHATSAPP_APP_ID` | Facebook App ID | Yes |
| `WHATSAPP_APP_SECRET` | Facebook App Secret | Yes |
| `WHATSAPP_API_VERSION` | WhatsApp API version (default: v18.0) | No |
| `WEBHOOK_VERIFY_TOKEN` | Webhook verification token | No |
| `WEBHOOK_BASE_URL` | Base URL for webhooks | No |

### Firebase Collections

- `whatsapp_accounts` - Managed account data
- `whatsapp_webhook_logs` - Webhook processing logs

## Development

### Project Structure

```
whatsapp-integration/
├── app.py                 # Main FastAPI application
├── config/
│   └── settings.py        # Configuration management
├── models/
│   ├── account_models.py  # Account-related Pydantic models
│   └── webhook_models.py  # Webhook payload models
├── services/
│   ├── bsp_provider.py    # Abstract BSP interface
│   ├── twilio_provider.py # Twilio BSP implementation
│   ├── firebase_service.py# Firebase/Firestore integration
│   └── webhook_service.py # Webhook processing service
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker configuration
├── docker-compose.yml    # Docker Compose setup
└── README.md            # This file
```

### Getting WhatsApp Business API Credentials

1. **Facebook Business Account**: Sign up at [business.facebook.com](https://business.facebook.com)
2. **WhatsApp Business API Access**: Apply for access through Meta Business Manager
3. **Create Facebook App**: 
   - Go to [developers.facebook.com](https://developers.facebook.com)
   - Create a new app with WhatsApp Business API product
   - Get App ID, App Secret, and generate Access Token
4. **Phone Number Registration**: Register your WhatsApp business phone numbers
5. **Webhook Setup**: Configure webhook URLs in your app settings

### Testing

```bash
# Run tests (when implemented)
pytest

# Test API endpoints
curl http://localhost:8000/health
```

## Deployment

### Production Considerations

1. **Security**: Use proper secrets management for credentials
2. **Scaling**: Consider using Redis for session storage
3. **Monitoring**: Add proper logging and monitoring
4. **SSL**: Use HTTPS for webhook endpoints
5. **Rate Limiting**: Implement rate limiting for API endpoints

### Cloud Run Deployment

```bash
# Build for Cloud Run
docker build -t gcr.io/your-project/whatsapp-bsp .

# Push to Container Registry
docker push gcr.io/your-project/whatsapp-bsp

# Deploy to Cloud Run
gcloud run deploy whatsapp-bsp \
  --image gcr.io/your-project/whatsapp-bsp \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated
```

## Troubleshooting

### Common Issues

1. **Firebase Permission Denied**: Check service account permissions
2. **WhatsApp API Access Denied**: Verify your Meta Business Manager access
3. **Phone Verification Fails**: Check phone number format and WhatsApp Business API limits
4. **Message Sending Fails**: Verify phone number is registered with WhatsApp Business API
5. **Webhook Issues**: Ensure webhook URL is publicly accessible and uses HTTPS

### Logs

```bash
# View logs
docker-compose logs -f whatsapp-bsp

# Check health
curl http://localhost:8000/health
```

## Support

For issues and questions:
1. Check the logs for error details
2. Verify all environment variables are set
3. Test individual API endpoints
4. Check Firebase and Meta Business Manager dashboards
5. Verify WhatsApp Business API quotas and limits