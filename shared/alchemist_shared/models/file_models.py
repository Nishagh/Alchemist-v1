"""
File Data Models

Models for file uploads, processing, and metadata.
"""

from enum import Enum
from typing import Optional, Dict, Any
from pydantic import Field, validator
from .base_models import TimestampedModel


class FileStatus(str, Enum):
    """File processing status."""
    UPLOADED = "uploaded"
    PROCESSING = "processing"
    PROCESSED = "processed"
    FAILED = "failed"
    DELETED = "deleted"


class FileMetadata(TimestampedModel):
    """
    File metadata model.
    
    Contains information about uploaded files and their processing status.
    """
    
    agent_id: str = Field(..., description="ID of the agent this file belongs to")
    user_id: str = Field(..., description="ID of the user who uploaded the file")
    
    # File information
    filename: str = Field(..., description="Original filename")
    content_type: str = Field(..., description="MIME content type")
    file_size: int = Field(..., description="File size in bytes", ge=0)
    file_hash: Optional[str] = Field(default=None, description="File content hash (for deduplication)")
    
    # Storage information
    storage_path: str = Field(..., description="Path to file in storage")
    storage_bucket: Optional[str] = Field(default=None, description="Storage bucket name")
    
    # Processing information
    status: FileStatus = Field(default=FileStatus.UPLOADED, description="Processing status")
    processing_error: Optional[str] = Field(default=None, description="Processing error message")
    
    # Content extraction
    extracted_text: Optional[str] = Field(default=None, description="Extracted text content")
    page_count: Optional[int] = Field(default=None, description="Number of pages (for documents)")
    chunk_count: Optional[int] = Field(default=0, description="Number of text chunks created")
    
    # Metadata
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional file metadata")
    
    @validator("filename")
    def validate_filename(cls, v):
        """Validate filename."""
        if not v or not v.strip():
            raise ValueError("Filename cannot be empty")
        return v.strip()
    
    @validator("file_size")
    def validate_file_size(cls, v):
        """Validate file size."""
        max_size = 50 * 1024 * 1024  # 50MB
        if v > max_size:
            raise ValueError(f"File size exceeds maximum limit of {max_size} bytes")
        return v
    
    @validator("content_type")
    def validate_content_type(cls, v):
        """Validate content type."""
        allowed_types = [
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
            "text/plain",
            "text/html",
            "text/markdown",
        ]
        if v not in allowed_types:
            raise ValueError(f"Content type {v} not allowed")
        return v
    
    def is_processed(self) -> bool:
        """Check if file has been successfully processed."""
        return self.status == FileStatus.PROCESSED
    
    def is_text_file(self) -> bool:
        """Check if file is a text file."""
        return self.content_type.startswith("text/")
    
    def is_pdf(self) -> bool:
        """Check if file is a PDF."""
        return self.content_type == "application/pdf"
    
    def is_word_document(self) -> bool:
        """Check if file is a Word document."""
        return self.content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword"
        ]
    
    def mark_processing(self):
        """Mark file as being processed."""
        self.status = FileStatus.PROCESSING
        self.processing_error = None
        self.update_timestamp()
    
    def mark_processed(self, chunk_count: int = 0):
        """Mark file as successfully processed."""
        self.status = FileStatus.PROCESSED
        self.chunk_count = chunk_count
        self.processing_error = None
        self.update_timestamp()
    
    def mark_failed(self, error_message: str):
        """Mark file processing as failed."""
        self.status = FileStatus.FAILED
        self.processing_error = error_message
        self.update_timestamp()
    
    class Config:
        schema_extra = {
            "example": {
                "agent_id": "agent123",
                "user_id": "user123",
                "filename": "document.pdf",
                "content_type": "application/pdf",
                "file_size": 1024000,
                "storage_path": "files/agent123/document.pdf",
                "status": "processed",
                "chunk_count": 15
            }
        }