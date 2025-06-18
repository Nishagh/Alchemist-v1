from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from app.services.file_service import FileService
from app.models.file import FileResponse, FileList

router = APIRouter()
file_service = FileService()

@router.post("/upload-knowledge-base", response_model=FileResponse, tags=["knowledge-base"])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_id: str = Form(...)
):
    """
    Upload a file to the knowledge base for a specific agent.
    The file will be stored and indexed for semantic search.
    """
    try:
        # Validate file size (limit to 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Upload file and index in background
        result = await file_service.upload_file(file, agent_id)
        print("File uploaded and indexed successfully", result)

        return FileResponse(
            id=result["id"],
            filename=result["filename"],
            agent_id=result["agent_id"],
            content_type=result["content_type"],
            size=result["size"],
            upload_date=result["upload_date"],
            indexed=result["indexed"],
            purpose=result.get("purpose", "knowledge base"),
            chunk_count=result.get("chunk_count", 0),
            indexing_status=result.get("indexing_status", "pending"),
            indexing_phase=result.get("indexing_phase", None),
            progress_percent=result.get("progress_percent", 0),
            indexing_error=result.get("indexing_error", None),
            last_updated=result.get("last_updated", result["upload_date"])
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/{agent_id}/files", response_model=FileList, tags=["knowledge-base"])
async def list_files(agent_id: str):
    """
    List all files in the knowledge base for a specific agent.
    Response includes detailed information about the indexing status of each file.
    """
    try:
        files = file_service.get_files(agent_id)
        
        # Convert to response model with enhanced indexing status
        file_responses = [
            FileResponse(
                id=file["id"],
                filename=file["filename"],
                agent_id=file["agent_id"],
                content_type=file["content_type"],
                size=file["size"],
                upload_date=file["upload_date"],
                indexed=file["indexed"],
                chunk_count=file.get("chunk_count", 0),
                indexing_status=file.get("indexing_status", "pending"),
                indexing_phase=file.get("indexing_phase", None),
                progress_percent=file.get("progress_percent", 0),
                indexing_error=file.get("indexing_error", None),
                last_updated=file.get("last_updated", file["upload_date"])
            )
            for file in files
        ]
        
        return FileList(files=file_responses)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/knowledge-base/files/{file_id}", tags=["knowledge-base"])
async def delete_file(file_id: str):
    """
    Delete a file and its embeddings from the knowledge base.
    """
    try:
        result = file_service.delete_file(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/files/{file_id}/embeddings", tags=["knowledge-base"])
async def get_file_embeddings(file_id: str):
    """
    Get all embeddings for a specific file.
    This allows users to see what content has been indexed.
    """
    try:
        result = file_service.get_file_embeddings(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/files/{file_id}", response_model=FileResponse, tags=["knowledge-base"])
async def get_file(file_id: str):
    """
    Get file metadata from the knowledge base.
    Response includes detailed information about the indexing status of the file.
    """
    try:
        file = file_service.firebase_service.get_file(file_id)
        
        if not file:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        return FileResponse(
            id=file["id"],
            filename=file["filename"],
            agent_id=file["agent_id"],
            content_type=file["content_type"],
            size=file["size"],
            upload_date=file["upload_date"],
            indexed=file["indexed"],
            chunk_count=file.get("chunk_count", 0),
            indexing_status=file.get("indexing_status", "pending"),
            indexing_phase=file.get("indexing_phase", None),
            progress_percent=file.get("progress_percent", 0),
            indexing_error=file.get("indexing_error", None),
            last_updated=file.get("last_updated", file["upload_date"])
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/{agent_id}/embedding-stats", tags=["knowledge-base"])
async def get_agent_embedding_stats(agent_id: str):
    """
    Get embedding statistics for an agent.
    Shows how many embeddings exist and which files they belong to.
    """
    try:
        result = file_service.get_agent_embedding_stats(agent_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))