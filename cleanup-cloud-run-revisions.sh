#!/bin/bash
# Script to clean up old Cloud Run revisions for all services and jobs in the current project
# Keeps only the current active revision and one backup revision

set -e

# Configuration
REGION="us-central1"
PROJECT_ID=$(gcloud config get-value project)

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}🧹 Cleaning up old Cloud Run revisions for services and jobs${NC}"
echo "Project: ${PROJECT_ID}"
echo "Region: ${REGION}"
echo ""

# Check if required tools are installed
if ! command -v gcloud &> /dev/null; then
    echo -e "${RED}❌ gcloud CLI not found. Please install it first.${NC}"
    exit 1
fi

# Authenticate with Google Cloud
echo -e "${YELLOW}🔐 Checking authentication...${NC}"
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo -e "${YELLOW}🔐 Authenticating with Google Cloud...${NC}"
    gcloud auth login
fi

# Set project
echo -e "${YELLOW}📁 Setting Google Cloud project to: ${PROJECT_ID}${NC}"
gcloud config set project ${PROJECT_ID}

# Function to cleanup services
cleanup_services() {
    echo -e "${BLUE}📋 Getting list of Cloud Run services...${NC}"
    services=$(gcloud run services list --region=${REGION} --format="value(metadata.name)" 2>/dev/null)

    if [ -z "$services" ]; then
        echo -e "${YELLOW}⚠️  No Cloud Run services found in region ${REGION}${NC}"
        return 0
    fi

    total_services=$(echo "$services" | wc -l | xargs)
    echo -e "${BLUE}Found ${total_services} services to process${NC}"
    echo ""

    # Initialize counters
    local processed=0
    local cleaned=0
    local errors=0

    # Process each service
    while IFS= read -r service; do
        if [ -z "$service" ]; then
            continue
        fi
        
        processed=$((processed + 1))
        echo -e "${BLUE}[${processed}/${total_services}] Processing service: ${service}${NC}"
        
        # Get current active revision
        current_revision=$(gcloud run services describe "$service" --region=${REGION} --format="value(status.latestReadyRevisionName)" 2>/dev/null)
        
        if [ -z "$current_revision" ]; then
            echo -e "${YELLOW}⚠️  No active revision found for ${service}${NC}"
            echo ""
            continue
        fi
        
        echo "  Current active revision: ${current_revision}"
        
        # Get all revisions except current
        old_revisions=$(gcloud run revisions list --service="$service" --region=${REGION} --format="value(metadata.name)" 2>/dev/null | grep -v "$current_revision" || true)
        
        if [ -z "$old_revisions" ]; then
            echo -e "${GREEN}  ✅ No old revisions to delete${NC}"
            echo ""
            continue
        fi
        
        revision_count=$(echo "$old_revisions" | wc -l | xargs)
        echo "  Found ${revision_count} old revisions to delete"
        
        # Delete old revisions in batches to avoid timeouts
        deleted_count=0
        failed_count=0
        
        while IFS= read -r revision; do
            if [ -z "$revision" ]; then
                continue
            fi
            
            echo "    Deleting: ${revision}"
            if gcloud run revisions delete "$revision" --region=${REGION} --quiet 2>/dev/null; then
                deleted_count=$((deleted_count + 1))
            else
                echo -e "${YELLOW}    ⚠️  Failed to delete ${revision} (may be actively serving)${NC}"
                failed_count=$((failed_count + 1))
            fi
        done <<< "$old_revisions"
        
        if [ $deleted_count -gt 0 ]; then
            cleaned=$((cleaned + 1))
            echo -e "${GREEN}  ✅ Deleted ${deleted_count} old revisions${NC}"
        fi
        
        if [ $failed_count -gt 0 ]; then
            echo -e "${YELLOW}  ⚠️  ${failed_count} revisions could not be deleted${NC}"
        fi
        
        echo ""
        
    done <<< "$services"
    
    echo -e "${BLUE}📊 Services Summary:${NC}"
    echo "  Services processed: ${processed}"
    echo "  Services cleaned: ${cleaned}"
    echo ""
}

# Function to cleanup jobs
cleanup_jobs() {
    echo -e "${BLUE}📋 Getting list of Cloud Run jobs...${NC}"
    jobs=$(gcloud run jobs list --region=${REGION} --format="value(metadata.name)" 2>/dev/null)

    if [ -z "$jobs" ]; then
        echo -e "${YELLOW}⚠️  No Cloud Run jobs found in region ${REGION}${NC}"
        return 0
    fi

    total_jobs=$(echo "$jobs" | wc -l | xargs)
    echo -e "${BLUE}Found ${total_jobs} jobs to process${NC}"
    echo ""

    # Initialize counters
    local processed=0
    local cleaned=0
    local errors=0

    # Process each job
    while IFS= read -r job; do
        if [ -z "$job" ]; then
            continue
        fi
        
        processed=$((processed + 1))
        echo -e "${BLUE}[${processed}/${total_jobs}] Processing job: ${job}${NC}"
        
        # Get all executions for this job
        executions=$(gcloud run jobs executions list --job="$job" --region=${REGION} --format="value(metadata.name)" 2>/dev/null)
        
        if [ -z "$executions" ]; then
            echo -e "${YELLOW}⚠️  No executions found for job ${job}${NC}"
            echo ""
            continue
        fi
        
        # Keep only the most recent execution, delete the rest
        # Sort executions by creation time (newest first) and skip the first one
        old_executions=$(echo "$executions" | head -n -1)
        
        if [ -z "$old_executions" ]; then
            echo -e "${GREEN}  ✅ No old executions to delete${NC}"
            echo ""
            continue
        fi
        
        execution_count=$(echo "$old_executions" | wc -l | xargs)
        echo "  Found ${execution_count} old executions to delete"
        
        # Delete old executions
        deleted_count=0
        failed_count=0
        
        while IFS= read -r execution; do
            if [ -z "$execution" ]; then
                continue
            fi
            
            echo "    Deleting execution: ${execution}"
            if gcloud run jobs executions delete "$execution" --region=${REGION} --quiet 2>/dev/null; then
                deleted_count=$((deleted_count + 1))
            else
                echo -e "${YELLOW}    ⚠️  Failed to delete ${execution}${NC}"
                failed_count=$((failed_count + 1))
            fi
        done <<< "$old_executions"
        
        if [ $deleted_count -gt 0 ]; then
            cleaned=$((cleaned + 1))
            echo -e "${GREEN}  ✅ Deleted ${deleted_count} old executions${NC}"
        fi
        
        if [ $failed_count -gt 0 ]; then
            echo -e "${YELLOW}  ⚠️  ${failed_count} executions could not be deleted${NC}"
        fi
        
        echo ""
        
    done <<< "$jobs"
    
    echo -e "${BLUE}📊 Jobs Summary:${NC}"
    echo "  Jobs processed: ${processed}"
    echo "  Jobs cleaned: ${cleaned}"
    echo ""
}

# Run cleanup functions
cleanup_services
cleanup_jobs

# Final Summary
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo -e "${BLUE}✅ Cloud Run services and jobs cleanup finished${NC}"
echo ""
echo -e "${BLUE}💡 To run this script again:${NC}"
echo -e "${BLUE}💡 ./cleanup-cloud-run-revisions.sh${NC}"