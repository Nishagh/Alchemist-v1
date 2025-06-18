# Alchemist Google Cloud Run Deployment Guide

## 🚀 **Complete Deployment to Google Cloud Run**

This guide will deploy all Alchemist microservices to Google Cloud Run with proper inter-service communication and synchronization.

---

## 📋 **Prerequisites**

### **1. Google Cloud Setup**
```bash
# Install Google Cloud SDK
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Login and set project
gcloud auth login
gcloud config set project YOUR_PROJECT_ID

# Enable required APIs
gcloud services enable run.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable firestore.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### **2. Environment Variables**
```bash
# Set your project configuration
export PROJECT_ID="your-alchemist-project"
export REGION="us-central1"
export ENVIRONMENT="production"

# Update project ID in deployment scripts
sed -i "s/alchemist-e69bb/$PROJECT_ID/g" deployment/scripts/deploy-service.sh
```

### **3. Create Service Account**
```bash
# Create service account for Cloud Run services
gcloud iam service-accounts create alchemist-services \
    --display-name="Alchemist Services Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-services@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/firestore.user"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-services@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:alchemist-services@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

---

## 🔐 **Secret Management**

### **1. Store API Keys in Secret Manager**
```bash
# Store OpenAI API Key
echo -n "your-openai-api-key" | gcloud secrets create openai-api-key --data-file=-

# Store other secrets as needed
echo -n "your-serper-api-key" | gcloud secrets create serper-api-key --data-file=-

# Grant access to service account
gcloud secrets add-iam-policy-binding openai-api-key \
    --member="serviceAccount:alchemist-services@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### **2. Update Service Configurations**
```yaml
# Add to each service's Cloud Run configuration
env:
  - name: OPENAI_API_KEY
    valueFrom:
      secretKeyRef:
        key: openai-api-key
        version: latest
```

---

## 🏗️ **Deployment Strategy**

### **Phase 1: Deploy Core Services**

#### **1. Deploy Agent Engine (Main API)**
```bash
# Deploy the core orchestration service first
./deployment/scripts/deploy-service.sh agent-engine production

# Verify deployment
AGENT_ENGINE_URL=$(gcloud run services describe alchemist-agent-engine \
    --region=$REGION \
    --format="value(status.url)")

curl $AGENT_ENGINE_URL/health
```

#### **2. Deploy Knowledge Vault**
```bash
# Deploy document processing service
./deployment/scripts/deploy-service.sh knowledge-vault production

# Get service URL
KNOWLEDGE_VAULT_URL=$(gcloud run services describe alchemist-knowledge-vault \
    --region=$REGION \
    --format="value(status.url)")
```

#### **3. Deploy Agent Bridge (WhatsApp)**
```bash
# Deploy WhatsApp integration
./deployment/scripts/deploy-service.sh agent-bridge production

# Get service URL
AGENT_BRIDGE_URL=$(gcloud run services describe alchemist-agent-bridge \
    --region=$REGION \
    --format="value(status.url)")
```

### **Phase 2: Deploy Supporting Services**

#### **4. Deploy Agent Launcher**
```bash
# Deploy agent deployment service
./deployment/scripts/deploy-service.sh agent-launcher production

# Get service URL
AGENT_LAUNCHER_URL=$(gcloud run services describe alchemist-agent-launcher \
    --region=$REGION \
    --format="value(status.url)")
```

#### **5. Deploy Tool Forge**
```bash
# Deploy MCP server management
./deployment/scripts/deploy-service.sh tool-forge production

# Get service URL
TOOL_FORGE_URL=$(gcloud run services describe alchemist-tool-forge \
    --region=$REGION \
    --format="value(status.url)")
```

### **Phase 3: Deploy Frontend**

#### **6. Deploy Agent Studio**
```bash
# Update frontend environment variables with service URLs
cat > agent-studio/.env.production << EOF
REACT_APP_ENVIRONMENT=production
REACT_APP_API_BASE_URL=$AGENT_ENGINE_URL
REACT_APP_KNOWLEDGE_BASE_URL=$KNOWLEDGE_VAULT_URL
REACT_APP_WHATSAPP_SERVICE_URL=$AGENT_BRIDGE_URL
REACT_APP_AGENT_DEPLOYMENT_URL=$AGENT_LAUNCHER_URL
REACT_APP_TOOL_FORGE_URL=$TOOL_FORGE_URL
REACT_APP_FIREBASE_PROJECT_ID=$PROJECT_ID
EOF

# Deploy frontend
./deployment/scripts/deploy-service.sh agent-studio production

# Get service URL
AGENT_STUDIO_URL=$(gcloud run services describe alchemist-agent-studio \
    --region=$REGION \
    --format="value(status.url)")
