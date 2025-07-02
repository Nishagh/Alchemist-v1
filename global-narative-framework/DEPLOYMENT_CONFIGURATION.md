# Global Narrative Framework - Deployment Configuration Guide

## ✅ Current Status

The Global Narrative Framework (GNF) service has been **successfully tested and validated** with the following working functionality:

### Working Components ✅
- **Core GNF Components**: Firebase client, narrative tracker, memory integration, identity evolution
- **Firebase Integration**: Full connectivity and data persistence 
- **Lifecycle Event Recording**: Integrated with alchemist-shared lifecycle service
- **Story Event Publishing**: Pub/Sub integration for agent story events
- **Agent Creation/Tracking**: Complete agent lifecycle management
- **API Endpoints**: All REST API endpoints functional

### Validated Integrations ✅
- **Agent Lifecycle Service**: Records GNF events to `agent_lifecycle_events` collection
- **Story Event System**: Publishes to Pub/Sub topic `agent-story-events`
- **Firebase Collections**: Agents, conversations, memories, evolution events
- **Alchemist Shared**: Metrics, configuration, and event systems

## ⚠️ Configuration Requirements

### Required Environment Variables

For full EA3/Spanner integration, set these environment variables:

```bash
# Google Cloud Configuration
export GOOGLE_CLOUD_PROJECT="alchemist-e69bb"
export SPANNER_INSTANCE_ID="alchemist-graph"
export SPANNER_DATABASE_ID="agent-stories"

# Local Development (if not running on GCP)
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"

# Optional Redis for Caching
export REDIS_URL="redis://localhost:6379"

# Service Configuration
export PORT="8080"
export HOST="0.0.0.0"
export LOG_LEVEL="info"
```

### Cloud Resources Setup

1. **Spanner Database**:
   ```sql
   -- Create Spanner instance: alchemist-graph
   -- Create database: agent-stories
   -- Required tables: AgentStories, StoryEvents, NarrativeThreads, BeliefRevisions
   ```

2. **Pub/Sub Topics**:
   ```bash
   # Topic: agent-story-events
   # Subscriptions: ea3-processor, narrative-coherence
   ```

3. **IAM Permissions**:
   ```yaml
   # Service account needs:
   - roles/spanner.databaseUser
   - roles/pubsub.publisher
   - roles/pubsub.subscriber
   - roles/firestore.user
   ```

## 🚀 Deployment Commands

### Cloud Run Deployment

```bash
# Build and deploy GNF service
cd global-narative-framework

# Build Docker image
docker build -t gcr.io/alchemist-e69bb/gnf-service .

# Push to Container Registry
docker push gcr.io/alchemist-e69bb/gnf-service

# Deploy to Cloud Run
gcloud run deploy gnf-service \
  --image gcr.io/alchemist-e69bb/gnf-service \
  --platform managed \
  --region us-central1 \
  --set-env-vars GOOGLE_CLOUD_PROJECT=alchemist-e69bb \
  --set-env-vars SPANNER_INSTANCE_ID=alchemist-graph \
  --set-env-vars SPANNER_DATABASE_ID=agent-stories \
  --allow-unauthenticated \
  --memory 1Gi \
  --cpu 1 \
  --concurrency 100 \
  --timeout 300
```

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
source .env

# Run locally
python main.py
```

## 📊 Service Health Check

The service includes a comprehensive health endpoint at `/health` that reports:

```json
{
  "status": "healthy",
  "service": "global-narrative-framework",
  "components": {
    "narrative_tracker": true,
    "memory_integration": true,
    "identity_evolution": true,
    "ai_enhancement": true,
    "ea3_orchestrator": true,
    "story_event_publisher": true,
    "openai": {
      "status": "configured",
      "source": "alchemist-shared"
    }
  }
}
```

## 🔗 Service Integration

### Agent Studio Integration

GNF provides specialized endpoints for Agent Studio:

- `GET /agents/{agent_id}/identity` - Agent identity data
- `GET /agents/{agent_id}/responsibility/report` - Responsibility reports
- `GET /agents/{agent_id}/story` - AI-generated story summaries

### Story Event Flow

1. **Agent Creation** → Lifecycle Event → Story Event → Spanner Recording
2. **Interactions** → Narrative Analysis → Story Event → EA3 Processing
3. **Actions** → Responsibility Tracking → Story Event → Coherence Check

## 🛠️ Troubleshooting

### Common Issues

1. **Spanner Connection Issues**:
   - Verify `GOOGLE_CLOUD_PROJECT` is set
   - Check service account permissions
   - Ensure Spanner instance exists

2. **Story Events Not Publishing**:
   - Check Pub/Sub topic exists
   - Verify publisher permissions
   - Review project ID configuration

3. **AI Features Disabled**:
   - OpenAI API key configured in alchemist-shared
   - Check OpenAI service initialization

### Logs and Monitoring

```bash
# View service logs
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=gnf-service"

# Monitor Pub/Sub
gcloud pubsub topics list
gcloud pubsub subscriptions list

# Check Spanner
gcloud spanner instances list
gcloud spanner databases list --instance=alchemist-graph
```

## 📈 Performance Metrics

The service automatically records metrics via alchemist-shared:

- **Lifecycle Events**: Success/failure rates, event types
- **Story Publishing**: Pub/Sub publish rates, errors
- **API Performance**: Response times, error rates
- **Memory Usage**: Memory integration operations

## 🔒 Security

- Service account follows principle of least privilege
- Environment variables for sensitive configuration
- Firebase security rules enforced
- CORS configured for allowed origins

---

**Status**: ✅ Ready for deployment with proper environment configuration
**Last Validated**: $(date)
**Version**: 2.0.0