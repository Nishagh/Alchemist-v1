import os
import json
import uuid
from typing import Dict, List, Any, Union
from datetime import datetime

def generate_unique_id() -> str:
    """Generate a unique ID using UUID4"""
    return str(uuid.uuid4())

def format_datetime(dt: datetime) -> str:
    """Format datetime to ISO format string"""
    return dt.isoformat()

def make_json_safe(obj: Any) -> Any:
    """
    Make an object safe for JSON serialization
    
    This is particularly important for Firestore integration, as it addresses the
    serialization issues mentioned in the project memories about serializing
    agent thought processes.
    """
    if isinstance(obj, dict):
        return {k: make_json_safe(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [make_json_safe(item) for item in obj]
    elif isinstance(obj, datetime):
        return format_datetime(obj)
    elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
        return make_json_safe(obj.to_dict())
    # Handle special Firestore SERVER_TIMESTAMP
    elif str(obj) == "SERVER_TIMESTAMP":
        return "SERVER_TIMESTAMP"
    else:
        return obj