```

---

## 🔄 **Service Synchronization**

### **1. Update Agent Engine with Service URLs**
```bash
# Update Agent Engine environment variables
gcloud run services update alchemist-agent-engine \
    --region=$REGION \
    --set-env-vars="KNOWLEDGE_VAULT_URL=$KNOWLEDGE_VAULT_URL" \
    --set-env-vars="AGENT_BRIDGE_URL=$AGENT_BRIDGE_URL" \
    --set-env-vars="AGENT_LAUNCHER_URL=$AGENT_LAUNCHER_URL" \
    --set-env-vars="TOOL_FORGE_URL=$TOOL_FORGE_URL"
```

### **2. Configure Inter-Service Authentication**
```bash
# Allow services to communicate with each other
for service in alchemist-agent-engine alchemist-knowledge-vault alchemist-agent-bridge alchemist-agent-launcher alchemist-tool-forge; do
    gcloud run services add-iam-policy-binding $service \
        --region=$REGION \
        --member="serviceAccount:alchemist-services@$PROJECT_ID.iam.gserviceaccount.com" \
        --role="roles/run.invoker"
done
```

### **3. Update CORS Settings**
```bash
# Update CORS to allow frontend domain
gcloud run services update alchemist-agent-engine \
    --region=$REGION \
    --set-env-vars="CORS_ORIGINS=$AGENT_STUDIO_URL"

gcloud run services update alchemist-knowledge-vault \
    --region=$REGION \
    --set-env-vars="CORS_ORIGINS=$AGENT_STUDIO_URL"

gcloud run services update alchemist-agent-bridge \
    --region=$REGION \
    --set-env-vars="CORS_ORIGINS=$AGENT_STUDIO_URL"
```

---

## 🌐 **Load Balancer Setup (Optional)**

### **Create Application Load Balancer**
```bash
# Reserve static IP
gcloud compute addresses create alchemist-ip --global

# Create SSL certificate
gcloud compute ssl-certificates create alchemist-ssl \
    --domains=your-domain.com

# Create URL map
gcloud compute url-maps create alchemist-lb \
    --default-service=alchemist-agent-studio

# Add backend services
gcloud compute url-maps add-path-matcher alchemist-lb \
    --path-matcher-name=alchemist-services \
    --default-service=alchemist-agent-studio \
    --path-rules="/api/*=alchemist-agent-engine,/knowledge/*=alchemist-knowledge-vault"

# Create HTTPS proxy
gcloud compute target-https-proxies create alchemist-https-proxy \
    --url-map=alchemist-lb \
    --ssl-certificates=alchemist-ssl

# Create forwarding rule
gcloud compute forwarding-rules create alchemist-https-rule \
    --address=alchemist-ip \
    --global \
    --target-https-proxy=alchemist-https-proxy \
    --ports=443
```

---

## 🚀 **Quick Deployment Script**

### **All-in-One Deployment**
```bash
#!/bin/bash
# deploy-alchemist.sh

set -e

PROJECT_ID=${1:-"your-alchemist-project"}
REGION=${2:-"us-central1"}

echo "🚀 Deploying Alchemist to Google Cloud Run..."
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Update project ID in scripts
sed -i "s/alchemist-e69bb/$PROJECT_ID/g" deployment/scripts/deploy-service.sh

# Deploy services in order
echo "📦 Deploying core services..."
./deployment/scripts/deploy-service.sh agent-engine production
./deployment/scripts/deploy-service.sh knowledge-vault production
./deployment/scripts/deploy-service.sh agent-bridge production

echo "📦 Deploying supporting services..."
./deployment/scripts/deploy-service.sh agent-launcher production
./deployment/scripts/deploy-service.sh tool-forge production

# Get service URLs
echo "🔗 Getting service URLs..."
AGENT_ENGINE_URL=$(gcloud run services describe alchemist-agent-engine --region=$REGION --format="value(status.url)")
KNOWLEDGE_VAULT_URL=$(gcloud run services describe alchemist-knowledge-vault --region=$REGION --format="value(status.url)")
AGENT_BRIDGE_URL=$(gcloud run services describe alchemist-agent-bridge --region=$REGION --format="value(status.url)")
AGENT_LAUNCHER_URL=$(gcloud run services describe alchemist-agent-launcher --region=$REGION --format="value(status.url)")
TOOL_FORGE_URL=$(gcloud run services describe alchemist-tool-forge --region=$REGION --format="value(status.url)")

# Update Agent Engine with service URLs
echo "🔄 Configuring service URLs..."
gcloud run services update alchemist-agent-engine \
    --region=$REGION \
    --set-env-vars="KNOWLEDGE_VAULT_URL=$KNOWLEDGE_VAULT_URL,AGENT_BRIDGE_URL=$AGENT_BRIDGE_URL,AGENT_LAUNCHER_URL=$AGENT_LAUNCHER_URL,TOOL_FORGE_URL=$TOOL_FORGE_URL"

