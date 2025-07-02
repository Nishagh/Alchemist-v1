#!/usr/bin/env python3
"""
Test script to trigger MCP deployment with specific document ID
"""

import os
import sys
from datetime import datetime
from alchemist_shared.database.firebase_client import FirebaseClient
from alchemist_shared.constants.collections import Collections

def test_mcp_deployment(deployment_id: str):
    """Create or update test deployment document to trigger the flow"""
    
    print(f"🧪 Testing MCP deployment flow with ID: {deployment_id}")
    
    # Initialize Firebase
    firebase_client = FirebaseClient()
    db = firebase_client.db
    
    # Check if document already exists
    deployment_ref = db.collection(Collections.MCP_DEPLOYMENTS).document(deployment_id)
    deployment_doc = deployment_ref.get()
    
    if deployment_doc.exists:
        print(f"📄 Document {deployment_id} already exists")
        existing_data = deployment_doc.to_dict()
        print(f"   Status: {existing_data.get('status', 'unknown')}")
        print(f"   Progress: {existing_data.get('progress', 0)}%")
        print(f"   Current Step: {existing_data.get('current_step', 'N/A')}")
        
        # Check if we should retrigger  
        status = existing_data.get('status')
        if status in ['failed', 'completed', 'deployed', 'queued']:
            print(f"🔄 Retriggering deployment by updating document...")
            deployment_ref.update({
                'status': 'pending',
                'progress': 0,
                'current_step': 'Waiting for trigger...',
                'updated_at': datetime.utcnow(),
                'retrigger_count': existing_data.get('retrigger_count', 0) + 1,
                'test_trigger': True
            })
            print("✅ Document updated to retrigger deployment")
        else:
            print(f"⏳ Deployment is currently {status}, no action needed")
    else:
        print(f"📝 Creating new deployment document...")
        
        # Create test deployment document
        deployment_data = {
            'agent_id': 'test-agent-123',  # You can replace with actual agent ID
            'status': 'pending',
            'progress': 0,
            'current_step': 'Initializing deployment...',
            'created_at': datetime.utcnow(),
            'updated_at': datetime.utcnow(),
            'deployment_type': 'mcp_server',
            'test_deployment': True
        }
        
        deployment_ref.set(deployment_data)
        print("✅ Test deployment document created")
    
    print(f"\n🎯 Expected flow:")
    print(f"1. Eventarc detects document creation/update")
    print(f"2. Calls alchemist-tool-forge/trigger-mcp-deployment")
    print(f"3. Service triggers mcp-deployment-job with DEPLOYMENT_ID={deployment_id}")
    print(f"4. Job processes deployment and updates Firestore")
    
    print(f"\n📊 Monitor with:")
    print(f"   Job logs: gcloud logging read 'resource.type=cloud_run_job' --limit=20")
    print(f"   Service logs: gcloud logging read 'resource.type=cloud_run_revision AND resource.labels.service_name=alchemist-tool-forge' --limit=20")

if __name__ == "__main__":
    deployment_id = "auShKJQw0QZU2gP2Ei28"
    test_mcp_deployment(deployment_id)