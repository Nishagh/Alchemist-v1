# Agent Tuning Service

Microservice for fine-tuning AI agents using conversation-based training data. This service provides APIs for managing training jobs, processing training data, and integrating with OpenAI/Claude fine-tuning endpoints.

## Features

- **Training Job Management**: Create, monitor, and manage fine-tuning jobs
- **Conversation-based Training**: Process training pairs from interactive conversations
- **Data Validation**: Automated quality checks for training data
- **Progress Tracking**: Real-time job status and progress reporting
- **Model Integration**: Interface with OpenAI fine-tuning APIs
- **Firebase Integration**: Persistent storage for jobs and results

## Architecture

This service follows the Alchemist microservices architecture as a Tier 2 service, providing specialized ML capabilities while integrating seamlessly with existing services.

### Integration Points

- **Agent Engine**: Training job lifecycle management
- **Agent Studio**: Frontend interface for training management
- **Firebase**: Job state, progress tracking, and result storage
- **OpenAI API**: Model fine-tuning execution

## API Endpoints

### Training Jobs
- `POST /api/training/jobs` - Create and queue training jobs
- `GET /api/training/jobs/{job_id}` - Get job details
- `GET /api/training/jobs/{job_id}/status` - Real-time progress tracking
- `DELETE /api/training/jobs/{job_id}` - Cancel training job

### Training Data
- `POST /api/training/data/validate` - Validate training data quality
- `POST /api/training/data/process` - Process conversation pairs
- `GET /api/training/data/{agent_id}` - Get training data for agent

### Models
- `GET /api/training/models/{agent_id}` - Get fine-tuned models for agent
- `POST /api/training/models/{agent_id}/deploy` - Deploy fine-tuned model

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python main.py

# Run tests
pytest tests/
```

## Deployment

The service is deployed as part of the Alchemist microservices stack using Google Cloud Run.

```bash
# Deploy
./deploy.sh
```