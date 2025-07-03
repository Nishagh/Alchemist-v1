from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

class FileBase(BaseModel):
    """Base file model"""
    filename: str
    agent_id: str
    
class FileCreate(FileBase):
    """File creation model"""
    content_type: str
    size: int
    
class FileDB(FileBase):
    """File model as stored in the database"""
    id: str
    content_type: str
    size: int
    upload_date: datetime
    storage_path: str
    indexed: bool = False
    chunk_count: Optional[int] = None
    indexing_status: str = "pending"  # pending, processing, complete, failed
    indexing_phase: Optional[str] = None  # preparing, extracting_text, storing_chunks, complete, failed
    progress_percent: Optional[int] = 0  # 0-100 percentage of completion
    indexing_error: Optional[str] = None
    last_updated: Optional[datetime] = None
    
class FileResponse(FileBase):
    """File response model"""
    id: str
    content_type: str
    size: int
    upload_date: datetime
    indexed: bool
    chunk_count: Optional[int] = None
    indexing_status: str = "pending"  # pending, processing, complete, failed
    indexing_phase: Optional[str] = None  # preparing, extracting_text, storing_chunks, computing_chunk_analysis, complete, failed
    progress_percent: Optional[int] = 0  # 0-100 percentage of completion
    indexing_error: Optional[str] = None
    last_updated: Optional[datetime] = None
    chunk_analysis_available: Optional[bool] = None  # Whether chunk analysis was pre-computed
    
class FileList(BaseModel):
    """List of files response"""
    files: List[FileResponse]
    
class SearchQuery(BaseModel):
    """Search query model"""
    agent_id: str
    query: str
    top_k: int = 5
    
class SearchResult(BaseModel):
    """Individual search result"""
    file_id: str
    filename: str
    content: str
    page_number: Optional[int]
    score: float
    
class SearchResponse(BaseModel):
    """Search response model"""
    results: List[SearchResult]
    query: str

class ContentPreviewResponse(BaseModel):
    """Content preview response model"""
    file_id: str
    filename: str
    content_type: Optional[str] = None
    size: Optional[int] = None
    processing_version: str = "v2_enhanced"
    quality_score: Optional[float] = None
    processing_stats: Optional[Dict[str, Any]] = None
    content_metadata: Optional[Dict[str, Any]] = None
    chunk_count: Optional[int] = None
    original_content: str
    cleaned_content: Optional[str] = None
    relevance_score: Optional[float] = None
    relevance_assessment: Optional[Dict[str, Any]] = None
    agent_specific_quality: Optional[float] = None
    agent_id: Optional[str] = None
