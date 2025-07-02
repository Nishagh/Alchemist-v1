from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from typing import List, Dict, Any
from pydantic import BaseModel
from services.file_service import FileService
from services.chunk_analysis_service import ChunkAnalysisService
from services.content_processor import ContentProcessor
from services.agent_relevance_service import AgentRelevanceService
from models.file import FileResponse, FileList, ContentPreviewResponse

router = APIRouter()
file_service = FileService()
chunk_analysis_service = ChunkAnalysisService()
content_processor = ContentProcessor()
agent_relevance_service = AgentRelevanceService()

class BatchReprocessRequest(BaseModel):
    file_ids: List[str]

class ContentUpdateRequest(BaseModel):
    content: str

class ContentCleaningRequest(BaseModel):
    enable_cleaning: bool = False
    
class BatchContentCleaningRequest(BaseModel):
    file_ids: List[str]
    enable_cleaning: bool = False

@router.post("/upload-knowledge-base", response_model=FileResponse, tags=["knowledge-base"])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    agent_id: str = Form(...),
    auto_index: bool = Form(False)
):
    """
    Upload a file to the knowledge base for a specific agent.
    
    New workflow:
    - auto_index=False (default): File is uploaded but not indexed. Use /assess-quality and /index endpoints.
    - auto_index=True: File is uploaded and automatically indexed (legacy behavior).
    """
    try:
        # Validate file size (limit to 10MB)
        file_size = 0
        content = await file.read()
        file_size = len(content)
        await file.seek(0)  # Reset file pointer

        if file_size > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(status_code=400, detail="File too large (max 10MB)")

        # Upload file and optionally index
        result = await file_service.upload_file(file, agent_id, auto_index)
        print("File uploaded successfully", result)

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
            last_updated=result.get("last_updated", result["upload_date"]),
            chunk_analysis_available=bool(result.get("chunk_analysis") and not result.get("chunk_analysis", {}).get("error"))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/files/{file_id}/assess-quality", tags=["knowledge-base"])
async def assess_file_quality(file_id: str):
    """
    Assess content quality and relevance for an uploaded file without indexing.
    
    This endpoint provides:
    - Original content quality score and preview
    - Cleaned content quality score and preview  
    - Quality improvement potential
    - Agent-specific relevance assessment
    - Recommendation (clean vs index_as_is)
    """
    try:
        result = await file_service.assess_file_quality(file_id)
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class IndexingRequest(BaseModel):
    enable_cleaning: bool = False

@router.post("/knowledge-base/files/{file_id}/index", tags=["knowledge-base"])
async def index_uploaded_file(file_id: str, request: IndexingRequest):
    """
    Index a previously uploaded file with user-specified cleaning options.
    
    Args:
        file_id: ID of the uploaded file to index
        enable_cleaning: Whether to apply AI-powered content cleaning before indexing
        
    The file must be in 'uploaded' status (not already indexed).
    """
    try:
        result = await file_service.index_file_with_options(file_id, request.enable_cleaning)
        return result
    except HTTPException:
        raise
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
                last_updated=file.get("last_updated", file["upload_date"]),
                chunk_analysis_available=bool(file.get("chunk_analysis") and not file.get("chunk_analysis", {}).get("error"))
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
        result = await file_service.delete_file(file_id)
        return result
    except HTTPException:
        raise
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
            last_updated=file.get("last_updated", file["upload_date"]),
            chunk_analysis_available=bool(file.get("chunk_analysis") and not file.get("chunk_analysis", {}).get("error"))
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

