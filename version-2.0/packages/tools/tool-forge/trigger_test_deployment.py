#!/usr/bin/env python3
"""
Script to manually trigger a test deployment with specific agent_id and mcp_config_url
"""

import os
import sys
import uuid
from datetime import datetime, timezone

# Import alchemist-shared components
from alchemist_shared.database.firebase_client import FirebaseClient
from firebase_admin.firestore import SERVER_TIMESTAMP
from alchemist_shared.constants.collections import Collections

def create_test_deployment(agent_id: str, mcp_config_url: str):
    """Create a test deployment in Firestore"""
    
    # Initialize Firebase client
    firebase_client = FirebaseClient()
    db = firebase_client.db
    
    # Generate deployment ID
    deployment_id = str(uuid.uuid4())
    
    # First, create or update the agent document with the MCP config
    agent_data = {
        'id': agent_id,
        'name': 'Test Banking Agent',
        'description': 'Test agent for banking API tools',
        'mcp_config': {
            'public_url': mcp_config_url
        },
        'status': 'active',
        'created_at': SERVER_TIMESTAMP,
        'updated_at': SERVER_TIMESTAMP
    }
    
    # Create/update agent document
    agent_ref = db.collection(Collections.AGENTS).document(agent_id)
    agent_ref.set(agent_data, merge=True)
    print(f"Created/updated agent document: {agent_id}")
    
    # Create deployment document
    deployment_data = {
        'agent_id': agent_id,
        'user_id': 'test-user',
        'status': 'queued',
        'progress': 0,
        'current_step': 'Queued for deployment',
        'progress_steps': [
            {
                'step': 'validating',
                'status': 'pending',
                'message': 'Validating configuration...'
            },
            {
                'step': 'building',
                'status': 'pending',
                'message': 'Building MCP server...'
            },
            {
                'step': 'deploying',
                'status': 'pending',
                'message': 'Deploying to cloud...'
            },
            {
                'step': 'testing',
                'status': 'pending',
                'message': 'Testing deployment...'
            }
        ],
        'created_at': SERVER_TIMESTAMP,
        'updated_at': SERVER_TIMESTAMP
    }
    
    # Create deployment document
    deployment_ref = db.collection(Collections.MCP_DEPLOYMENTS).document(deployment_id)
    deployment_ref.set(deployment_data)
    
    print(f"Created deployment document: {deployment_id}")
    print(f"Agent ID: {agent_id}")
    print(f"MCP Config URL: {mcp_config_url}")
    print(f"This should trigger the deployment job automatically via Eventarc")
    
    return deployment_id

if __name__ == "__main__":
    # Configuration
    AGENT_ID = "9cb4e76c-28bf-45d6-a7c0-e67607675457"
    MCP_CONFIG_URL = "https://storage.googleapis.com/alchemist-e69bb.firebasestorage.app/mcp_configs/9cb4e76c-28bf-45d6-a7c0-e67607675457/20250701_121054_mcp_config.yaml"
    
    try:
        deployment_id = create_test_deployment(AGENT_ID, MCP_CONFIG_URL)
        print(f"\nTest deployment created successfully!")
        print(f"Deployment ID: {deployment_id}")
        print(f"Monitor status at: /deployments/{deployment_id}")
        
    except Exception as e:
        print(f"Error creating test deployment: {e}")
        sys.exit(1)