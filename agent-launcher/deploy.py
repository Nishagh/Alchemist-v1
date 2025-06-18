#!/usr/bin/env python3
"""
Universal Agent Deployment CLI

Simple command-line tool for deploying agents using the universal system.
Usage: python deploy.py <agent_id>
"""

import os
import sys
import logging
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the universal agent directory to the path
sys.path.insert(0, str(Path(__file__).parent / 'universal-agent'))

from agent_deployer import deploy_universal_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main deployment function."""
    if len(sys.argv) != 2:
        print("Usage: python deploy.py <agent_id>")
        print("")
        print("Environment variables required (.env file):")
        print("  PROJECT_ID - Google Cloud Project ID")
        print("  OPENAI_API_KEY - OpenAI API Key")
        print("  GOOGLE_APPLICATION_CREDENTIALS - Path to Firebase credentials JSON (optional)")
        print("  Note: .env file should already be configured with these values")
        sys.exit(1)
    
    agent_id = sys.argv[1]
    
    # Validate environment (check both lowercase and uppercase)
    project_id = os.getenv('PROJECT_ID') or os.getenv('project_id')
    openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('openai_api_key')
    
    missing_env = []
    if not project_id:
        missing_env.append('project_id/PROJECT_ID')
    if not openai_key:
        missing_env.append('openai_api_key/OPENAI_API_KEY')
    
    if missing_env:
        print(f"❌ Missing required environment variables: {', '.join(missing_env)}")
        sys.exit(1)
    
    try:
        print(f"🚀 Starting universal agent deployment for: {agent_id}")
        print(f"📍 Project: {project_id}")
        print(f"🌍 Region: {os.getenv('REGION') or os.getenv('region', 'us-central1')}")
        print("")
        
        result = deploy_universal_agent(agent_id)
        
        print("✅ Deployment successful!")
        print(f"🔗 Service URL: {result['service_url']}")
        print(f"🤖 Agent ID: {result['agent_id']}")
        print(f"🎯 Optimizations applied: {result['optimizations_applied']}")
        print(f"📅 Deployed at: {result['deployed_at']}")
        
    except Exception as e:
        print(f"❌ Deployment failed: {str(e)}")
        logger.error(f"Deployment error: {str(e)}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()