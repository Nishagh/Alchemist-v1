# Async Deployment Documentation

## Overview

The MCP Manager Service now supports **asynchronous deployments** with comprehensive logging and progress tracking. This update ensures that:

1. **Upload endpoints return immediately** after validation
2. **Deployments run in the background** as long-running services  
3. **Deployment logs are saved** to Cloud Storage and Firestore
4. **Progress can be tracked** in real-time
5. **Multiple deployments** can run concurrently

## Key Changes

### 1. Async Deployment Flow

**Before:**
```
Upload Config → Wait for Build → Wait for Deploy → Return Result
(5-10 minutes of blocking)
```

**After:**
```
Upload Config → Return Deployment ID (immediate)
                ↓
Background: Build → Deploy → Update Status → Save Logs
```

### 2. New API Endpoints

#### Start Deployment
```http
POST /deploy
POST /deploy-from-file
```
**Returns immediately with:**
```json
{
  "message": "Deployment started",
  "deployment_id": "uuid-here",
  "agent_id": "your-agent-id", 
  "status": "queued"
}
```

#### Track Progress
```http
GET /deployments/{deployment_id}
```
**Returns:**
```json
{
  "deployment_id": "uuid-here",
  "agent_id": "your-agent-id",
  "status": "building|deploying|completed|failed",
  "current_step": "Building Docker image",
  "progress": 45,
  "logs": ["recent log entries..."],
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Get Full Logs
```http
GET /deployments/{deployment_id}/logs
```
**Returns:**
```json
{
  "logs": "Complete deployment logs from Cloud Storage..."
}
```

## Deployment Stages

The deployment process now has clear stages with progress tracking:

| Stage | Progress | Description |
|-------|----------|-------------|
| Queued | 0% | Deployment queued for processing |
| Validating | 10% | Configuration validation |
| Config Saved | 20% | Configuration saved to Firebase |
| Building | 30-60% | Docker image build via Cloud Build |
| Deploying | 70-90% | Cloud Run service deployment |
| Verifying | 95% | Health check verification |
| Completed | 100% | Deployment successful |

## Logging Infrastructure

### Cloud Storage
- **Location:** `gs://bucket/deployment_logs/{agent_id}/{deployment_id}.log`
- **Format:** Timestamped log entries with levels (INFO, WARNING, ERROR)
- **Retention:** Permanent (can be configured with lifecycle policies)

### Firestore Collections

#### `deployment_jobs`
```json
{
  "deployment_id": "uuid",
  "agent_id": "agent-123",
  "status": "building",
  "current_step": "Building Docker image", 
  "progress": 45,
  "logs": ["last 10 log entries"],
  "created_at": "2024-01-01T00:00:00Z",
  "started_at": "2024-01-01T00:00:05Z"
}
```

#### `mcp_server_status` (updated)
```json
{
  "agent_id": "agent-123",
  "status": "creating|running|error", 
  "deployment_id": "uuid",
  "current_step": "Deploying to Cloud Run",
  "progress": 75,
  "service_url": "https://...",
  "created_at": "2024-01-01T00:00:00Z"
}
```

## Client SDK Updates

### Async Client Example
```python
from mcp_manager_client import MCPManagerClient

async with MCPManagerClient(manager_url) as client:
    # Start deployment (returns immediately)
    result = await client.deploy_from_config(
        agent_id="my-agent",
        config_data=config,
        description="My AI Agent"
    )
    
    print(f"Deployment started: {result.deployment_id}")
    
    # Track progress with callback
    def progress_callback(job):
        print(f"Progress: {job.progress}% - {job.current_step}")
        
    # Wait for completion
    final_status = await client.wait_for_deployment(
        result.deployment_id,
        progress_callback=progress_callback
    )
    
    print(f"Deployed at: {final_status.service_url}")
```

### Deploy and Wait (One Call)
```python
# For simpler usage - start deployment and wait for completion
server_status = await client.deploy_and_wait(
    agent_id="my-agent",
    config_data=config,
    progress_callback=lambda job: print(f"{job.progress}%")
)
```

### Sync Client Wrapper
```python
from mcp_manager_client import MCPManagerSyncClient

client = MCPManagerSyncClient(manager_url)

# Synchronous deployment
result = client.deploy_from_config(agent_id, config)
final_status = client.wait_for_deployment(result.deployment_id)
```

## Web Portal Integration

