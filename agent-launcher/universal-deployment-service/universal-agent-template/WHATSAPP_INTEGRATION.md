# WhatsApp Integration for Universal Agent Template

This document explains how to configure and use WhatsApp integration with the Universal Agent Template.

## Overview

The WhatsApp integration allows deployed agents to receive and respond to WhatsApp messages through webhook endpoints. The integration dynamically loads configuration from Firestore and requires no environment variables or manual setup.

## Features

- ✅ **Dynamic Configuration**: Loads WhatsApp settings from Firestore at runtime
- ✅ **Webhook Verification**: Secure webhook verification using Meta's standards
- ✅ **Message Processing**: Handles text, image, document, and audio messages
- ✅ **Conversation Integration**: Seamlessly integrates with existing conversation system
- ✅ **Response Formatting**: Formats agent responses for WhatsApp delivery
- ✅ **Security**: Webhook signature verification and input validation
- ✅ **Error Handling**: Graceful error handling and fallback responses

## Configuration

### Firestore Configuration Structure

Add the following WhatsApp configuration to your agent document in Firestore (`agents/{agentId}`):

```json
{
  "whatsapp": {
    "enabled": true,
    "phone_id": "123456789012345",
    "access_token": "EAAxxxxxxxxxxxxx",
    "verify_token": "your_webhook_verify_token",
    "app_id": "123456789",
    "app_secret": "your_app_secret_here"
  }
}
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `enabled` | boolean | Whether WhatsApp integration is enabled |
| `phone_id` | string | WhatsApp Business phone number ID from Meta |
| `access_token` | string | Meta API access token for sending messages |
| `verify_token` | string | Webhook verification token (your choice) |
| `app_id` | string | Meta app ID (optional, for enhanced security) |
| `app_secret` | string | Meta app secret for webhook signature verification |

### Getting WhatsApp Credentials

1. **Create a Meta Developer Account**: Visit [developers.facebook.com](https://developers.facebook.com)
2. **Create an App**: Create a new app and add WhatsApp Business API
3. **Get Phone Number ID**: From the WhatsApp Business API dashboard
4. **Generate Access Token**: Create a permanent access token for your app
5. **Set Webhook URL**: Configure webhook URL to `https://your-agent-domain.com/webhook/whatsapp`
6. **Set Verify Token**: Use the same token you configured in Firestore

## Webhook Endpoints

The integration automatically adds the following endpoints to your agent:

### Webhook Verification
- **Method**: GET
- **URL**: `/webhook/whatsapp`
- **Purpose**: Meta uses this to verify your webhook during setup

### Message Processing
- **Method**: POST  
- **URL**: `/webhook/whatsapp`
- **Purpose**: Receives incoming WhatsApp messages for processing

## Message Flow

1. **User sends WhatsApp message** → Meta servers
2. **Meta forwards message** → Your agent's webhook endpoint
3. **Agent verifies signature** → Ensures message authenticity
4. **Agent processes message** → Uses existing conversation system
5. **Agent generates response** → Via LangChain agent pipeline
6. **Agent sends response** → Back to user via WhatsApp API

## Supported Message Types

### Text Messages
- Plain text messages are processed directly by the agent
- Long responses are automatically split into multiple messages

### Media Messages
- **Images**: Processes image caption as text message
- **Documents**: Acknowledges receipt and asks for text description
- **Audio**: Acknowledges receipt and asks for text description

### Interactive Messages
- Support for quick reply buttons (coming soon)
- Button responses processed as text messages

## Conversation Management

- Each WhatsApp phone number gets a unique conversation ID
- Conversation history is maintained across message exchanges
- Messages include metadata about WhatsApp source and phone number
- User ID format: `whatsapp_{phone_number}`

## Security Features

### Webhook Signature Verification
- Verifies all incoming webhooks using HMAC-SHA256
- Uses `app_secret` from Firestore configuration
- Rejects messages with invalid signatures

### Input Validation
- Validates webhook structure and required fields
- Sanitizes message content before processing
- Rate limiting protection (built into FastAPI)

## Error Handling

### Configuration Errors
- Agent starts normally if WhatsApp config is missing
- Webhook endpoints return 404 if integration not configured
- Logs clear error messages for troubleshooting

### Runtime Errors
- Failed message sends are logged but don't crash the agent
- Users receive fallback error messages for processing failures
- Webhook signature failures are logged for security monitoring

## Testing

### Local Testing with ngrok
1. Install ngrok: `npm install -g ngrok`
2. Start your agent locally: `python main.py`
3. Expose via ngrok: `ngrok http 8080`
4. Use ngrok URL for webhook configuration in Meta dashboard

### Unit Testing
Run the test suite: `python test_whatsapp.py`

## Monitoring and Debugging

### Log Messages
The integration provides detailed logging:
- WhatsApp service initialization
- Webhook verification attempts
- Message processing status
- API call results

### Health Check
Check agent status including WhatsApp integration:
```bash
curl https://your-agent-domain.com/healthz
```

### Configuration Check
View current WhatsApp configuration:
```bash
curl https://your-agent-domain.com/api/config
```

## Common Issues

### Webhook Verification Fails
- Check that `verify_token` in Firestore matches Meta dashboard
- Ensure webhook URL is accessible from the internet
- Verify agent is running and responding to requests

### Messages Not Being Processed
- Check webhook signature verification (app_secret)
- Verify access_token has required permissions
- Check agent logs for processing errors

### Responses Not Sending
- Verify access_token is valid and not expired
- Check phone_id is correct in configuration
- Ensure agent has internet access for API calls

## Production Deployment

### Security Checklist
- ✅ Use strong, unique verify_token
- ✅ Keep app_secret secure in Firestore
- ✅ Use HTTPS for all webhook URLs
- ✅ Monitor webhook signature verification logs
- ✅ Regularly rotate access tokens

### Performance Considerations
- Messages are processed in background tasks
- Webhook responses are immediate (200 OK)
- Long agent responses are automatically chunked
- Failed sends are retried automatically by Meta

## Example Usage

Once configured, users can interact with your agent via WhatsApp:

**User**: "Hello, what can you help me with?"
**Agent**: "Hi! I'm an AI assistant. I can help you with questions, provide information, and assist with various tasks. What would you like to know?"

**User**: "Tell me about the weather"
**Agent**: [Agent processes using available tools and responds with weather information]

The integration maintains full conversation context and leverages all existing agent capabilities including knowledge bases, MCP tools, and custom functions.