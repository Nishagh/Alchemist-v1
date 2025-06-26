# Knowledge Base Service Tools

## Vector Index Inspection Tool

This directory contains utility scripts for diagnosing and managing the Knowledge Base Service.

### List Vectors Tool (`list_vectors.py`)

This script connects to the Knowledge Base Service API and lists all vector-indexed files for a given agent. Use this to verify what documents are actually indexed in the service.

#### Prerequisites

- Python 3.6+
- Required packages: `requests`, `python-dotenv`
- Access to the Knowledge Base Service API

#### Usage

1. **For the cloud-deployed service:**

```bash
# Use the default cloud service URL
python tools/list_vectors.py --agent-id 8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7

# With verbose output to see detailed metadata
python tools/list_vectors.py --agent-id 8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7 --verbose
```

2. **For a locally running service:**

```bash
# Specify the local service URL
python tools/list_vectors.py --agent-id 8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7 --service-url http://localhost:8080
```

#### Sample Output

```
Connecting to Knowledge Base Service at https://alchemist-knowledge-vault-b3hpe34qdq-uc.a.run.app...

Vector Index Summary for Agent: 8e18dfe2-1478-4bb3-a9ee-894ff1ac81e7
Collection Name: agent_8e18dfe2_1478_4bb3_a9ee_894ff1ac81e7
Total Vectors: 24

Indexed Files (3 total):
  - banking_faq.pdf (File ID: 5f9a2d7e-1234-5678-90ab-cdef12345678, Chunks: 12)
  - account_terms.txt (File ID: 7a8b9c0d-1234-5678-90ab-cdef12345678, Chunks: 8)
  - security_guide.pdf (File ID: e1f2a3b4-1234-5678-90ab-cdef12345678, Chunks: 4)
```

## Deployment Considerations

This tool helps diagnose issues with ChromaDB persistence between deployments. On Google Cloud Run, the local filesystem is ephemeral, which means:

1. Local data (including ChromaDB indices) is wiped clean between deployments
2. The service relies on Cloud Storage for persistent data storage
3. The backup/restore mechanism in `cloud_storage.py` synchronizes data on startup/shutdown

If the vector index is empty after a deployment, check:
- The `BUCKET_NAME` environment variable is correctly set
- The service account has proper permissions for the bucket
- The service had enough time to upload data before previous shutdown
- The local and cloud paths for ChromaDB data match

## Troubleshooting

If you see inconsistencies between what the Knowledge Base Service reports and what agents receive:
1. Check that the vector index is properly populated using this tool
2. Verify that the ChromaDB persistence path is consistent across services
3. Ensure the cloud storage backup/restore mechanism is working correctly