### Basic Integration
```javascript
// Start deployment
const response = await fetch('/deploy-from-file', {
    method: 'POST',
    body: formData  // Contains agent_id and config_file
});

const result = await response.json();
console.log(`Deployment started: ${result.deployment_id}`);

// Poll for progress
const deploymentId = result.deployment_id;
const pollProgress = setInterval(async () => {
    const status = await fetch(`/deployments/${deploymentId}`);
    const job = await status.json();
    
    updateProgressBar(job.progress);
    updateStatusMessage(job.current_step);
    
    if (job.status === 'completed') {
        clearInterval(pollProgress);
        showSuccess(job);
    } else if (job.status === 'failed') {
        clearInterval(pollProgress);
        showError(job.error_message);
    }
}, 5000);  // Poll every 5 seconds
```

### With Real-time Updates
For real-time updates, consider using WebSockets or Server-Sent Events:

```javascript
// Server-Sent Events example
const eventSource = new EventSource(`/deployments/${deploymentId}/stream`);

eventSource.onmessage = function(event) {
    const job = JSON.parse(event.data);
    updateProgress(job.progress, job.current_step);
    
    if (job.status === 'completed' || job.status === 'failed') {
        eventSource.close();
    }
};
```

## Error Handling

### Deployment Failures
When deployments fail, comprehensive error information is available:

```python
try:
    final_status = await client.wait_for_deployment(deployment_id)
except Exception as e:
    # Get detailed error logs
    logs = await client.get_deployment_logs(deployment_id)
    
    # Parse error from logs or job status
    job = await client.get_deployment_status(deployment_id)
    error_message = job.error_message
    
    print(f"Deployment failed: {error_message}")
    print(f"Full logs:\n{logs}")
```

### Common Error Scenarios
1. **Configuration validation errors** - Invalid YAML/JSON format
2. **Cloud Build failures** - Docker build issues, missing dependencies
3. **Cloud Run deployment failures** - Resource limits, networking issues  
4. **Service verification failures** - Application startup problems

## Monitoring and Alerting

### Cloud Monitoring
Set up alerts for:
- High deployment failure rates
- Long-running deployments (>10 minutes)
- Cloud Build quota exhaustion
- Storage write failures

### Log Analysis
Query deployment logs in Cloud Storage:
```bash
# Find failed deployments
gsutil ls gs://bucket/deployment_logs/*/*.log | xargs -I {} \
    gsutil cat {} | grep "ERROR"

# Deployment timing analysis  
gsutil ls gs://bucket/deployment_logs/*/*.log | xargs -I {} \
    gsutil cat {} | grep "completed"
```

## Migration Guide

### From Sync to Async

**Old synchronous code:**
```python
status = await client.deploy_from_config(agent_id, config)
# status contains final deployment result
```

**New asynchronous code:**
```python
result = await client.deploy_from_config(agent_id, config)
# result contains deployment_id for tracking

final_status = await client.wait_for_deployment(result.deployment_id)
# final_status contains deployment result
```

### Web Portal Updates

1. **Update form handlers** to use deployment IDs
2. **Add progress indicators** using the progress tracking endpoints
3. **Implement log viewing** for debugging deployment issues
4. **Handle async responses** appropriately in UI

## Testing

Run the test suite to verify async functionality:

```bash
python test_async_deployment.py
```

This tests:
- Basic async deployment flow
- Progress tracking and logging
- Deploy-and-wait functionality  
- Synchronous client wrapper
- File upload deployments
- Error handling and cleanup

## Best Practices

1. **Always track deployment progress** rather than assuming success
2. **Implement proper error handling** with log retrieval
3. **Set reasonable timeouts** (5-10 minutes for typical deployments)
4. **Use progress callbacks** to keep users informed
5. **Clean up failed deployments** to avoid resource waste
6. **Monitor deployment metrics** for system health

## Production Considerations

1. **Rate Limiting:** Implement limits on concurrent deployments per user
2. **Resource Quotas:** Monitor Cloud Build and Cloud Run quotas
3. **Log Retention:** Configure Cloud Storage lifecycle policies
4. **Error Alerts:** Set up monitoring for deployment failures
5. **Performance:** Optimize Docker image builds for faster deployments

---

For more examples and implementation details, see:
- `mcp_manager_client.py` - Client SDK with async support
- `test_async_deployment.py` - Comprehensive test suite
- `mcp_manager_service.py` - Updated service with async deployments 