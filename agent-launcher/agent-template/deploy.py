#!/usr/bin/env python3
"""
Deployment script for the Accountable AI Agent
"""

import os
import sys
import asyncio
import logging
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from core.accountable_agent import AccountableAgent
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_agent_deployment(agent_id: str):
    """Test agent deployment with given ID"""
    logger.info(f"Testing deployment for agent ID: {agent_id}")
    
    try:
        # Create and initialize agent
        agent = AccountableAgent(agent_id)
        
        logger.info("Initializing agent...")
        success = await agent.initialize()
        
        if not success:
            logger.error("Agent initialization failed")
            return False
        
        logger.info("Agent initialized successfully")
        
        # Test basic functionality
        logger.info("Testing basic conversation...")
        
        # Create a test conversation
        conversation_id = await agent.create_conversation()
        logger.info(f"Created test conversation: {conversation_id}")
        
        # Send test message
        result = await agent.process_message(
            conversation_id=conversation_id,
            message="Hello! Please introduce yourself and explain your capabilities.",
            user_id="test_user"
        )
        
        if result.success:
            logger.info("✅ Test conversation successful")
            logger.info(f"Response length: {len(result.response)} characters")
            logger.info(f"Token usage: {result.token_usage.total_tokens} tokens")
            logger.info(f"Accountability data keys: {list(result.accountability_data.keys())}")
        else:
            logger.error(f"❌ Test conversation failed: {result.error}")
            return False
        
        # Test agent info
        agent_info = agent.get_agent_info()
        logger.info("✅ Agent info retrieved:")
        logger.info(f"  - Name: {agent_info.get('name')}")
        logger.info(f"  - Model: {agent_info.get('model')}")
        logger.info(f"  - Tools count: {agent_info.get('tools_count')}")
        logger.info(f"  - Accountability enabled: {agent_info.get('accountability_enabled')}")
        
        # Test health check
        health = await agent.health_check()
        logger.info(f"✅ Health check: {health.get('overall_healthy')}")
        
        # Test token usage
        usage = agent.get_token_usage()
        logger.info(f"✅ Token usage: {usage.get('total_tokens')} tokens (${usage.get('estimated_cost'):.4f})")
        
        # Cleanup
        await agent.shutdown()
        logger.info("✅ Agent shutdown completed")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment test failed: {e}")
        return False


async def main():
    """Main deployment test function"""
    # Test with the example agent ID from the user request
    test_agent_id = "9cb4e76c-28bf-45d6-a7c0-e67607675457"
    
    logger.info("🚀 Starting accountable agent deployment test")
    logger.info(f"Agent ID: {test_agent_id}")
    logger.info(f"Environment: {os.getenv('ENVIRONMENT', 'development')}")
    logger.info(f"GNF enabled: {settings.enable_gnf}")
    
    # Run the test
    success = await test_agent_deployment(test_agent_id)
    
    if success:
        logger.info("🎉 Deployment test completed successfully!")
        logger.info("The accountable agent template is ready for use.")
        logger.info("\nTo deploy:")
        logger.info("1. Set environment variables in .env file")
        logger.info("2. Run: python main.py")
        logger.info("3. Or use Docker: docker build -t accountable-agent . && docker run -p 8000:8000 accountable-agent")
        return 0
    else:
        logger.error("💥 Deployment test failed!")
        logger.error("Please check the logs above for error details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)