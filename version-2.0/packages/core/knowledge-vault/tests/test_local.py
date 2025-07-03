#!/usr/bin/env python3
"""
Test script for Knowledge Base Service
This script tests the full workflow of the Knowledge Base Service:
1. Upload a file to an agent
2. List files for the agent
3. Search for content in the uploaded file
4. Delete the file
"""

import os
import sys
import json
import time
import requests
import argparse
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables
load_dotenv()

# Constants
DEFAULT_TEST_FILE = "sample_test.txt"
DEFAULT_AGENT_ID = "test-agent-" + datetime.now().strftime("%Y%m%d%H%M%S")

def create_test_file(file_path, content=None):
    """Create a sample text file for testing"""
    if content is None:
        content = """
        # Knowledge Base Test Document
        
        This is a test document for the Knowledge Base Service.
        
        ## Features
        
        - Semantic search capabilities
        - Automatic indexing
        - Document management
        
        ## Banking Information
        
        The process for opening a new account includes:
        1. Submitting identification documents
        2. Completing the application form
        3. Making an initial deposit
        
        ## FAQ
        
        Q: What are the minimum requirements for opening an account?
        A: You must be at least 18 years old and provide valid identification.
        
        Q: How long does account approval take?
        A: Typically 1-2 business days after all documents are received.
        
        Q: What is the minimum balance requirement?
        A: Standard accounts require a minimum balance of $100 to avoid monthly fees.
        """
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"✅ Created test file: {file_path}")
    return file_path

