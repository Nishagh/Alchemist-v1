"""
Service configuration for monitoring
"""

from typing import List, Dict, Any
from pydantic import BaseModel

class ServiceConfig(BaseModel):
    name: str
    url: str
    health_endpoint: str = "/health"
    timeout: int = 10
    description: str = ""
    service_type: str = "microservice"
    version: str = "1.0.0"
    port: int = 8080
    icon: str = "🔧"

# All Alchemist services to monitor
MONITORED_SERVICES: List[ServiceConfig] = [
    ServiceConfig(
        name="Agent Engine",
        url="https://alchemist-agent-engine-851487020021.us-central1.run.app",
        description="Core orchestration service for the Alchemist AI platform",
        service_type="Core Service",
        icon="🚀"
    ),
    ServiceConfig(
        name="Knowledge Vault",
        url="https://alchemist-knowledge-vault-851487020021.us-central1.run.app",
        description="Document processing and semantic search service",
        service_type="Data Service",
        icon="📚"
    ),
    ServiceConfig(
        name="Agent Bridge",
        url="https://alchemist-agent-bridge-851487020021.us-central1.run.app",
        description="WhatsApp Business integration service",
        service_type="Integration Service",
        icon="🌉"
    ),
    ServiceConfig(
        name="Agent Launcher",
        url="https://alchemist-agent-launcher-851487020021.us-central1.run.app",
        description="Agent deployment automation service",
        service_type="Infrastructure Service",
        icon="🚀"
    ),
    ServiceConfig(
        name="Tool Forge",
        url="https://alchemist-tool-forge-851487020021.us-central1.run.app",
        description="MCP server management and deployment",
        service_type="Management Service",
        icon="🔨"
    ),
    ServiceConfig(
        name="Agent Studio",
        url="https://alchemist-agent-studio-851487020021.us-central1.run.app",
        description="Web application interface for agent management",
        service_type="Frontend Service",
        port=3000,
        icon="🎨"
    ),
    ServiceConfig(
        name="Prompt Engine",
        url="https://alchemist-prompt-engine-851487020021.us-central1.run.app",
        description="AI prompt processing and optimization service",
        service_type="AI Service",
        icon="🧠"
    ),
    ServiceConfig(
        name="Sandbox Console",
        url="https://alchemist-sandbox-console-851487020021.us-central1.run.app",
        description="Interactive testing and development environment",
        service_type="Development Service",
        icon="🧪"
    ),
    ServiceConfig(
        name="MCP Config Generator",
        url="https://alchemist-mcp-config-generator-851487020021.us-central1.run.app",
        description="MCP configuration generation service",
        service_type="Configuration Service",
        icon="⚙️"
    ),
]

# Monitoring configuration
MONITORING_CONFIG = {
    "check_interval_seconds": 30,
    "health_check_timeout": 10,
    "max_retries": 3,
    "retry_delay_seconds": 5,
    "metrics_retention_days": 30,
    "aggregation_intervals": ["1h", "6h", "24h", "7d"],
}