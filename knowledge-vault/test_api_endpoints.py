#!/usr/bin/env python3
"""
Test script for Knowledge Vault API endpoints
This script tests the new content update functionality and existing preview endpoints
"""

import requests
import json
import sys
import time
from typing import Dict, Any

# Configuration
BASE_URL = "http://localhost:8001"  # Knowledge vault service URL
API_PREFIX = "/api"

# Test agent and file IDs (replace with actual values for testing)
TEST_AGENT_ID = "test-agent-123"
TEST_FILE_ID = None  # Will be set when we upload a test file

def make_request(method: str, endpoint: str, **kwargs) -> requests.Response:
    """Make HTTP request with error handling"""
    url = f"{BASE_URL}{API_PREFIX}{endpoint}"
    try:
        response = requests.request(method, url, **kwargs)
        print(f"{method} {endpoint} -> {response.status_code}")
        return response
    except requests.exceptions.RequestException as e:
        print(f"Error making request to {endpoint}: {e}")
        sys.exit(1)

def test_upload_file() -> str:
    """Test file upload and get file ID"""
    print("\n=== Testing File Upload ===")
    
    # Create a test file content
    test_content = """
    # Test Knowledge Base File
    
    This is a test document for the knowledge base system.
    
    ## Features
    - Content editing
    - Reindexing
    - Preview functionality
    
    ## Testing
    This content will be used to test the update and preview endpoints.
    """
    
    # Create multipart form data
    files = {
        'file': ('test_document.txt', test_content, 'text/plain')
    }
    data = {
        'agent_id': TEST_AGENT_ID
    }
    
    response = make_request('POST', '/upload-knowledge-base', files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        file_id = result.get('id')
        print(f"✅ File uploaded successfully. File ID: {file_id}")
        return file_id
    else:
        print(f"❌ Upload failed: {response.text}")
        sys.exit(1)

def test_get_file_preview(file_id: str) -> Dict[str, Any]:
    """Test content preview endpoint"""
    print(f"\n=== Testing Content Preview (File ID: {file_id}) ===")
    
    response = make_request('GET', f'/knowledge-base/files/{file_id}/preview')
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Preview retrieved successfully")
        print(f"   Filename: {result.get('filename')}")
        print(f"   Content Type: {result.get('content_type')}")
        print(f"   Original Content Length: {len(result.get('original_content', ''))}")
        print(f"   Cleaned Content Length: {len(result.get('cleaned_content', ''))}")
        print(f"   Chunk Count: {result.get('chunk_count')}")
        return result
    else:
        print(f"❌ Preview failed: {response.text}")
        return {}

def test_update_content(file_id: str):
    """Test content update endpoint"""
    print(f"\n=== Testing Content Update (File ID: {file_id}) ===")
    
    # New content to update
    updated_content = """
    # Updated Test Knowledge Base File
    
    This document has been UPDATED through the API.
    
    ## New Features Added
    - Real-time content editing
    - Automatic reindexing after updates
    - Enhanced preview with diff highlighting
    - Version tracking
    
    ## Updated Testing Information
    This content has been modified to test the update endpoint functionality.
    The system should automatically reprocess and reindex this content.
    
    ## Additional Content
    - Content change tracking
    - Story event publishing
    - Quality score recalculation
    """
    
    payload = {
        "content": updated_content
    }
    
    response = make_request('PUT', f'/knowledge-base/files/{file_id}/content', 
                           json=payload, headers={'Content-Type': 'application/json'})
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Content updated successfully")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        print(f"   New Content Size: {result.get('new_content_size')} bytes")
        return result
    else:
        print(f"❌ Content update failed: {response.text}")
        return {}

def test_reprocess_file(file_id: str):
    """Test file reprocessing endpoint"""
    print(f"\n=== Testing File Reprocessing (File ID: {file_id}) ===")
    
    response = make_request('POST', f'/knowledge-base/files/{file_id}/reprocess')
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File reprocessing started successfully")
        print(f"   Status: {result.get('status')}")
        print(f"   Message: {result.get('message')}")
        return result
    else:
        print(f"❌ Reprocessing failed: {response.text}")
        return {}

def test_get_processing_status(file_id: str):
    """Test processing status endpoint"""
    print(f"\n=== Testing Processing Status (File ID: {file_id}) ===")
    
    response = make_request('GET', f'/knowledge-base/files/{file_id}/status')
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Processing status retrieved successfully")
        print(f"   Status: {result.get('indexing_status')}")
        print(f"   Phase: {result.get('indexing_phase')}")
        print(f"   Progress: {result.get('progress_percent')}%")
        print(f"   Quality Score: {result.get('quality_score')}")
        return result
    else:
        print(f"❌ Status check failed: {response.text}")
        return {}

def wait_for_processing(file_id: str, max_wait: int = 30):
    """Wait for file processing to complete"""
    print(f"\n=== Waiting for Processing to Complete ===")
    
    for i in range(max_wait):
        status = test_get_processing_status(file_id)
        indexing_status = status.get('indexing_status', 'unknown')
        
        if indexing_status == 'complete':
            print("✅ Processing completed successfully")
            return True
        elif indexing_status == 'failed':
            print(f"❌ Processing failed: {status.get('indexing_error')}")
            return False
        
        print(f"   Waiting... ({i+1}/{max_wait}) Status: {indexing_status}")
        time.sleep(1)
    
    print("⚠️ Processing timeout - continuing with tests")
    return False

def main():
    """Run all API endpoint tests"""
    print("🚀 Starting Knowledge Vault API Endpoint Tests")
    print(f"   Base URL: {BASE_URL}")
    print(f"   Test Agent ID: {TEST_AGENT_ID}")
    
    try:
        # Test 1: Upload a test file
        file_id = test_upload_file()
        global TEST_FILE_ID
        TEST_FILE_ID = file_id
        
        # Wait for initial processing
        wait_for_processing(file_id)
        
        # Test 2: Get initial content preview
        initial_preview = test_get_file_preview(file_id)
        
        # Test 3: Update file content
        update_result = test_update_content(file_id)
        
        # Wait for reprocessing after update
        wait_for_processing(file_id)
        
        # Test 4: Get updated content preview
        updated_preview = test_get_file_preview(file_id)
        
        # Test 5: Test reprocessing endpoint
        reprocess_result = test_reprocess_file(file_id)
        
        # Test 6: Final status check
        final_status = test_get_processing_status(file_id)
        
        print("\n🎉 All API endpoint tests completed!")
        print(f"   Test file ID: {file_id}")
        print("   You can now test the frontend with this file ID")
        
        # Show content comparison
        if initial_preview and updated_preview:
            print(f"\n📊 Content Comparison:")
            print(f"   Initial content length: {len(initial_preview.get('original_content', ''))}")
            print(f"   Updated content length: {len(updated_preview.get('original_content', ''))}")
            print(f"   Initial chunks: {initial_preview.get('chunk_count', 0)}")
            print(f"   Updated chunks: {updated_preview.get('chunk_count', 0)}")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Tests interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()