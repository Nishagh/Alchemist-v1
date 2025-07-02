#!/usr/bin/env python3
"""
Test script to verify Cloud Run Jobs API approach works independently
"""

import os
import logging
from google.cloud import run_v2
from google.cloud.run_v2.types import RunJobRequest

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_cloud_run_api():
    """Test triggering Cloud Run Job via API"""
    try:
        project_id = "alchemist-e69bb"
        region = "us-central1"
        job_name = "mcp-deployment-job"
        test_deployment_id = "test-api-deployment-123"
        
        logger.info(f"Testing Cloud Run Job {job_name} for deployment {test_deployment_id}")
        
        # Use Cloud Run API client
        client = run_v2.JobsClient()
        
        # Build the job resource name
        job_resource_name = f"projects/{project_id}/locations/{region}/jobs/{job_name}"
        logger.info(f"Job resource name: {job_resource_name}")
        
        # Create the request with environment variables
        request = RunJobRequest(
            name=job_resource_name,
            overrides=run_v2.RunJobRequest.Overrides(
                container_overrides=[
                    run_v2.RunJobRequest.Overrides.ContainerOverride(
                        env=[
                            run_v2.EnvVar(name="DEPLOYMENT_ID", value=test_deployment_id)
                        ]
                    )
                ]
            )
        )
        
        logger.info("Sending API request...")
        
        # Execute the job
        operation = client.run_job(request=request)
        
        logger.info(f"SUCCESS: Job execution triggered via API")
        logger.info(f"Operation type: {type(operation)}")
        logger.info(f"Operation dir: {[attr for attr in dir(operation) if not attr.startswith('_')]}")
        
        # Try to get execution info
        if hasattr(operation, 'name'):
            logger.info(f"Operation name: {operation.name}")
        if hasattr(operation, 'metadata'):
            logger.info(f"Operation metadata: {operation.metadata}")
        if hasattr(operation, 'execution'):
            logger.info(f"Execution: {operation.execution}")
            
        return True
        
    except Exception as e:
        logger.error(f"FAILED: Error triggering job via API: {e}")
        logger.error(f"Error type: {type(e)}")
        return False

def test_gcloud_cli():
    """Test gcloud CLI approach for comparison"""
    import subprocess
    
    try:
        project_id = "alchemist-e69bb"
        region = "us-central1"
        job_name = "mcp-deployment-job"
        test_deployment_id = "test-cli-deployment-456"
        
        logger.info(f"Testing gcloud CLI for deployment {test_deployment_id}")
        
        # Set up environment for gcloud
        env = os.environ.copy()
        env.update({
            'CLOUDSDK_CONFIG': '/tmp/.config/gcloud',
            'HOME': '/tmp',
            'TMPDIR': '/tmp'
        })
        
        # Create config directory
        os.makedirs('/tmp/.config/gcloud', exist_ok=True)
        os.makedirs('/tmp/.config/gcloud/logs', exist_ok=True)
        
        job_command = [
            "gcloud", "run", "jobs", "execute", job_name,
            "--region", region,
            "--project", project_id,
            "--update-env-vars", f"DEPLOYMENT_ID={test_deployment_id}",
            "--async",
            "--format", "value(metadata.name)"
        ]
        
        logger.info(f"Running: {' '.join(job_command)}")
        
        process = subprocess.run(
            job_command,
            capture_output=True,
            text=True,
            timeout=30,
            env=env
        )
        
        if process.returncode == 0:
            execution_name = process.stdout.strip()
            logger.info(f"SUCCESS: gcloud CLI triggered job: {execution_name}")
            return True
        else:
            logger.error(f"FAILED: gcloud CLI error: {process.stderr}")
            return False
            
    except Exception as e:
        logger.error(f"FAILED: gcloud CLI exception: {e}")
        return False

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("Testing Cloud Run Job triggering approaches")
    logger.info("=" * 50)
    
    # Test API approach
    logger.info("\n1. Testing Cloud Run API approach:")
    api_success = test_cloud_run_api()
    
    # Test CLI approach
    logger.info("\n2. Testing gcloud CLI approach:")
    cli_success = test_gcloud_cli()
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("RESULTS:")
    logger.info(f"API approach: {'SUCCESS' if api_success else 'FAILED'}")
    logger.info(f"CLI approach: {'SUCCESS' if cli_success else 'FAILED'}")
    logger.info("=" * 50)