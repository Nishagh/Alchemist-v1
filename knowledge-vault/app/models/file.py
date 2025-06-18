from typing import Optional, List
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
    indexing_phase: Optional[str] = None  # preparing, extracting_text, storing_chunks, complete, failed
    progress_percent: Optional[int] = 0  # 0-100 percentage of completion
    indexing_error: Optional[str] = None
    last_updated: Optional[datetime] = None
    
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
