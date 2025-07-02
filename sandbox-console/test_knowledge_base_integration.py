#!/usr/bin/env python3
"""
Test Knowledge Base Integration for Agent 9cb4e76c-28bf-45d6-a7c0-e67607675457

This script tests the knowledge base file access and search functionality
to ensure the agent can properly access its knowledge files.
"""
import requests
import json
import logging
from typing import Dict, Any, List
from knowledge_service import default_knowledge_client
from knowledge_base_tool import get_knowledge_base_tools

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test agent ID
TEST_AGENT_ID = "9cb4e76c-28bf-45d6-a7c0-e67607675457"
KNOWLEDGE_BASE_URL = "https://alchemist-knowledge-vault-851487020021.us-central1.run.app"

def test_knowledge_base_connectivity():
    """Test basic connectivity to knowledge base service."""
    print("🔗 Testing Knowledge Base Service Connectivity")
    print("=" * 60)
    
    try:
        # Test health endpoint
        response = requests.get(f"{KNOWLEDGE_BASE_URL}/health", timeout=10)
        print(f"Health Check: {response.status_code}")
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Knowledge base service is healthy")
            print(f"   Service: {health_data.get('service', 'Unknown')}")
            print(f"   Status: {health_data.get('status', 'Unknown')}")
            return True
        else:
            print(f"❌ Health check failed with status: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_agent_knowledge_files():
    """Test retrieving knowledge files for the specific agent."""
    print(f"\\n📁 Testing Agent Knowledge Files for {TEST_AGENT_ID}")
    print("=" * 60)
    
    try:
        # Try to get knowledge files for the agent
        response = requests.get(
            f"{KNOWLEDGE_BASE_URL}/api/knowledge-base/{TEST_AGENT_ID}/files",
            timeout=10
        )
        
        print(f"Files API Status: {response.status_code}")
        
        if response.status_code == 200:
            files_data = response.json()
            files = files_data.get('files', [])
            print(f"✅ Found {len(files)} knowledge files for agent")
            
            for i, file_info in enumerate(files[:5]):  # Show first 5 files
                print(f"   {i+1}. {file_info.get('filename', 'Unknown')} ({file_info.get('file_type', 'Unknown type')})")
                print(f"      Size: {file_info.get('file_size_bytes', 0)} bytes")
                print(f"      Status: {file_info.get('status', 'Unknown')}")
            
            if len(files) > 5:
                print(f"   ... and {len(files) - 5} more files")
                
            return files
        else:
            print(f"❌ Files API failed with status: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text[:200]}")
            return []
            
    except Exception as e:
        print(f"❌ Error retrieving knowledge files: {e}")
        return []

def test_knowledge_search():
    """Test knowledge base search functionality."""
    print(f"\\n🔍 Testing Knowledge Base Search for {TEST_AGENT_ID}")
    print("=" * 60)
    
    # Test queries that might be relevant to the agent
    test_queries = [
        "banking services",
        "account information", 
        "customer support",
        "transactions",
        "policies"
    ]
    
    search_results = {}
    
    for query in test_queries:
        print(f"\\nTesting query: '{query}'")
        try:
            results = default_knowledge_client.search(
                agent_id=TEST_AGENT_ID,
                query=query,
                top_k=3
            )
            
            if results:
                print(f"✅ Found {len(results)} results")
                search_results[query] = results
                
                for i, result in enumerate(results):
                    content = result.get('content', result.get('page_content', ''))[:100]
                    score = result.get('score', 0.0)
                    filename = result.get('filename', result.get('source', 'Unknown'))
                    print(f"   {i+1}. Score: {score:.3f} | Source: {filename}")
                    print(f"      Content: {content}...")
            else:
                print(f"❌ No results found for query: '{query}'")
                search_results[query] = []
                
        except Exception as e:
            print(f"❌ Search failed for query '{query}': {e}")
            search_results[query] = []
    
    return search_results

def test_knowledge_base_tools():
    """Test LangChain knowledge base tools integration."""
    print(f"\\n🛠️  Testing Knowledge Base Tools Integration")
    print("=" * 60)
    
    try:
        # Get knowledge base tools for the agent
        kb_tools = get_knowledge_base_tools(agent_id=TEST_AGENT_ID)
        
        print(f"Created {len(kb_tools)} knowledge base tools")
        
        for tool in kb_tools:
            print(f"✅ Tool: {tool.name}")
            print(f"   Description: {tool.description}")
            
            # Test the tool with a sample query
            try:
                print(f"   Testing with query 'banking services'...")
                result = tool.func("banking services")
                
                if result and "Error" not in result:
                    print(f"   ✅ Tool execution successful")
                    print(f"   Result preview: {result[:150]}...")
                else:
                    print(f"   ❌ Tool execution failed or returned error")
                    print(f"   Result: {result[:200] if result else 'No result'}")
                    
            except Exception as e:
                print(f"   ❌ Tool execution error: {e}")
        
        return kb_tools
        
    except Exception as e:
        print(f"❌ Error creating knowledge base tools: {e}")
        return []

def generate_knowledge_base_report(connectivity_ok, files, search_results, tools):
    """Generate a comprehensive report of knowledge base testing."""
    print(f"\\n📊 Knowledge Base Integration Report for Agent {TEST_AGENT_ID}")
    print("=" * 80)
    
    # Connectivity
    print("\\n🔗 CONNECTIVITY:")
    print(f"   Status: {'✅ Connected' if connectivity_ok else '❌ Failed'}")
    
    # Files
    print("\\n📁 KNOWLEDGE FILES:")
    print(f"   Total Files: {len(files)}")
    if files:
        file_types = {}
        total_size = 0
        for file_info in files:
            file_type = file_info.get('file_type', 'Unknown')
            file_types[file_type] = file_types.get(file_type, 0) + 1
            total_size += file_info.get('file_size_bytes', 0)
        
        print(f"   Total Size: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
        print("   File Types:")
        for file_type, count in file_types.items():
            print(f"     {file_type}: {count} files")
    else:
        print("   ❌ No files found or access failed")
    
    # Search
    print("\\n🔍 SEARCH FUNCTIONALITY:")
    successful_searches = sum(1 for results in search_results.values() if results)
    total_searches = len(search_results)
    print(f"   Successful Searches: {successful_searches}/{total_searches}")
    
    if successful_searches > 0:
        for query, results in search_results.items():
            if results:
                avg_score = sum(r.get('score', 0) for r in results) / len(results)
                print(f"   '{query}': {len(results)} results (avg score: {avg_score:.3f})")
    
    # Tools
    print("\\n🛠️  LANGCHAIN INTEGRATION:")
    print(f"   Tools Created: {len(tools)}")
    print(f"   Status: {'✅ Ready for agent use' if tools else '❌ No tools available'}")
    
    # Overall Assessment
    print("\\n🎯 OVERALL ASSESSMENT:")
    score = 0
    max_score = 4
    
    if connectivity_ok:
        score += 1
        print("   ✅ Service connectivity working")
    else:
        print("   ❌ Service connectivity issues")
    
    if files:
        score += 1
        print("   ✅ Knowledge files accessible")
    else:
        print("   ❌ No knowledge files found")
    
    if successful_searches > 0:
        score += 1
        print("   ✅ Search functionality working")
    else:
        print("   ❌ Search functionality not working")
    
    if tools:
        score += 1
        print("   ✅ LangChain tools integration ready")
    else:
        print("   ❌ LangChain tools integration failed")
    
    print(f"\\n   SCORE: {score}/{max_score} ({score/max_score*100:.0f}%)")
    
    if score == max_score:
        print("   🎉 EXCELLENT: Knowledge base fully operational!")
    elif score >= 3:
        print("   ✅ GOOD: Knowledge base mostly working with minor issues")
    elif score >= 2:
        print("   ⚠️  PARTIAL: Knowledge base partially working, needs attention")
    else:
        print("   ❌ CRITICAL: Knowledge base not functioning properly")

def main():
    """Run all knowledge base tests."""
    print(f"🧪 Testing Knowledge Base Integration for Agent: {TEST_AGENT_ID}")
    print("=" * 80)
    
    # Run tests
    connectivity_ok = test_knowledge_base_connectivity()
    files = test_agent_knowledge_files()
    search_results = test_knowledge_search()
    tools = test_knowledge_base_tools()
    
    # Generate report
    generate_knowledge_base_report(connectivity_ok, files, search_results, tools)

if __name__ == "__main__":
    main()