# Create frontend environment file
echo "🎨 Configuring frontend..."
cat > agent-studio/.env.production << EOF
REACT_APP_ENVIRONMENT=production
REACT_APP_API_BASE_URL=$AGENT_ENGINE_URL
REACT_APP_KNOWLEDGE_BASE_URL=$KNOWLEDGE_VAULT_URL
REACT_APP_WHATSAPP_SERVICE_URL=$AGENT_BRIDGE_URL
REACT_APP_AGENT_DEPLOYMENT_URL=$AGENT_LAUNCHER_URL
REACT_APP_TOOL_FORGE_URL=$TOOL_FORGE_URL
REACT_APP_FIREBASE_PROJECT_ID=$PROJECT_ID
EOF

# Deploy frontend
./deployment/scripts/deploy-service.sh agent-studio production

AGENT_STUDIO_URL=$(gcloud run services describe alchemist-agent-studio --region=$REGION --format="value(status.url)")

# Update CORS settings
echo "🌐 Updating CORS settings..."
for service in alchemist-agent-engine alchemist-knowledge-vault alchemist-agent-bridge; do
    gcloud run services update $service \
        --region=$REGION \
        --set-env-vars="CORS_ORIGINS=$AGENT_STUDIO_URL"
done

echo "✅ Alchemist deployment completed!"
echo ""
echo "🌟 Service URLs:"
echo "Agent Engine: $AGENT_ENGINE_URL"
echo "Knowledge Vault: $KNOWLEDGE_VAULT_URL"
echo "Agent Bridge: $AGENT_BRIDGE_URL"
echo "Agent Launcher: $AGENT_LAUNCHER_URL"
echo "Tool Forge: $TOOL_FORGE_URL"
echo "Agent Studio: $AGENT_STUDIO_URL"
echo ""
echo "🧪 Test your deployment:"
echo "curl $AGENT_ENGINE_URL/health"
echo "open $AGENT_STUDIO_URL"
```

---

## 🧪 **Testing Deployment**

### **1. Health Checks**
```bash
# Check all services are healthy
curl $AGENT_ENGINE_URL/health
curl $KNOWLEDGE_VAULT_URL/health  
curl $AGENT_BRIDGE_URL/health
curl $AGENT_LAUNCHER_URL/health
curl $TOOL_FORGE_URL/health
```

### **2. Integration Test**
```bash
# Test agent creation flow
curl -X POST $AGENT_ENGINE_URL/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Agent",
    "domain": "customer_service",
    "model": "gpt-4"
  }'

# Test knowledge base upload
curl -X POST $KNOWLEDGE_VAULT_URL/api/upload \
  -F "file=@test-document.pdf"

# Test WhatsApp integration
curl $AGENT_BRIDGE_URL/api/bsp/accounts/test
```

### **3. Frontend Test**
```bash
# Open Agent Studio
open $AGENT_STUDIO_URL

# Check frontend can reach API
curl $AGENT_STUDIO_URL
```

---

## 📊 **Monitoring & Maintenance**

### **1. Set Up Logging**
```bash
# View logs for a service
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=alchemist-agent-engine" --limit=50

# Set up log-based alerts
gcloud alpha logging sinks create alchemist-errors \
  bigquery.googleapis.com/projects/$PROJECT_ID/datasets/alchemist_logs \
  --log-filter='severity>=ERROR'
```

### **2. Monitor Performance**
```bash
# Check service metrics
gcloud monitoring metrics list --filter="resource.type=cloud_run_revision"

# Set up uptime checks
gcloud compute health-checks create http alchemist-health \
  --request-path=/health \
  --check-interval=30s
```

### **3. Auto-scaling Configuration**
```bash
# Configure auto-scaling for each service
for service in alchemist-agent-engine alchemist-knowledge-vault alchemist-agent-bridge; do
    gcloud run services update $service \
        --region=$REGION \
        --min-instances=1 \
        --max-instances=10 \
        --cpu-utilization=70 \
        --concurrency=80
done
```

---

## 🔄 **Continuous Deployment**

### **Set Up GitHub Actions**
The existing `.github/workflows/ci-cd.yml` is already configured for automatic deployment. Just add these secrets to your GitHub repository:

```bash
# In GitHub repository settings, add these secrets:
GCP_SA_KEY=<your-service-account-key-json>
PROJECT_ID=<your-project-id>
```

---

## 🎯 **Final Verification**

After deployment, verify everything works:

1. **✅ All services respond to health checks**
2. **✅ Frontend can reach all backend services**
3. **✅ Inter-service communication works**
4. **✅ Authentication and authorization work**
5. **✅ File uploads and processing work**
6. **✅ Agent creation and deployment work**

**Your Alchemist platform is now running on Google Cloud Run! 🧙‍♂️✨**