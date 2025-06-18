#!/usr/bin/env python3
"""
Test script for the new vector storage workflow
"""

import requests
import json
import time
import os

# Configuration
BASE_URL = "http://localhost:8000"
AGENT_ID = "test_agent_123"

def test_upload_file():
    """Test file upload with automatic vector storage"""
    print("Testing file upload with vector storage...")
    
    # Create a test file
    test_content = """
    This is a test document for the knowledge base.
    It contains information about machine learning, artificial intelligence, and data science.
    The service should extract text, create embeddings, and save vectors to storage.
    """
    
    with open("test_document.txt", "w") as f:
        f.write(test_content)
    
    # Upload file
    with open("test_document.txt", "rb") as f:
        files = {"file": f}
        data = {"agent_id": AGENT_ID}
        response = requests.post(f"{BASE_URL}/upload-knowledge-base", files=files, data=data)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ File uploaded successfully!")
        print(f"File ID: {result.get('id')}")
        print(f"Indexing Status: {result.get('indexing_status')}")
        print(f"Vector saved to storage: {result.get('vector_saved_to_storage')}")
        print(f"Vector storage path: {result.get('vector_storage_path')}")
        return result.get('id')
    else:
        print(f"❌ Upload failed: {response.status_code} - {response.text}")
        return None

def test_list_files():
    """Test listing files for agent"""
    print("\nTesting file listing...")
    
    response = requests.get(f"{BASE_URL}/knowledge-base/{AGENT_ID}/files")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Files listed successfully!")
        print(f"Number of files: {len(result.get('files', []))}")
        for file in result.get('files', []):
            print(f"  - {file.get('filename')} (ID: {file.get('id')})")
    else:
        print(f"❌ Listing failed: {response.status_code} - {response.text}")

def test_list_vector_files():
    """Test listing vector files for agent"""
    print("\nTesting vector files listing...")
    
    response = requests.get(f"{BASE_URL}/knowledge-base/{AGENT_ID}/vector-files")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Vector files listed successfully!")
        print(f"Total files with vectors: {result.get('total_files_with_vectors')}")
        print(f"Total vector count: {result.get('total_vector_count')}")
        print(f"Latest vector file: {result.get('latest_vector_file', {}).get('vector_storage_path')}")
    else:
        print(f"❌ Vector files listing failed: {response.status_code} - {response.text}")

def test_search_chromadb():
    """Test search using ChromaDB"""
    print("\nTesting ChromaDB search...")
    
    params = {
        "agent_id": AGENT_ID,
        "query": "machine learning",
        "top_k": 3
    }
    
    response = requests.get(f"{BASE_URL}/search-knowledge-base", params=params)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ ChromaDB search successful!")
        print(f"Query: {result.get('query')}")
        print(f"Results found: {len(result.get('results', []))}")
        for i, result_item in enumerate(result.get('results', [])):
            print(f"  {i+1}. {result_item.get('filename')} (Score: {result_item.get('score'):.3f})")
    else:
        print(f"❌ ChromaDB search failed: {response.status_code} - {response.text}")

def test_search_storage():
    """Test search using storage vectors"""
    print("\nTesting storage-based search...")
    
    params = {
        "agent_id": AGENT_ID,
        "query": "artificial intelligence",
        "top_k": 3
    }
    
    response = requests.get(f"{BASE_URL}/search-knowledge-base/storage", params=params)
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Storage search successful!")
        print(f"Query: {result.get('query')}")
        print(f"Results found: {len(result.get('results', []))}")
        for i, result_item in enumerate(result.get('results', [])):
            print(f"  {i+1}. {result_item.get('filename')} (Score: {result_item.get('score'):.3f})")
    else:
        print(f"❌ Storage search failed: {response.status_code} - {response.text}")

def test_load_vectors():
    """Test loading vectors from storage"""
    print("\nTesting vector loading from storage...")
    
    response = requests.get(f"{BASE_URL}/knowledge-base/{AGENT_ID}/vectors/load")
    
    if response.status_code == 200:
        result = response.json()
        print("✅ Vectors loaded successfully!")
        print(f"Status: {result.get('status')}")
        print(f"Total vectors loaded: {result.get('total_vectors')}")
        print(f"Storage path: {result.get('storage_path')}")
    else:
        print(f"❌ Vector loading failed: {response.status_code} - {response.text}")

def cleanup():
    """Clean up test files"""
    if os.path.exists("test_document.txt"):
        os.remove("test_document.txt")

def main():
    """Run all tests"""
    print("🧪 Starting Vector Storage Workflow Tests")
    print("=" * 50)
    
    try:
        # Test the complete workflow
        file_id = test_upload_file()
        
        # Wait a moment for indexing to complete
        time.sleep(2)
        
        test_list_files()
        test_list_vector_files()
        test_search_chromadb()
        test_search_storage()
        test_load_vectors()
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to the service. Make sure it's running on http://localhost:8000")
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
    finally:
        cleanup()

if __name__ == "__main__":
    main() 