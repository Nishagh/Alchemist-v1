#!/bin/bash
# Script to clean up old Cloud Run revisions for all services in the current project
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

echo -e "${GREEN}🧹 Cleaning up old Cloud Run revisions${NC}"
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

# Get all Cloud Run services
echo -e "${BLUE}📋 Getting list of Cloud Run services...${NC}"
services=$(gcloud run services list --region=${REGION} --format="value(metadata.name)" 2>/dev/null)

if [ -z "$services" ]; then
    echo -e "${YELLOW}⚠️  No Cloud Run services found in region ${REGION}${NC}"
    exit 0
fi

total_services=$(echo "$services" | wc -l | xargs)
echo -e "${BLUE}Found ${total_services} services to process${NC}"
echo ""

# Initialize counters
processed=0
cleaned=0
errors=0

# Process each service
while IFS= read -r service; do
    if [ -z "$service" ]; then
        continue
    fi
    
    processed=$((processed + 1))
    echo -e "${BLUE}[${processed}/${total_services}] Processing: ${service}${NC}"
    
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

# Summary
echo -e "${GREEN}🎉 Cleanup completed!${NC}"
echo -e "${BLUE}📊 Summary:${NC}"
echo "  Services processed: ${processed}"
echo "  Services cleaned: ${cleaned}"
echo "  Services with errors: ${errors}"
echo ""

if [ $cleaned -gt 0 ]; then
    echo -e "${GREEN}✅ Successfully cleaned up old revisions for ${cleaned} services${NC}"
else
    echo -e "${YELLOW}ℹ️  No services required cleanup${NC}"
fi

echo ""
echo -e "${BLUE}💡 To run this script again:${NC}"
echo -e "${BLUE}💡 ./cleanup-cloud-run-revisions.sh${NC}"