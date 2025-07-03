"""
Base Data Models

Common base models and schemas used across all services.
"""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel as PydanticBaseModel, Field


class BaseModel(PydanticBaseModel):
    """
    Base model with common configuration.
    
    All Alchemist models should inherit from this class.
    """
    
    model_config = {
        # Allow population by field name and alias
        "populate_by_name": True,
        # Generate schema with examples
        "json_schema_extra": {
            "example": {}
        },
        # Validate assignment
        "validate_assignment": True,
        # Use enum values instead of names
        "use_enum_values": True
    }


class TimestampedModel(BaseModel):
    """
    Base model with automatic timestamp fields.
    
    Includes created_at and updated_at fields with automatic population.
    """
    
    id: Optional[str] = Field(default=None, description="Unique identifier")
    created_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    
    def update_timestamp(self):
        """Update the updated_at timestamp."""
        self.updated_at = datetime.utcnow()
    
    def to_firestore(self) -> Dict[str, Any]:
        """Convert model to Firestore-compatible dictionary."""
        data = self.model_dump(exclude_none=True)
        
        # Convert datetime objects to Firestore timestamp format
        if self.created_at:
            data["created_at"] = self.created_at
        if self.updated_at:
            data["updated_at"] = self.updated_at
            
        return data
    
    @classmethod
    def from_firestore(cls, data: Dict[str, Any], doc_id: str = None):
        """Create model instance from Firestore data."""
        if doc_id:
            data["id"] = doc_id
        
        # Handle Firestore timestamp conversion if needed
        for field in ["created_at", "updated_at"]:
            if field in data and hasattr(data[field], "timestamp"):
                data[field] = datetime.fromtimestamp(data[field].timestamp())
        
        return cls(**data)