class KnowledgeBaseServiceTester:
    def __init__(self, base_url, agent_id, test_file):
        self.base_url = base_url
        self.agent_id = agent_id
        self.test_file = test_file
        self.file_id = None
        
        # Check if the service is running
        try:
            response = requests.get(f"{self.base_url}/health")
            if response.status_code != 200:
                print(f"❌ Service is not running at {self.base_url}")
                sys.exit(1)
            print(f"✅ Service is running at {self.base_url}")
        except requests.exceptions.ConnectionError:
            print(f"❌ Cannot connect to service at {self.base_url}")
            sys.exit(1)
    
    def upload_file(self):
        """Test uploading a file"""
        print("\n🔄 Testing file upload...")
        
        # Prepare the multipart form data
        files = {
            'file': open(self.test_file, 'rb'),
        }
        data = {
            'agent_id': self.agent_id,
        }
        
        # Upload the file
        response = requests.post(
            f"{self.base_url}/api/upload-knowledge-base",
            files=files,
            data=data
        )
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            self.file_id = result.get('id')
            print(f"✅ File uploaded successfully. File ID: {self.file_id}")
            print(f"   Filename: {result.get('filename')}")
            print(f"   Size: {result.get('size')} bytes")
            return True
        else:
            print(f"❌ File upload failed. Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def list_files(self):
        """Test listing files for an agent"""
        print("\n🔄 Testing file listing...")
        
        # List files
        response = requests.get(
            f"{self.base_url}/api/knowledge-base/{self.agent_id}/files"
        )
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            files = result.get('files', [])
            print(f"✅ Files listed successfully. Count: {len(files)}")
            
            # Print file details
            for i, file in enumerate(files):
                print(f"   {i+1}. {file.get('filename')} (ID: {file.get('id')})")
                print(f"      Indexed: {file.get('indexed')}, Chunks: {file.get('chunk_count')}")
            
            # Wait for indexing to complete if necessary
            if files and not all(file.get('indexed') for file in files):
                print("⏳ Waiting for indexing to complete...")
                max_attempts = 10
                for attempt in range(max_attempts):
                    # Check if indexing is complete
                    response = requests.get(
                        f"{self.base_url}/api/knowledge-base/{self.agent_id}/files"
                    )
                    if response.status_code == 200:
                        result = response.json()
                        files = result.get('files', [])
                        if all(file.get('indexed') for file in files):
                            print("✅ All files indexed successfully.")
                            break
                    
                    # Wait before checking again
                    time.sleep(3)
                    
                    # Print progress
                    if attempt < max_attempts - 1:
                        print(f"⏳ Still waiting for indexing ({attempt+1}/{max_attempts})...")
            
            return True
        else:
            print(f"❌ File listing failed. Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def search_knowledge_base(self, query="account requirements"):
        """Test searching in the knowledge base"""
        print(f"\n🔄 Testing knowledge base search with query: '{query}'...")
        # Perform search
        payload = {
            "agent_id": self.agent_id,
            "query": query,
            "top_k": 3
        }
        
        response = requests.post(
            f"{self.base_url}/api/search-knowledge-base",
            json=payload
        )
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            results = result.get('results', [])
            print(f"✅ Search completed successfully. Results: {len(results)}")
            
            # Print search results
            for i, item in enumerate(results):
                print(f"\n   Result {i+1} (Score: {item.get('score'):.4f}):")
                print(f"   File: {item.get('filename')}")
                print(f"   Content: {item.get('content')[:150]}...")
            
            return True
        else:
            print(f"❌ Search failed. Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def delete_file(self):
        """Test deleting a file"""
        if not self.file_id:
            print("❌ Cannot delete file: No file ID available")
            return False
        
        print(f"\n🔄 Testing file deletion for file ID: {self.file_id}...")
        
        # Delete the file
        response = requests.delete(
            f"{self.base_url}/api/knowledge-base/files/{self.file_id}"
        )
        
        # Check the response
        if response.status_code == 200:
            result = response.json()
            print(f"✅ File deleted successfully.")
            print(f"   Message: {result.get('message')}")
            return True
        else:
            print(f"❌ File deletion failed. Status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    
    def run_all_tests(self):
        """Run all tests in sequence"""
        print(f"\n🚀 Starting Knowledge Base Service test suite...")
        print(f"📋 Test Configuration:")
        print(f"   Service URL: {self.base_url}")
        print(f"   Agent ID: {self.agent_id}")
        print(f"   Test File: {self.test_file}")
        
        # Run tests
        upload_success = self.upload_file()
        if not upload_success:
            print("❌ Upload test failed. Stopping test suite.")
            return False
        
        list_success = self.list_files()
        if not list_success:
            print("❌ List files test failed. Continuing with other tests...")
        
        search_success = self.search_knowledge_base()
        if not search_success:
            print("❌ Search test failed. Continuing with other tests...")
        
        delete_success = self.delete_file()
        if not delete_success:
            print("❌ Delete test failed.")
            return False
        
        # Final status
        print("\n🏁 Test suite completed.")
        if upload_success and list_success and search_success and delete_success:
            print("✅ All tests passed successfully!")
            return True
        else:
            print("⚠️ Some tests failed. See above for details.")
            return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Test the Knowledge Base Service locally')
    parser.add_argument('--url', default='http://localhost:8080', help='Base URL of the service')
    parser.add_argument('--agent-id', default=DEFAULT_AGENT_ID, help='Agent ID to use for testing')
    parser.add_argument('--file', default=None, help='Test file to upload (will create if not provided)')
    
    args = parser.parse_args()
    
    # Create or use test file
    test_file = args.file
    if not test_file:
        test_file = DEFAULT_TEST_FILE
        create_test_file(test_file)
    elif not os.path.exists(test_file):
        print(f"❌ Test file not found: {test_file}")
        sys.exit(1)
    
    
    # Run tests
    tester = KnowledgeBaseServiceTester(args.url, args.agent_id, test_file)
    success = tester.run_all_tests()
    
    # Clean up test file if we created it
    if args.file is None and os.path.exists(DEFAULT_TEST_FILE):
        os.remove(DEFAULT_TEST_FILE)
        print(f"✅ Removed test file: {DEFAULT_TEST_FILE}")
    
    # Exit with appropriate status code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
