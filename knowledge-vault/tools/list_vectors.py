#!/usr/bin/env python3
"""
Vector Index Inspection Tool

This script connects to the Knowledge Base Service API and lists all vector-indexed files
for a given agent. Use this to verify what documents are actually indexed in the service.
"""

import os
import sys
import json
import argparse
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="List vector-indexed files for an agent")
    parser.add_argument("--agent-id", type=str, required=True, 
                        help="Agent ID to list vectors for")
    parser.add_argument("--service-url", type=str, 
                        default=os.environ.get("KNOWLEDGE_BASE_URL", "https://knowledge-base-service-b3hpe34qdq-uc.a.run.app"),
                        help="URL of the Knowledge Base Service")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Display detailed vector metadata")
    return parser.parse_args()

def list_vectors(agent_id, service_url, verbose=False):
    """List all vector-indexed files for an agent"""
    # Build the API URL
    url = f"{service_url}/api/vectors/{agent_id}"
    
    try:
        # Make the API request
        print(f"Connecting to Knowledge Base Service at {service_url}...")
        response = requests.get(url)
        
        # Check for successful response
        if response.status_code != 200:
            print(f"Error: API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
        
        # Parse the response
        data = response.json()
        
        # Print summary
        print(f"\nVector Index Summary for Agent: {agent_id}")
        print(f"Collection Name: {data.get('collection_name', 'unknown')}")
        print(f"Total Vectors: {data.get('vector_count', 0)}")
        
        # Group vectors by file
        files = {}
        for vector in data.get('vectors', []):
            file_id = vector.get('file_id', 'unknown')
            if file_id not in files:
                files[file_id] = []
            files[file_id].append(vector)
        
        # Print file summary
        print(f"\nIndexed Files ({len(files)} total):")
        for file_id, vectors in files.items():
            # Get filename from first vector's metadata if available
            filename = "unknown"
            if vectors and 'metadata' in vectors[0] and 'filename' in vectors[0]['metadata']:
                filename = vectors[0]['metadata']['filename']
            
            print(f"  - {filename} (File ID: {file_id}, Chunks: {len(vectors)})")
            
            # Print detailed vector info if verbose
            if verbose:
                for i, vector in enumerate(vectors):
                    print(f"      Vector {i+1}:")
                    for key, value in vector.get('metadata', {}).items():
                        if key != 'embedding':  # Skip embedding as it's too large
                            print(f"        {key}: {value}")
        
        return True
    
    except requests.exceptions.ConnectionError:
        print(f"Error: Could not connect to Knowledge Base Service at {service_url}")
        return False
    except Exception as e:
        print(f"Error: {str(e)}")
        return False

def main():
    """Main function"""
    # Parse arguments
    # List vectors
    agent_id = "8e749a5b-91a3-4354-afdf-dc1d157e89fd"
    service_url = "https://knowledge-base-service-b3hpe34qdq-uc.a.run.app"
    success = list_vectors(agent_id, service_url, verbose=True)
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
