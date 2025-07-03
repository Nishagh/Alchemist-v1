#!/usr/bin/env python3
"""
Logging Configuration for Knowledge Base Service

This module provides a centralized logging configuration with custom formatters
and handlers for consistent logging across the Knowledge Base Service.
"""
import os
import logging
import logging.config
from datetime import datetime
import json

# Define log levels and their corresponding emoji prefixes
LOG_LEVEL_EMOJIS = {
    "DEBUG": "🔍",
    "INFO": "ℹ️",
    "WARNING": "⚠️",
    "ERROR": "❌",
    "CRITICAL": "🔥"
}

# Custom log formatter with emojis, colors, and structured data
class CustomFormatter(logging.Formatter):
    """Custom log formatter with emojis and colors for better readability"""
    
    # ANSI escape sequences for colors
    COLORS = {
        "DEBUG": "\033[36m",      # Cyan
        "INFO": "\033[32m",       # Green
        "WARNING": "\033[33m",    # Yellow
        "ERROR": "\033[31m",      # Red
        "CRITICAL": "\033[35m",   # Purple
        "RESET": "\033[0m"        # Reset
    }
    
    def format(self, record):
        # Add timestamp in ISO format
        record.timestamp = datetime.now().isoformat()
        
        # Add emoji prefix based on log level
        levelname = record.levelname
        record.emoji_prefix = LOG_LEVEL_EMOJIS.get(levelname, "")
        
        # Add color codes if terminal supports it
        if os.environ.get("COLORIZE_LOGS", "true").lower() == "true":
            record.levelname_colored = f"{self.COLORS.get(levelname, '')}{levelname}{self.COLORS['RESET']}"
        else:
            record.levelname_colored = levelname
            
        # Extract structured data if present
        if hasattr(record, 'structured_data') and record.structured_data:
            try:
                if isinstance(record.structured_data, dict):
                    record.structured_data_str = json.dumps(record.structured_data)
                else:
                    record.structured_data_str = str(record.structured_data)
            except:
                record.structured_data_str = str(record.structured_data)
        else:
            record.structured_data_str = ""
            
        return super().format(record)

def get_logger(name):
    """Get logger with the specified name and custom configuration"""
    logger = logging.getLogger(name)
    
    # Only configure if not already configured
    if not logger.handlers:
        # Create console handler
        console_handler = logging.StreamHandler()
        
        # Create formatter
        formatter = CustomFormatter(
            "%(emoji_prefix)s [%(timestamp)s] %(levelname_colored)s [%(name)s] %(message)s %(structured_data_str)s"
        )
        
        # Set formatter for handler
        console_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(console_handler)
        
        # Set level from environment or default to INFO
        log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    return logger

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# Helper function to log with structured data
def log_with_data(logger, level, message, data=None):
    """Log a message with structured data"""
    record = logging.LogRecord(
        name=logger.name,
        level=getattr(logging, level),
        pathname="",
        lineno=0,
        msg=message,
        args=(),
        exc_info=None
    )
    
    # Add structured data to the record
    record.structured_data = data
    
    # Find the handler with our custom formatter
    for handler in logger.handlers:
        if isinstance(handler.formatter, CustomFormatter):
            handler.handle(record)
            return
    
    # Fallback if no custom handler found
    getattr(logger, level.lower())(message)
