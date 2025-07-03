from fastapi import APIRouter, HTTPException, Query
from typing import Dict, Any, List
from pydantic import BaseModel
from services.firebase_service import FirebaseService
from services.openai_service import OpenAIService
import logging
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
firebase_service = FirebaseService()
openai_service = OpenAIService()

class SearchRequest(BaseModel):
    agent_id: str
    query: str
    top_k: int = 5

@router.get("/knowledge-base/{agent_id}/embeddings", tags=["embeddings"])
async def get_agent_embeddings(agent_id: str) -> Dict[str, Any]:
    """
    Get all embeddings for a specific agent from Firestore.
    This endpoint is useful for agent services to access embeddings for search.
    """
    try:
        logger.info(f"Getting embeddings for agent {agent_id}")
        
        # Get embeddings from Firestore
        embeddings = firebase_service.get_embeddings_by_agent(agent_id)
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "embeddings": embeddings,
            "total_embeddings": len(embeddings)
        }
    except Exception as e:
        logger.error(f"Error getting embeddings for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting embeddings: {str(e)}")

@router.get("/knowledge-base/{agent_id}/files", tags=["embeddings", "sync"])
async def get_knowledge_base_files(agent_id: str) -> Dict[str, Any]:
    """
    Get the knowledge base files for an agent.
    Returns files that have been successfully indexed.
    """
    try:
        logger.info(f"Getting knowledge base files for agent {agent_id}")
        
        # Get files from Firebase for this agent
        files = firebase_service.get_files_by_agent(agent_id)
        
        # Filter to only include successfully indexed files
        indexed_files = []
        for file_data in files:
            if file_data.get('indexed', False):
                indexed_files.append({
                    'file_id': file_data.get('id'),
                    'filename': file_data.get('filename', 'unknown'),
                    'status': file_data.get('indexing_status', 'unknown'),
                    'upload_date': file_data.get('upload_date'),
                    'last_updated': file_data.get('last_updated'),
                    'chunk_count': file_data.get('chunk_count', 0),
                    'content_type': file_data.get('content_type')
                })
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "files": indexed_files,
            "total_files": len(indexed_files)
        }
        
    except Exception as e:
        logger.error(f"Error getting knowledge base files for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting files: {str(e)}")

@router.get("/knowledge-base/files/{file_id}/embeddings", tags=["embeddings", "sync"])
async def get_file_embeddings(
    file_id: str, 
    agent_id: str = Query(..., description="Agent ID requesting the embeddings")
) -> Dict[str, Any]:
    """
    Get embeddings for a specific file.
    This endpoint is used by agent services to access file-specific embeddings.
    """
    try:
        logger.info(f"Getting embeddings for file {file_id} requested by agent {agent_id}")
        
        # Get embeddings from Firestore for this specific file
        embeddings = firebase_service.get_embeddings_by_file(agent_id, file_id)
        
        if not embeddings:
            logger.warning(f"No embeddings found for file {file_id}")
            return {
                "status": "success",
                "file_id": file_id,
                "agent_id": agent_id,
                "embeddings": [],
                "total_embeddings": 0
            }
        
        return {
            "status": "success",
            "file_id": file_id,
            "agent_id": agent_id,
            "embeddings": embeddings,
            "total_embeddings": len(embeddings)
        }
        
    except Exception as e:
        logger.error(f"Error getting embeddings for file {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting file embeddings: {str(e)}")

@router.get("/knowledge-base/{agent_id}/embedding-stats", tags=["embeddings"])
async def get_embedding_stats(agent_id: str) -> Dict[str, Any]:
    """
    Get embedding statistics for an agent.
    """
    try:
        logger.info(f"Getting embedding stats for agent {agent_id}")
        
        # Get stats from Firebase
        stats = firebase_service.get_embedding_stats(agent_id)
        
        # Get file count
        files = firebase_service.get_files_by_agent(agent_id)
        indexed_files = [f for f in files if f.get('indexed', False)]
        
        return {
            "status": "success",
            "agent_id": agent_id,
            "embedding_stats": stats,
            "total_files": len(files),
            "indexed_files": len(indexed_files)
        }
        
    except Exception as e:
        logger.error(f"Error getting embedding stats for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error getting embedding stats: {str(e)}")

@router.delete("/knowledge-base/{agent_id}/embeddings", tags=["embeddings"])
async def delete_agent_embeddings(agent_id: str) -> Dict[str, Any]:
    """
    Delete all embeddings for an agent.
    Use with caution - this will remove all indexed content for the agent.
    """
    try:
        logger.info(f"Deleting all embeddings for agent {agent_id}")
        
        # Delete all embeddings for this agent
        deleted_count = firebase_service.delete_all_embeddings_by_agent(agent_id)
        
        return {
            "status": "success",
            "message": f"Deleted {deleted_count} embeddings for agent {agent_id}",
            "agent_id": agent_id,
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Error deleting embeddings for agent {agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error deleting embeddings: {str(e)}")

def cosine_similarity(a, b):
    """Calculate cosine similarity between two vectors"""
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

@router.post("/search-knowledge-base/storage", tags=["search"])
async def search_knowledge_base_storage(request: SearchRequest) -> Dict[str, Any]:
    """
    Search the knowledge base using semantic similarity.
    
    This endpoint performs vector search across the agent's indexed documents
    to find the most relevant content for the given query.
    """
    try:
        logger.info(f"Searching knowledge base for agent {request.agent_id} with query: {request.query}")
        
        # Get query embedding
        query_embedding = openai_service.get_embeddings([request.query])[0]
        
        # Get all embeddings for the agent
        embeddings = firebase_service.get_embeddings_by_agent(request.agent_id)
        
        if not embeddings:
            logger.info(f"No embeddings found for agent {request.agent_id}")
            return {
                "status": "success",
                "results": [],
                "total_results": 0,
                "agent_id": request.agent_id,
                "query": request.query
            }
        
        # Calculate similarities
        results = []
        for embedding_doc in embeddings:
            if 'embedding' not in embedding_doc or not embedding_doc['embedding']:
                continue
                
            # Calculate cosine similarity
            doc_embedding = np.array(embedding_doc['embedding'])
            similarity = cosine_similarity(query_embedding, doc_embedding)
            
            # Create result object
            result = {
                "content": embedding_doc.get('content', ''),
                "filename": embedding_doc.get('filename', ''),
                "file_id": embedding_doc.get('file_id', ''),
                "chunk_index": embedding_doc.get('chunk_index', 0),
                "page_number": embedding_doc.get('page_number', 1),
                "similarity_score": float(similarity),
                "metadata": embedding_doc.get('chunk_metadata', {})
            }
            results.append(result)
        
        # Sort by similarity score (descending)
        results.sort(key=lambda x: x['similarity_score'], reverse=True)
        
        # Return top_k results
        top_results = results[:request.top_k]
        
        logger.info(f"Found {len(results)} total results, returning top {len(top_results)}")
        
        return {
            "status": "success",
            "results": top_results,
            "total_results": len(results),
            "returned_results": len(top_results),
            "agent_id": request.agent_id,
            "query": request.query
        }
        
    except Exception as e:
        logger.error(f"Error searching knowledge base for agent {request.agent_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error searching knowledge base: {str(e)}")