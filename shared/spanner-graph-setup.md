# Google Cloud Spanner Graph Setup for eA³

This document outlines how to set up Google Cloud Spanner Graph for Alchemist's eA³ (Epistemic Autonomy, Accountability, Alignment) system.

## Prerequisites

1. Google Cloud Project with billing enabled
2. Cloud Spanner API enabled
3. Service account with Spanner Database Admin role

## Setup Steps

### 1. Create Spanner Instance

```bash
# Create a regional Spanner instance
gcloud spanner instances create alchemist-graph \
    --config=regional-us-central1 \
    --description="Alchemist Agent Life-Stories Graph Database" \
    --nodes=1

# For production, consider multi-region:
# --config=nam-eur-asia1
```

### 2. Create Database

```bash
# Create the agent-stories database
gcloud spanner databases create agent-stories \
    --instance=alchemist-graph \
    --database-dialect=GOOGLE_STANDARD_SQL
```

### 3. Environment Variables

Set these environment variables in your deployment:

```bash
# Required
export GOOGLE_CLOUD_PROJECT="your-project-id"
export SPANNER_INSTANCE_ID="alchemist-graph"
export SPANNER_DATABASE_ID="agent-stories"

# Optional (uses defaults if not set)
export SPANNER_EMULATOR_HOST="localhost:9010"  # For local development
```

### 4. Service Account Setup

Create a service account for Spanner access:

```bash
# Get current project ID
PROJECT_ID=$(gcloud config get-value project)
echo "Using project: $PROJECT_ID"

# Create service account
gcloud iam service-accounts create alchemist-spanner \
    --description="Alchemist Spanner Graph Service Account" \
    --display-name="Alchemist Spanner" \
    --project=$PROJECT_ID

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-spanner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseUser"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-spanner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseReader"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-spanner@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/spanner.databaseAdmin"

# Create and download key to shared folder
gcloud iam service-accounts keys create ../shared/spanner-key.json \
    --iam-account=alchemist-spanner@$PROJECT_ID.iam.gserviceaccount.com
```

### 5. Cloud Run Deployment

Add to your Cloud Run deployment:

```yaml
# In your cloud run service YAML
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cloudsql-instances: alchemist-e69bb:us-central1:alchemist-graph
    spec:
      containers:
      - env:
        - name: GOOGLE_CLOUD_PROJECT
          value: "alchemist-e69bb"
        - name: SPANNER_INSTANCE_ID
          value: "alchemist-graph"
        - name: SPANNER_DATABASE_ID
          value: "agent-stories"
        - name: GOOGLE_APPLICATION_CREDENTIALS
          value: "/app/shared/spanner-key.json"
        volumeMounts:
        - name: spanner-key
          mountPath: /app/shared
          readOnly: true
      volumes:
      - name: spanner-key
        secret:
          secretName: spanner-service-account-key
```

## Database Schema

The eA³ system will automatically create these tables:

### Core Tables

- **StoryEvents**: Individual events in agent life-stories
- **CausalRelations**: Graph edges showing cause-effect relationships
- **NarrativeThreads**: Coherent storylines within agent narratives
- **ThreadEvents**: Many-to-many mapping of events to threads
- **BeliefRevisions**: History of recursive belief revisions (RbR)
- **AgentStories**: Metadata for each agent's overall life-story

### Key Features

- **CNE (Coherent Narrative Exclusivity)**: Each agent has one consistent story
- **RbR (Recursive Belief Revision)**: Automatic belief updating when contradictions arise
- **Accountability**: Full trace of how agents arrived at decisions
- **Alignment**: Continuous monitoring of goal alignment

## Cost Optimization

### Development/Testing
```bash
# Use single node regional instance
--nodes=1 --config=regional-us-central1
```

### Production
```bash
# Multi-region with auto-scaling
--config=nam-eur-asia1 --processing-units=1000
```

### Cost Monitoring
```bash
# Set up billing alerts
gcloud alpha billing budgets create \
    --billing-account=BILLING_ACCOUNT_ID \
    --display-name="Spanner Graph Budget" \
    --budget-amount=100USD \
    --threshold-rules-percent=50,90,100
```

## Monitoring and Maintenance

### Key Metrics to Monitor

1. **QPS (Queries Per Second)**: Should be < 80% of limit
2. **CPU Utilization**: Auto-scale when > 65%
3. **Storage Usage**: Monitor growth rate
4. **Transaction Latency**: < 100ms for 95th percentile

### Backup Strategy

```bash
# Create backup
gcloud spanner backups create agent-stories-backup \
    --instance=alchemist-graph \
    --database=agent-stories \
    --retention-period=7d
```

## Local Development with Emulator

```bash
# Start Spanner emulator
gcloud emulators spanner start

# Set environment variable
export SPANNER_EMULATOR_HOST=localhost:9010

# Create instance and database
gcloud config configurations activate emulator
gcloud spanner instances create test-instance \
    --config=emulator-config \
    --description="Test" \
    --nodes=1

gcloud spanner databases create agent-stories \
    --instance=test-instance
```

## Troubleshooting

### Common Issues

1. **Permission Denied**: Check service account roles
2. **Instance Not Found**: Verify SPANNER_INSTANCE_ID environment variable
3. **Connection Timeout**: Check network configuration and firewall rules
4. **Schema Creation Failed**: Check database admin permissions

### Debug Commands

```bash
# List instances
gcloud spanner instances list

# Check database schema
gcloud spanner databases ddl describe agent-stories \
    --instance=alchemist-graph

# Monitor operations
gcloud spanner operations list \
    --instance=alchemist-graph \
    --database=agent-stories
```

## Performance Tuning

### Query Optimization

1. Use appropriate indexes for common query patterns
2. Batch operations when possible
3. Use read-only transactions for data retrieval
4. Implement connection pooling

### Schema Design Best Practices

1. Use interleaved tables for parent-child relationships
2. Choose appropriate primary key distribution
3. Avoid hotspots with sequential keys
4. Use TIMESTAMP columns for time-series data

## Security

### Access Control

1. Use least privilege principle for service accounts
2. Enable audit logging for Spanner operations
3. Use VPC firewall rules to restrict access
4. Rotate service account keys regularly

### Data Protection

1. Enable encryption at rest (default)
2. Use SSL/TLS for connections (default)
3. Implement proper authentication in application
4. Monitor access patterns for anomalies