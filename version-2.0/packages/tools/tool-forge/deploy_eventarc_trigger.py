#!/usr/bin/env python3
"""
Deployment script for Eventarc trigger that connects Firestore to Cloud Function
Creates trigger for mcp_deployments collection document creation
"""

import subprocess
import json
import sys
import os

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"🔨 {description}")
    print(f"Running: {' '.join(command)}")
    
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        if result.stdout:
            print(f"Output: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        print(f"Error: {e.stderr}")
        sys.exit(1)

def get_project_id():
    """Get current Google Cloud project ID"""
    try:
        result = subprocess.run(['gcloud', 'config', 'get-value', 'project'], 
                              capture_output=True, text=True, check=True)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        print("❌ Could not get project ID. Make sure gcloud is configured.")
        sys.exit(1)

def check_prerequisites():
    """Check if required tools are available"""
    tools = ['gcloud', 'python3']
    
    for tool in tools:
        try:
            subprocess.run([tool, '--version'], capture_output=True, check=True)
            print(f"✅ {tool} is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            print(f"❌ {tool} is not available or not working")
            sys.exit(1)

def deploy_cloud_function():
    """Deploy the Cloud Function for MCP deployment trigger"""
    project_id = get_project_id()
    
    # Deploy the Cloud Function
    deploy_command = [
        'gcloud', 'functions', 'deploy', 'trigger-mcp-deployment',
        '--gen2',
        '--runtime', 'python312',
        '--region', 'us-central1',
        '--source', '.',
        '--entry-point', 'trigger_mcp_deployment',
        '--trigger-event-filters', 'type=google.cloud.firestore.document.v1.created',
        '--trigger-event-filters', f'database=(default)',
        '--trigger-event-filters-path-pattern', f'document=mcp_deployments/{{deployment_id}}',
        '--set-env-vars', f'GOOGLE_CLOUD_PROJECT={project_id}',
        '--memory', '512MB',
        '--timeout', '540s',
        '--max-instances', '10',
        '--service-account', f'tool-forge-service@{project_id}.iam.gserviceaccount.com'
    ]
    
    run_command(deploy_command, "Deploying Cloud Function")

def create_eventarc_trigger():
    """Create Eventarc trigger for Firestore document creation"""
    project_id = get_project_id()
    
    # Create Eventarc trigger
    trigger_command = [
        'gcloud', 'eventarc', 'triggers', 'create', 'mcp-deployment-trigger',
        '--location', 'us-central1',
        '--destination-run-service', 'tool-forge',
        '--destination-run-region', 'us-central1',
        '--destination-run-path', '/trigger-mcp-deployment',
        '--event-filters', 'type=google.cloud.firestore.document.v1.created',
        '--event-filters', f'database=(default)',
        '--event-filters-path-pattern', 'document=mcp_deployments/{deployment_id}',
        '--service-account', f'tool-forge-service@{project_id}.iam.gserviceaccount.com'
    ]
    
    try:
        run_command(trigger_command, "Creating Eventarc trigger")
    except SystemExit:
        # Check if trigger already exists
        print("🔍 Checking if trigger already exists...")
        list_command = ['gcloud', 'eventarc', 'triggers', 'list', '--location', 'us-central1', '--format', 'json']
        result = subprocess.run(list_command, capture_output=True, text=True)
        
        if result.returncode == 0:
            triggers = json.loads(result.stdout) if result.stdout else []
            existing_trigger = next((t for t in triggers if t.get('name', '').endswith('/mcp-deployment-trigger')), None)
            
            if existing_trigger:
                print("✅ Trigger already exists, updating...")
                # Update the existing trigger
                update_command = trigger_command.copy()
                update_command[3] = 'update'  # Change 'create' to 'update'
                run_command(update_command, "Updating Eventarc trigger")
            else:
                print("❌ Failed to create trigger and no existing trigger found")
                sys.exit(1)
        else:
            print("❌ Failed to list existing triggers")
            sys.exit(1)

def setup_iam_permissions():
    """Set up IAM permissions for the service account"""
    project_id = get_project_id()
    service_account = f'tool-forge-service@{project_id}.iam.gserviceaccount.com'
    
    # Required roles for Cloud Build integration
    roles = [
        'roles/cloudbuild.builds.editor',
        'roles/run.admin',
        'roles/storage.admin',  # For Cloud Build artifacts
        'roles/firestore.user',
        'roles/eventarc.eventReceiver'
    ]
    
    for role in roles:
        iam_command = [
            'gcloud', 'projects', 'add-iam-policy-binding', project_id,
            '--member', f'serviceAccount:{service_account}',
            '--role', role
        ]
        
        try:
            run_command(iam_command, f"Adding IAM role {role}")
        except SystemExit:
            print(f"⚠️  Role {role} may already be assigned or there was an error")
            continue

def main():
    """Main deployment function"""
    print("🚀 Deploying MCP Deployment Trigger")
    print("=" * 50)
    
    # Check prerequisites
    check_prerequisites()
    
    # Get project info
    project_id = get_project_id()
    print(f"📁 Project ID: {project_id}")
    
    # Verify we're in the right directory
    if not os.path.exists('mcp_deployment_trigger.py'):
        print("❌ Must run from tool-forge directory with mcp_deployment_trigger.py")
        sys.exit(1)
    
    # Set up IAM permissions
    setup_iam_permissions()
    
    # Deploy Cloud Function (if using Cloud Functions approach)
    # deploy_cloud_function()
    
    # Create Eventarc trigger (if using Cloud Run approach)
    create_eventarc_trigger()
    
    print("\n🎉 Deployment completed successfully!")
    print("=" * 50)
    print("📋 Next steps:")
    print("1. Test by creating a document in mcp_deployments collection")
    print("2. Monitor Cloud Function/Run logs for execution")
    print("3. Check Cloud Build console for triggered builds")
    print(f"\n🔍 Monitor with:")
    print(f"gcloud logging read 'resource.type=cloud_function AND resource.labels.function_name=trigger-mcp-deployment' --limit=50")

if __name__ == "__main__":
    main()