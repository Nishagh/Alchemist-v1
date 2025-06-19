# Agent Billing System Documentation

## Overview

The Agent Billing System provides comprehensive billing tracking for deployed AI agents. This system differentiates between development/testing (free) and production usage (billable), ensuring accurate cost tracking for agent owners.

## Key Features

### 🆓 Development vs 💰 Production Modes

- **Development Mode**: Free testing with full functionality
- **Production Mode**: Billable usage with real-time cost tracking
- **Clear Mode Indicators**: Visual warnings and confirmations for billing

### 📊 Real-time Billing Tracking

- **Token Usage**: Accurate prompt and completion token counting
- **Cost Calculation**: Based on OpenAI GPT-4 pricing ($0.03/1K prompt tokens, $0.06/1K completion tokens)
- **Session Tracking**: Per-session cost accumulation
- **Real-time Updates**: Live billing information during conversations

### 📈 Analytics & Reporting

- **Usage Analytics**: Daily, weekly, and monthly usage patterns
- **Cost Analysis**: Detailed cost breakdowns and efficiency metrics
- **Conversation History**: Complete audit trail of all billable interactions
- **Export Functionality**: Download reports in JSON format

## Architecture

### Frontend Components

1. **AgentTesting.js** - Main testing interface with billing controls
2. **AgentAnalytics.js** - Comprehensive analytics dashboard
3. **conversationService.js** - Handles billing API calls and data persistence

### Backend Integration

The system integrates with the Universal Agent service to:
- Send messages to deployed agents
- Track token usage and costs
- Stream responses with billing metadata

### Database Schema

#### Firestore Collections

1. **`billable_conversations`**
   ```javascript
   {
     agentId: string,
     conversationId: string,
     userMessage: string,
     agentResponse: string,
     tokens: {
       prompt: number,
       completion: number,
       total: number
     },
     cost: number,
     timestamp: string,
     billable: boolean,
     testMode: boolean,
     createdAt: Timestamp
   }
   ```

2. **`agent_billing_summary`**
   ```javascript
   {
     agentId: string,
     totalMessages: number,
     totalTokens: number,
     totalCost: number,
     lastActivity: Timestamp,
     createdAt: Timestamp,
     updatedAt: Timestamp
   }
   ```

3. **`billing_sessions`**
   ```javascript
   {
     agentId: string,
     conversationId: string,
     messageCount: number,
     totalTokens: number,
     totalCost: number,
     testMode: string,
     endedAt: string,
     createdAt: Timestamp
   }
   ```

## Usage Guide

### For Agent Owners

1. **Navigate to Agent Testing**
   - Go to your agent list
   - Click the "Test" button on any agent card

2. **Choose Testing Mode**
   - **Development**: Free testing for debugging and validation
   - **Production**: Billable testing that simulates real usage

3. **Start Testing Session**
   - Click "Start Testing" to begin
   - Confirm billing mode if in production
   - Chat with your agent normally

4. **Monitor Costs**
   - Real-time cost display in the sidebar
   - Token usage tracking per message
   - Session cost accumulation

5. **View Analytics**
   - Click "View Analytics" for detailed insights
   - Export reports for billing reconciliation
   - Track usage patterns over time

### For Developers

#### Adding Billing to New Features

1. **Import Required Services**
   ```javascript
   import {
     sendMessageToDeployedAgent,
     saveBillingSession,
     getBillingInfo
   } from '../services/conversations/conversationService';
   ```

2. **Track Billable Interactions**
   ```javascript
   // Send message with billing tracking
   const response = await sendMessageToDeployedAgent({
     agentId,
     conversationId,
     message,
     testMode: 'production' // or 'development'
   });
   
   // Access billing information
   const { tokens, cost } = response;
   ```

3. **Save Session Data**
   ```javascript
   await saveBillingSession({
     agentId,
     conversationId,
     messages: messageCount,
     totalTokens,
     totalCost,
     testMode,
     endedAt: new Date().toISOString()
   });
   ```

## Configuration

### Environment Variables

```bash
# Universal Agent URL for deployed agents
REACT_APP_UNIVERSAL_AGENT_URL=https://your-agent-service-url

# Firebase configuration
REACT_APP_FIREBASE_PROJECT_ID=your-project-id
```

### Cost Calculation

The system uses standard OpenAI pricing:
- **Prompt tokens**: $0.03 per 1,000 tokens
- **Completion tokens**: $0.06 per 1,000 tokens

Modify the `calculateCost` function in `conversationService.js` to adjust pricing.

## Deployment

### Prerequisites

1. **Firebase Setup**
   - Firestore database with billing collections
   - Proper security rules for user data isolation

2. **Universal Agent Service**
   - Deployed agent endpoints
   - Token usage tracking enabled
   - Streaming response support

### Firestore Security Rules

```javascript
rules_version = '2';
service cloud.firestore {
  match /databases/{database}/documents {
    // Billing conversations - user can only access their own agent's data
    match /billable_conversations/{conversationId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.userId;
    }
    
    // Agent billing summaries
    match /agent_billing_summary/{agentId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == get(/databases/$(database)/documents/alchemist_agents/$(agentId)).data.userId;
    }
    
    // Billing sessions
    match /billing_sessions/{sessionId} {
      allow read, write: if request.auth != null 
        && request.auth.uid == resource.data.userId;
    }
  }
}
```

## Monitoring & Alerts

### Cost Monitoring

Implement alerts for:
- Daily cost thresholds per agent
- Unusual token usage patterns
- Failed billing transactions

### Analytics Tracking

- **User Engagement**: Test session frequency and duration
- **Cost Efficiency**: Token usage optimization opportunities
- **Feature Usage**: Most used agent types and capabilities

## Troubleshooting

### Common Issues

1. **Billing Not Tracking**
   - Verify agent deployment status
   - Check Firestore permissions
   - Confirm Universal Agent service connectivity

2. **Token Count Mismatches**
   - Ensure Universal Agent returns accurate token counts
   - Verify cost calculation formulas
   - Check for streaming response token aggregation

3. **Analytics Not Loading**
   - Verify Firestore query permissions
   - Check date range filters
   - Confirm agent ownership

### Debug Mode

Enable debug logging by setting:
```javascript
localStorage.setItem('DEBUG_BILLING', 'true');
```

## Future Enhancements

- **Usage Limits**: Set daily/monthly spending limits per agent
- **Billing Plans**: Tiered pricing for different usage levels
- **Cost Optimization**: AI-powered suggestions for reducing costs
- **Integration**: Stripe/payment gateway integration for automatic billing
- **Alerts**: Email/SMS notifications for cost thresholds
- **Multi-tenant**: Support for team billing and cost allocation

## Support

For issues related to the billing system:
1. Check the browser console for error messages
2. Verify Firestore data integrity
3. Test with development mode first
4. Contact support with agent ID and error details