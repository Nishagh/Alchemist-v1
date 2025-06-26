#!/usr/bin/env python3
"""
Local runner for agent-engine with proper Python path setup
"""
import sys
import os

# Add the shared directory to Python path so alchemist_shared can be imported
shared_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'shared')
sys.path.insert(0, shared_path)

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

# Set working directory to parent so .env.local can be found
parent_dir = os.path.dirname(os.path.dirname(__file__))
os.chdir(parent_dir)

print(f"Working directory: {os.getcwd()}")
print(f"Python path includes: {shared_path}")
print(f"Looking for .env.local at: {os.path.join(parent_dir, '.env.local')}")

# Now import and run the main application
if __name__ == "__main__":
    from agent_engine.main import app
    import uvicorn
    
    # Get configuration
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    print(f"Starting agent-engine locally on {host}:{port}")
    print("Using centralized configuration from alchemist_shared")
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        reload=True,
        log_level="info"
    )