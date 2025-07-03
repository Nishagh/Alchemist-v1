#!/usr/bin/env python3
"""
Test script to verify MCP URL generation logic.
"""
from agent import get_mcp_server

def test_mcp_url_generation():
    """Test the MCP URL generation for different agent IDs."""
    test_agent_ids = [
        "9cb4e76c-28bf-45d6-a7c0-e67607675457",
        "test-agent-123",
        "banking-agent-456"
    ]
    
    print("Testing MCP URL Generation:")
    print("=" * 50)
    
    for agent_id in test_agent_ids:
        try:
            mcp_url = get_mcp_server(agent_id)
            expected_url = f"https://mcp-{agent_id}-851487020021.us-central1.run.app"
            
            print(f"\nAgent ID: {agent_id}")
            print(f"Generated URL: {mcp_url}")
            print(f"Expected URL:  {expected_url}")
            print(f"Matches: {'✅' if mcp_url == expected_url else '❌'}")
            
        except Exception as e:
            print(f"❌ Error for agent {agent_id}: {e}")

if __name__ == "__main__":
    test_mcp_url_generation()