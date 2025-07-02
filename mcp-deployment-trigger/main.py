"""
Cloud Function to trigger MCP deployment via Cloud Build
Triggered by Eventarc when mcp_deployments document is created
"""

import json
import logging
import os
from typing import Dict, Any

import functions_framework
from google.cloud import build_v1
from google.cloud import firestore
from firebase_admin.firestore import SERVER_TIMESTAMP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize clients
build_client = build_v1.CloudBuildClient()
db = firestore.Client()

PROJECT_ID = os.getenv('GOOGLE_CLOUD_PROJECT')
BUILD_CONFIG_PATH = 'cloudbuild-mcp-deployment.yaml'


@functions_framework.cloud_event
def trigger_mcp_deployment(cloud_event):
    """
    Cloud Function triggered by Firestore document creation in mcp_deployments collection
    Starts Cloud Build job with deployment parameters
    """
    try:
        # Extract event data
        event_data = cloud_event.data
        
        # Get document path from event
        document_path = event_data.get('value', {}).get('name', '')
        logger.info(f"Document path: {document_path}")
        
        # Extract deployment ID from document path
        # Format: projects/PROJECT_ID/databases/(default)/documents/mcp_deployments/DEPLOYMENT_ID
        if '/mcp_deployments/' not in document_path:
            logger.error("Event not from mcp_deployments collection")
            return
        
        deployment_id = document_path.split('/mcp_deployments/')[-1]
        logger.info(f"Processing deployment: {deployment_id}")
        
        # Only process 'create' events
        if event_data.get('value', {}).get('createTime') is None:
            logger.info("Ignoring non-create event")
            return
        
        # Get deployment document data
        deployment_data = _get_deployment_data(deployment_id)
        if not deployment_data:
            logger.error(f"Could not retrieve deployment data for {deployment_id}")
            return
        
        # Get agent configuration
        agent_id = deployment_data.get('agent_id')
        if not agent_id:
            logger.error("No agent_id found in deployment data")
            _update_deployment_status(deployment_id, 'failed', 0, 
                                    'Invalid deployment: missing agent_id')
            return
        
        agent_data = _get_agent_data(agent_id)
        if not agent_data:
            logger.error(f"Could not retrieve agent data for {agent_id}")
            _update_deployment_status(deployment_id, 'failed', 0, 
                                    f'Agent {agent_id} not found')
            return
        
        # Validate agent has MCP config
        if 'mcp_config' not in agent_data or 'public_url' not in agent_data['mcp_config']:
            logger.error(f"Agent {agent_id} missing MCP configuration")
            _update_deployment_status(deployment_id, 'failed', 0, 
                                    'Agent missing MCP configuration')
            return
        
        mcp_config_url = agent_data['mcp_config']['public_url']
        
        # Start Cloud Build
        build_id = _trigger_cloud_build(deployment_id, agent_id, mcp_config_url)
        
        # Update deployment with build information
        _update_deployment_status(
            deployment_id, 
            'processing', 
            5, 
            f'Cloud Build started (ID: {build_id})',
            build_id=build_id
        )
        
        logger.info(f"Successfully triggered Cloud Build {build_id} for deployment {deployment_id}")
        
    except Exception as e:
        logger.error(f"Error processing deployment trigger: {e}")
        # Try to update deployment status if we have deployment_id
        try:
            if 'deployment_id' in locals():
                _update_deployment_status(deployment_id, 'failed', 0, 
                                        f'Trigger failed: {str(e)}')
        except:
            pass


def _get_deployment_data(deployment_id: str) -> Dict[str, Any]:
    """Get deployment document from Firestore"""
    try:
        deployment_ref = db.collection('mcp_deployments').document(deployment_id)
        deployment_doc = deployment_ref.get()
        
        if deployment_doc.exists:
            return deployment_doc.to_dict()
        else:
            logger.error(f"Deployment {deployment_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get deployment data: {e}")
        return None


def _get_agent_data(agent_id: str) -> Dict[str, Any]:
    """Get agent document from Firestore"""
    try:
        agent_ref = db.collection('agents').document(agent_id)
        agent_doc = agent_ref.get()
        
        if agent_doc.exists:
            return agent_doc.to_dict()
        else:
            logger.error(f"Agent {agent_id} not found")
            return None
            
    except Exception as e:
        logger.error(f"Failed to get agent data: {e}")
        return None


def _trigger_cloud_build(deployment_id: str, agent_id: str, mcp_config_url: str) -> str:
    """Trigger Cloud Build with deployment parameters"""
    try:
        # Define the build configuration
        build_config = {
            "source": {
                "repo_source": {
                    "project_id": PROJECT_ID,
                    "repo_name": "github_your-org_alchemist-v1",  # Update with your repo
                    "branch_name": "main"
                }
            },
            "filename": BUILD_CONFIG_PATH,
            "substitutions": {
                "_DEPLOYMENT_ID": deployment_id,
                "_AGENT_ID": agent_id,
                "_MCP_CONFIG_URL": mcp_config_url
            },
            "options": {
                "logging": "CLOUD_LOGGING_ONLY",
                "machine_type": "E2_HIGHCPU_8"
            },
            "timeout": "7200s"  # 2 hours
        }
        
        # Create build request
        request = build_v1.CreateBuildRequest(
            project_id=PROJECT_ID,
            build=build_config
        )
        
        # Submit build
        operation = build_client.create_build(request=request)
        build_id = operation.metadata.build.id
        
        logger.info(f"Cloud Build triggered: {build_id}")
        return build_id
        
    except Exception as e:
        logger.error(f"Failed to trigger Cloud Build: {e}")
        raise


def _update_deployment_status(deployment_id: str, status: str, progress: int, 
                            current_step: str, error_message: str = None, 
                            build_id: str = None):
    """Update deployment status in Firestore"""
    try:
        deployment_ref = db.collection('mcp_deployments').document(deployment_id)
        
        update_data = {
            'status': status,
            'progress': progress,
            'current_step': current_step,
            'updated_at': SERVER_TIMESTAMP
        }
        
        if error_message:
            update_data['error_message'] = error_message
            
        if build_id:
            update_data['build_id'] = build_id
            
        if status in ['deployed', 'failed']:
            update_data['completed_at'] = SERVER_TIMESTAMP
            
        deployment_ref.update(update_data)
        logger.info(f"Updated deployment {deployment_id} status: {status}")
        
    except Exception as e:
        logger.error(f"Failed to update deployment status: {e}")


# For local testing
if __name__ == "__main__":
    # Mock event for testing
    class MockEvent:
        def __init__(self):
            self.data = {
                'value': {
                    'name': f'projects/{PROJECT_ID}/databases/(default)/documents/mcp_deployments/test-deployment-123',
                    'createTime': '2025-01-01T00:00:00Z'
                }
            }
    
    trigger_mcp_deployment(MockEvent())