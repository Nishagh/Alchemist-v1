# Knowledge Base Service

A FastAPI-based service for managing knowledge bases with file upload, text extraction, semantic search, and vector storage capabilities.

## Features

- **File Upload & Processing**: Upload PDF, DOCX, TXT, and HTML files
- **Text Extraction**: Automatic text extraction from various file formats
- **Vector Indexing**: Create embeddings using OpenAI's embedding models
- **Semantic Search**: Search documents using natural language queries
- **Vector Storage**: Save and load vectors from Firebase Storage
- **ChromaDB Integration**: Local vector database for fast search operations
- **Firebase Integration**: Cloud storage and metadata management

## Enhanced Workflow

### File Upload Process
1. **Save Raw File**: Upload file to Firebase Storage
2. **Process & Index**: Extract text, create chunks, generate embeddings
3. **Store in ChromaDB**: Save vectors to local ChromaDB instance
4. **Save to Storage**: Automatically export vectors to Firebase Storage

### Search Process  
Two search methods available:

**Method 1: ChromaDB Search (Fast)**
- Search directly from local ChromaDB instance
- Fastest performance for real-time queries

**Method 2: Storage-Based Search (Persistent)**
- Load vectors from Firebase Storage
- Search against loaded vectors
- Ensures data persistence across service restarts

## API Endpoints

### File Operations
- `POST /upload-knowledge-base` - Upload and index a file
- `GET /knowledge-base/{agent_id}/files` - List all files for an agent
- `GET /knowledge-base/files/{file_id}` - Get file metadata
- `DELETE /knowledge-base/files/{file_id}` - Delete file (basic)
- `DELETE /knowledge-base/files/{file_id}/with-vectors` - Delete file and vectors
- `DELETE /knowledge-base/files/{file_id}/and-update-storage` - Delete file and update vector storage

### Vector Management
- `GET /knowledge-base/{agent_id}/vector-files` - List vector export files
- `GET /knowledge-base/{agent_id}/vectors/load` - Load vectors from storage
- `POST /knowledge-base/{agent_id}/vectors/save` - Save vectors to storage
- `GET /knowledge-base/files/{file_id}/vectors` - Get vectors for specific file

### Search Operations
- `POST /search-knowledge-base` - Search using ChromaDB (fast)
- `GET /search-knowledge-base` - Search using ChromaDB (GET method)
- `POST /search-knowledge-base/storage` - Search using storage vectors
- `GET /search-knowledge-base/storage` - Search using storage vectors (GET method)

### Vector Information
- `GET /vectors/{agent_id}` - List all vectors in ChromaDB for an agent

## Usage Examples

### Upload a File
```bash
curl -X POST "http://localhost:8000/upload-knowledge-base" \
  -F "file=@document.pdf" \
  -F "agent_id=agent123"
```

### Search Knowledge Base (ChromaDB)
```bash
curl -X GET "http://localhost:8000/search-knowledge-base?agent_id=agent123&query=machine learning&top_k=5"
```

### Search Knowledge Base (Storage)
```bash
curl -X GET "http://localhost:8000/search-knowledge-base/storage?agent_id=agent123&query=machine learning&top_k=5"
```

### List Vector Files
```bash
curl -X GET "http://localhost:8000/knowledge-base/agent123/vector-files"
```

### Load Vectors from Storage
```bash
curl -X GET "http://localhost:8000/knowledge-base/agent123/vectors/load"
```

## Configuration

The service requires the following environment variables:

```env
OPENAI_API_KEY=your_openai_api_key
FIREBASE_STORAGE_BUCKET=your_firebase_bucket
GOOGLE_APPLICATION_CREDENTIALS=path/to/firebase-credentials.json
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `.env` file

3. Run the service:
```bash
uvicorn app.main:app --reload --port 8000
```

## File Upload Response

When uploading a file, you'll receive detailed status information:

```json
{
  "id": "file_uuid",
  "filename": "document.pdf",
  "agent_id": "agent123",
  "indexed": true,
  "indexing_status": "complete",
  "indexing_phase": "complete",
  "progress_percent": 100,
  "chunk_count": 25,
  "vector_saved_to_storage": true,
  "vector_storage_path": "vector_exports/agent123/agent_vectors_export_20241101_143022.json"
}
```

## Vector Storage Format

Vector files are stored in JSON format with the following structure:

```json
{
  "export_metadata": {
    "agent_id": "agent123",
    "export_timestamp": "2024-11-01T14:30:22",
    "total_files": 3,
    "total_vectors": 150,
    "export_version": "1.0"
  },
  "files": [...],
  "vectors": {
    "agent_id": "agent123",
    "vector_count": 150,
    "vectors": [...]
  },
  "chunks_metadata": [...]
}
```

This format allows for complete restoration of the knowledge base from storage files.