@router.post("/knowledge-base/files/{file_id}/reprocess", tags=["knowledge-base"])
async def reprocess_file(file_id: str):
    """
    Reprocess a file without content cleaning.
    This will delete existing embeddings and recreate them with the original content.
    For content cleaning, use the /clean-and-reindex endpoint instead.
    """
    try:
        result = await file_service.reprocess_file(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/files/{file_id}/clean-and-reindex", tags=["knowledge-base"])
async def clean_and_reindex_file(file_id: str, request: ContentCleaningRequest):
    """
    Clean content and re-index a file with user-controlled content cleaning.
    This allows users to control whether content cleaning is applied during reprocessing.
    
    Args:
        file_id: ID of the file to process
        enable_cleaning: Whether to apply AI-powered content cleaning (default: False)
    
    Returns:
        Processing result with quality scores and metadata
    """
    try:
        result = await file_service.reprocess_file(file_id, enable_cleaning=request.enable_cleaning)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/files/batch-clean-and-reindex", tags=["knowledge-base"])
async def batch_clean_and_reindex_files(request: BatchContentCleaningRequest):
    """
    Clean content and re-index multiple files with user-controlled content cleaning.
    This allows bulk processing with controlled cleaning settings.
    
    Args:
        file_ids: List of file IDs to process
        enable_cleaning: Whether to apply content cleaning to all files (default: False)
    
    Returns:
        Batch processing results with individual file outcomes
    """
    try:
        results = []
        errors = []
        
        for file_id in request.file_ids:
            try:
                result = await file_service.reprocess_file(file_id, enable_cleaning=request.enable_cleaning)
                results.append({"file_id": file_id, "status": "success", "result": result})
            except Exception as e:
                errors.append({"file_id": file_id, "status": "error", "error": str(e)})
        
        return {
            "processed": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors,
            "cleaning_enabled": request.enable_cleaning
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/files/{file_id}/preview-cleaning", tags=["knowledge-base"])
async def preview_content_cleaning(file_id: str, request: ContentCleaningRequest):
    """
    Preview what content cleaning would do to a file without applying changes.
    This allows users to see the difference between original and cleaned content
    before deciding whether to apply cleaning.
    
    Works with both uploaded (unindexed) and indexed files.
    
    Args:
        file_id: ID of the file to preview
        enable_cleaning: Whether to show cleaned version (True) or original (False, default)
    
    Returns:
        Content preview with quality scores and processing statistics
    """
    try:
        # Get file metadata
        file_data = file_service.firebase_service.get_file(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Get file content from storage
        agent_id = file_data.get("agent_id")
        storage_path = file_data.get("storage_path")
        content_type = file_data.get("content_type")
        filename = file_data.get("filename")
        
        # Download file content
        file_content = file_service.firebase_service.download_file_from_storage(storage_path)
        
        # Create temporary file for processing
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(file_content)
            temp_file_path = temp_file.name
        
        try:
            # Extract text
            raw_text = file_service.indexing_service._extract_text(temp_file_path, content_type)
            
            # Process content with user's cleaning preference
            processing_result = content_processor.process_content(
                text=raw_text,
                content_type=content_type,
                filename=filename,
                agent_id=agent_id,
                enable_cleaning=request.enable_cleaning
            )
            
            # Also process without cleaning for comparison
            comparison_result = content_processor.process_content(
                text=raw_text,
                content_type=content_type,
                filename=filename,
                agent_id=agent_id,
                enable_cleaning=not request.enable_cleaning
            )
            
            return {
                "file_id": file_id,
                "filename": filename,
                "content_type": content_type,
                "cleaning_enabled": request.enable_cleaning,
                "preview": {
                    "original_text": raw_text[:2000] + "..." if len(raw_text) > 2000 else raw_text,
                    "processed_text": processing_result["processed_text"][:2000] + "..." if len(processing_result["processed_text"]) > 2000 else processing_result["processed_text"],
                    "quality_score": processing_result["quality_score"],
                    "processing_stats": processing_result["processing_stats"],
                    "relevance_score": processing_result.get("relevance_score"),
                    "agent_specific_quality": processing_result.get("agent_specific_quality")
                },
                "comparison": {
                    "alternative_text": comparison_result["processed_text"][:2000] + "..." if len(comparison_result["processed_text"]) > 2000 else comparison_result["processed_text"],
                    "alternative_quality_score": comparison_result["quality_score"],
                    "alternative_processing_stats": comparison_result["processing_stats"],
                    "alternative_relevance_score": comparison_result.get("relevance_score"),
                    "alternative_agent_specific_quality": comparison_result.get("agent_specific_quality")
                }
            }
            
        finally:
            # Clean up temp file
            import os
            try:
                os.remove(temp_file_path)
            except:
                pass
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/files/{file_id}/status", tags=["knowledge-base"])
async def get_file_processing_status(file_id: str):
    """
    Get detailed processing status for a file.
    Includes progress, quality metrics, and processing statistics.
    """
    try:
        result = file_service.get_processing_status(file_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/{agent_id}/stats", tags=["knowledge-base"])
async def get_agent_processing_stats(agent_id: str):
    """
    Get processing statistics for all files of an agent.
    Includes quality distribution, processing metrics, and content analysis.
    """
    try:
        files = file_service.get_files(agent_id)
        
        # Calculate statistics
        total_files = len(files)
        # All files now use enhanced processing (v2_enhanced)
        
        # Quality metrics
        quality_scores = [f.get("quality_score", 0) for f in files if f.get("quality_score", 0) > 0]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0
        
        # Content reduction metrics
        reduction_percentages = [
            f.get("processing_stats", {}).get("reduction_percentage", 0) 
            for f in files 
            if f.get("processing_stats", {}).get("reduction_percentage", 0) > 0
        ]
        avg_reduction = sum(reduction_percentages) / len(reduction_percentages) if reduction_percentages else 0
        
        # Status distribution
        status_counts = {}
        for file in files:
            status = file.get("indexing_status", "unknown")
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "agent_id": agent_id,
            "total_files": total_files,
            "avg_quality_score": round(avg_quality, 2),
            "avg_content_reduction": round(avg_reduction, 2),
            "status_distribution": status_counts,
            "quality_distribution": {
                "high": len([s for s in quality_scores if s >= 80]),
                "medium": len([s for s in quality_scores if 60 <= s < 80]),
                "low": len([s for s in quality_scores if s < 60])
            },
            "total_chunks": sum(f.get("chunk_count", 0) for f in files)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/files/{file_id}/preview", response_model=ContentPreviewResponse, tags=["knowledge-base"])
async def get_file_content_preview(file_id: str):
    """
    Get file content preview showing original vs processed content.
    Only available for files processed with enhanced pipeline.
    """
    try:
        file_data = file_service.firebase_service.get_file(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        # Get original and processed text directly from file metadata
        original_text = file_data.get("original_text", "")
        processed_text = file_data.get("processed_text", "")
        
        # Get embeddings for chunk count and fallback content
        embeddings_data = file_service.get_file_embeddings(file_id)
        embeddings = embeddings_data.get("embeddings", [])
        
        # Fallback: If full text not available, reconstruct from chunks (for legacy files)
        if not original_text or not processed_text:
            if embeddings:
                # Sort by chunk index if available
                sorted_embeddings = sorted(embeddings, key=lambda x: x.get("chunk_index", 0))
                
                reconstructed_processed = ""
                reconstructed_original = ""
                for embedding in sorted_embeddings:
                    reconstructed_processed += embedding.get("content", "") + "\n\n"
                    reconstructed_original += embedding.get("original_content", "") + "\n\n"
                
                # Use reconstructed text only if direct text not available
                original_text = original_text or reconstructed_original.strip()
                processed_text = processed_text or reconstructed_processed.strip()
        
        # Calculate quality scores for both original and cleaned content
        original_quality = content_processor._calculate_quality_score(original_text) if original_text else 0
        cleaned_quality = content_processor._calculate_quality_score(processed_text) if processed_text else 0
        quality_improvement = cleaned_quality - original_quality
        
        # Enhance processing stats with content comparison data
        processing_stats = file_data.get("processing_stats", {})
        processing_stats.update({
            "original_text": original_text,
            "processed_text": processed_text,
            "original_length": len(original_text),
            "final_length": len(processed_text),
            "original_quality_score": round(original_quality, 2),
            "cleaned_quality_score": round(cleaned_quality, 2),
            "quality_improvement": round(quality_improvement, 2),
            "quality_improvement_percentage": round((quality_improvement / max(original_quality, 1)) * 100, 2)
        })
        
        return ContentPreviewResponse(
            file_id=file_id,
            filename=file_data.get("filename", ""),
            content_type=file_data.get("content_type"),
            size=file_data.get("size"),
            processing_version=file_data.get("processing_version", "v2_enhanced"),
            quality_score=file_data.get("quality_score", 0),
            processing_stats=processing_stats,
            content_metadata=file_data.get("content_metadata", {}),
            chunk_count=len(embeddings),
            original_content=original_text,
            cleaned_content=processed_text,
            relevance_score=file_data.get("relevance_score"),
            relevance_assessment=file_data.get("relevance_assessment"),
            agent_specific_quality=file_data.get("agent_specific_quality"),
            agent_id=file_data.get("agent_id")
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/knowledge-base/files/batch-reprocess", tags=["knowledge-base"])
async def batch_reprocess_files(request: BatchReprocessRequest):
    """
    Reprocess multiple files with enhanced cleaning pipeline.
    """
    try:
        results = []
        errors = []
        
        for file_id in request.file_ids:
            try:
                result = file_service.reprocess_file(file_id)
                results.append({"file_id": file_id, "status": "success", "result": result})
            except Exception as e:
                errors.append({"file_id": file_id, "status": "error", "error": str(e)})
        
        return {
            "processed": len(results),
            "errors": len(errors),
            "results": results,
            "error_details": errors
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/knowledge-base/files/{file_id}/content", tags=["knowledge-base"])
async def update_file_content(file_id: str, request: ContentUpdateRequest):
    """
    Update the content of a file and reindex it.
    This will update the original content and reprocess the file with the new content.
    """
    try:
        result = await file_service.update_file_content(file_id, request.content)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/knowledge-base/files/{file_id}/chunk-analysis", tags=["knowledge-base"])
def get_file_chunk_analysis(file_id: str):
    """
    Get detailed chunk analysis for a specific file.
    
    Returns pre-computed analysis if available (computed during upload),
    otherwise computes analysis on-demand.
    
    Provides comprehensive analysis including:
    - Content distribution metrics (size, word count, sentence count)
    - Quality assessment for each chunk
    - Readability analysis (Flesch-Kincaid grade, reading ease)
    - Overlap analysis between consecutive chunks
    - Semantic similarity analysis using embeddings
    - Content type distribution (code, tables, lists, plain text)
    - Agent relevance analysis
    - Optimization recommendations
    - Detailed chunk-by-chunk information
    
    Response includes 'cached' field indicating if analysis was pre-computed.
    """
    try:
        analysis_result = chunk_analysis_service.analyze_file_chunks(file_id)
        
        if "error" in analysis_result:
            raise HTTPException(status_code=404, detail=analysis_result["error"])
        
        return analysis_result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze chunks: {str(e)}")

@router.get("/knowledge-base/files/{file_id}/relevance-analysis", tags=["knowledge-base"])
def get_file_relevance_analysis(file_id: str):
    """
    Get agent-specific relevance analysis for a file.
    
    Provides comprehensive relevance assessment including:
    - Overall relevance score (0-100) for the agent
    - Domain alignment assessment
    - Purpose relevance evaluation
    - Knowledge value analysis
    - Quality and usefulness metrics
    - Scope appropriateness rating
    - Key topics extraction
    - Detailed relevance explanation
    - Recommendations for improvement
    - Content categorization (high/medium/low relevance)
    
    This analysis helps understand how well the file content aligns with
    the specific agent's purpose, domain, and capabilities.
    """
    try:
        # Get file data
        file_data = file_service.firebase_service.get_file(file_id)
        
        if not file_data:
            raise HTTPException(status_code=404, detail=f"File with ID {file_id} not found")
        
        agent_id = file_data.get("agent_id")
        if not agent_id:
            raise HTTPException(status_code=400, detail="File does not have an associated agent")
        
        # Get processed content (prefer processed over original for analysis)
        content = file_data.get("processed_text") or file_data.get("original_text", "")
        
        if not content.strip():
            # Fallback: reconstruct from embeddings if no full text available
            embeddings_data = file_service.get_file_embeddings(file_id)
            embeddings = embeddings_data.get("embeddings", [])
            
            if embeddings:
                sorted_embeddings = sorted(embeddings, key=lambda x: x.get("chunk_index", 0))
                content = "\n\n".join([emb.get("content", "") for emb in sorted_embeddings])
        
        if not content.strip():
            raise HTTPException(status_code=400, detail="No content available for relevance analysis")
        
        # Perform relevance analysis
        relevance_analysis = agent_relevance_service.assess_content_relevance(
            content=content,
            agent_id=agent_id,
            content_type=file_data.get("content_type"),
            filename=file_data.get("filename")
        )
        
        # Add file context to the result
        analysis_result = {
            "file_id": file_id,
            "filename": file_data.get("filename", ""),
            "agent_id": agent_id,
            "content_type": file_data.get("content_type"),
            "content_length": len(content),
            "analysis": relevance_analysis,
            "file_metadata": {
                "size": file_data.get("size"),
                "upload_date": file_data.get("upload_date"),
                "chunk_count": file_data.get("chunk_count", 0),
                "quality_score": file_data.get("quality_score", 0)
            }
        }
        
        return analysis_result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to analyze relevance: {str(e)}")

# eA³ (Epistemic Autonomy) Agent Story Tracking Endpoints

@router.get("/knowledge-base/{agent_id}/story-coherence", tags=["ea3"])
async def check_agent_story_coherence(agent_id: str):
    """
    Check the narrative coherence of an agent's life-story from knowledge-vault perspective.
    
    This endpoint uses GPT-4.1 enhanced analysis to assess how knowledge acquisition
    events fit into the agent's overall narrative and suggests improvements.
    """
    try:
        # Import eA³ services
        from alchemist_shared.services import get_ea3_orchestrator
        
        ea3_orchestrator = get_ea3_orchestrator()
        if not ea3_orchestrator:
            raise HTTPException(
                status_code=503, 
                detail="eA³ services not available - Spanner Graph may not be initialized"
            )
        
        # Force a comprehensive narrative coherence check
        coherence_result = await ea3_orchestrator.force_narrative_coherence_check(agent_id)
        
        # Add knowledge-vault specific context
        file_count = await file_service._get_agent_file_count(agent_id)
        
        return {
            "agent_id": agent_id,
            "service": "knowledge-vault",
            "knowledge_context": {
                "total_files": file_count,
                "knowledge_integration_score": coherence_result.get("enhanced_coherence_score", 0.5)
            },
            "narrative_coherence": coherence_result,
            "recommendations": {
                "knowledge_specific": [
                    "Ensure new knowledge files align with agent's core objectives",
                    "Monitor for contradictory information in uploaded documents",
                    "Maintain consistent terminology across knowledge sources"
                ]
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check story coherence: {str(e)}")

@router.post("/knowledge-base/{agent_id}/trigger-reflection", tags=["ea3"])
async def trigger_agent_reflection(agent_id: str):
    """
    Trigger autonomous reflection for an agent based on their knowledge acquisition patterns.
    
    This uses GPT-4.1 to analyze how recent knowledge changes should influence
    the agent's worldview and decision-making processes.
    """
    try:
        # Import eA³ services
        from alchemist_shared.services import get_ea3_orchestrator
        
        ea3_orchestrator = get_ea3_orchestrator()
        if not ea3_orchestrator:
            raise HTTPException(
                status_code=503, 
                detail="eA³ services not available - Spanner Graph may not be initialized"
            )
        
        # Get recent knowledge acquisition events
        file_count = await file_service._get_agent_file_count(agent_id)
        
        # Trigger autonomous reflection with knowledge context
        reflection_result = await ea3_orchestrator.trigger_autonomous_reflection(
            agent_id=agent_id,
            context={
                "trigger_source": "knowledge_vault",
                "knowledge_file_count": file_count,
                "reflection_focus": "knowledge_integration"
            }
        )
        
        return {
            "agent_id": agent_id,
            "reflection_triggered": True,
            "service": "knowledge-vault",
            "context": {
                "total_knowledge_files": file_count,
                "focus": "knowledge_integration_and_worldview_update"
            },
            "reflection_result": reflection_result
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger reflection: {str(e)}")

@router.get("/knowledge-base/{agent_id}/ea3-status", tags=["ea3"])
async def get_agent_ea3_status(agent_id: str):
    """
    Get the current eA³ (Epistemic Autonomy, Accountability, Alignment) status
    for an agent from the knowledge-vault perspective.
    """
    try:
        # Import eA³ services
        from alchemist_shared.services import get_ea3_orchestrator
        
        ea3_orchestrator = get_ea3_orchestrator()
        if not ea3_orchestrator:
            return {
                "agent_id": agent_id,
                "ea3_status": "unavailable",
                "message": "eA³ services not initialized",
                "knowledge_context": {
                    "total_files": await file_service._get_agent_file_count(agent_id)
                }
            }
        
        # Get comprehensive eA³ status
        ea3_status = await ea3_orchestrator.get_ea3_assessment(agent_id)
        file_count = await file_service._get_agent_file_count(agent_id)
        
        return {
            "agent_id": agent_id,
            "service": "knowledge-vault",
            "ea3_status": ea3_status,
            "knowledge_context": {
                "total_files": file_count,
                "knowledge_base_health": "healthy" if file_count > 0 else "empty",
                "epistemic_growth_potential": "high" if file_count < 10 else "moderate"
            },
            "narrative_intelligence": {
                "gpt41_enhanced": True,
                "coherence_tracking": "active",
                "story_integration": "automatic"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get eA³ status: {str(e)}")