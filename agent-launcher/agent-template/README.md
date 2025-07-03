# Accountable AI Agent Template

A comprehensive AI agent template with accountability tracking through Global Narrative Framework (GNF) integration. This template provides a reusable foundation for creating AI agents with advanced narrative coherence monitoring, responsibility assessment, and ethical evaluation.

## Features

### Core Capabilities
- **Alchemist-Shared Integration**: Automatic credential management for Firebase, OpenAI, and other services
- **Direct LLM Integration**: High-performance OpenAI API integration with comprehensive token tracking
- **Conversation Management**: Enhanced conversation handling with memory management
- **Tool Integration**: Extensible tool registry with built-in and external tool support
- **Embedded Knowledge Base**: Local semantic search with OpenAI embeddings and cosine similarity
- **MCP Support**: Model Control Protocol integration for external tool connectivity

### Accountability Framework (GNF Integration)
- **Narrative Identity Tracking**: Monitors agent personality evolution and coherence
- **Story-Loss Calculation**: Detects contradictions in beliefs, facts, goals, and actions
- **Responsibility Assessment**: Evaluates ethical impact and decision quality
- **Development Stages**: Tracks agent progression (nascent → developing → established → mature → evolved)
- **Self-Reflection**: Automatic and manual self-reflection triggers
- **Real-time Monitoring**: Comprehensive alert system for accountability metrics

## Quick Start

### 1. Install Dependencies

Install alchemist-shared for automatic credential management:
```bash
# Install alchemist-shared (required for credentials)
pip install -e ../alchemist-shared

# Install agent dependencies
pip install -r requirements.txt
```

### 2. Environment Setup

Copy the environment template:
```bash
cp .env.example .env
```

Configure your environment variables:
```env
# Agent Configuration
AGENT_ID=your-agent-id-here
DEFAULT_MODEL=gpt-4

# Credentials automatically loaded from alchemist-shared
USE_ALCHEMIST_SHARED=true

# GNF Settings
ENABLE_GNF=true
STORY_LOSS_THRESHOLD=0.7
RESPONSIBILITY_THRESHOLD=0.3

# Note: API keys and Firebase credentials are automatically 
# loaded from alchemist-shared configuration
```

### 3. Run the Agent

```bash
# Direct execution
python main.py

# Or with uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Or test deployment
python deploy.py
```

### 4. Docker Deployment

```bash
# Build image
docker build -t accountable-agent .

# Run container
docker run -p 8000:8000 --env-file .env accountable-agent
```

## API Endpoints

### Core Endpoints
- `GET /` - Health check
- `GET /health` - Comprehensive health status
- `GET /agent/info` - Agent information and capabilities

### Conversation Management
- `POST /conversations` - Create new conversation
- `POST /chat` - Send message to agent
- `GET /conversations/{id}/stats` - Get conversation statistics

### Accountability & Monitoring
- `GET /agent/accountability` - Get accountability summary
- `GET /agent/token-usage` - Get token usage statistics
- `GET /agent/narrative-state` - Get current narrative state
- `POST /agent/reflect` - Trigger manual self-reflection

### Configuration & Tools
- `GET /config` - Get agent configuration
- `GET /agent/tools` - Get available tools

## Configuration

### Agent Configuration
The agent configuration is loaded from Firebase and includes:

```python
{
    "agent_id": "your-agent-id",
    "name": "Agent Name",
    "description": "Agent description",
    "model": "gpt-4",
    "system_prompt": "Your system prompt here",
    "temperature": 0.7,
    "max_tokens": 2048,
    "development_stage": "nascent",
    "accountability_enabled": True,
    "tools_enabled": True,
    "enable_knowledge_base": True,
    "embedding_model": "text-embedding-3-small",
    "mcp_server_url": "optional-mcp-server-url"
}
```

### Accountability Configuration
Fine-tune accountability thresholds in `config/accountability_config.py`:

```python
# Story-loss thresholds
story_loss_warning = 0.7
story_loss_critical = 0.9

# Responsibility thresholds  
responsibility_warning = 0.3
responsibility_critical = 0.1

# Self-reflection settings
enable_automatic_reflection = True
reflection_trigger_conditions = {...}
```

## Usage Examples

### Basic Chat Interaction

```python
import asyncio
from core.accountable_agent import AccountableAgent

async def example_chat():
    # Initialize agent
    agent = AccountableAgent("your-agent-id")
    await agent.initialize()
    
    # Create conversation
    conversation_id = await agent.create_conversation()
    
    # Send message
    result = await agent.process_message(
        conversation_id=conversation_id,
        message="Hello! How can you help me today?",
        user_id="user123"
    )
    
    print(f"Response: {result.response}")
    print(f"Accountability data: {result.accountability_data}")
    
    # Cleanup
    await agent.shutdown()

asyncio.run(example_chat())
```

### Custom Tool Registration

```python
from services.tool_registry import ToolRegistry

# Create custom tool
async def custom_analysis_tool(data: str, analysis_type: str = "basic") -> str:
    # Your custom tool logic here
    return f"Analysis of {data} using {analysis_type} method"

# Register tool
tool_registry = ToolRegistry("agent-id")
tool_registry.register_function_tool(
    name="analyze_data",
    description="Perform custom data analysis",
    parameters={
        "type": "object",
        "properties": {
            "data": {"type": "string", "description": "Data to analyze"},
            "analysis_type": {"type": "string", "enum": ["basic", "advanced"]}
        },
        "required": ["data"]
    },
    function=custom_analysis_tool,
    category="analysis"
)
```

## Architecture

### Core Components
- **AccountableAgent**: Main orchestrator with GNF integration
- **DirectLLMService**: High-performance LLM interface with token tracking
- **EnhancedConversationManager**: Conversation handling with accountability
- **ToolRegistry**: Extensible tool management system
- **FirebaseService**: Firebase integration for persistence

### Accountability Components
- **GNFIntegration**: Global Narrative Framework integration
- **StoryLossCalculator**: Narrative coherence monitoring
- **ResponsibilityAssessor**: Ethical evaluation and responsibility tracking

### Services
- **EmbeddedKnowledgeService**: Local embedding-based semantic search with document chunking
- **MCPService**: Model Control Protocol integration  
- **AgentConfigLoader**: Dynamic configuration management

## Customization for Different Agent IDs

To use this template for different agents, simply:

1. **Update the Agent ID**: Change `AGENT_ID` in your `.env` file
2. **Configure Agent Settings**: Update the agent document in Firebase
3. **Customize System Prompt**: Modify the system prompt for your use case
4. **Add Specific Tools**: Register domain-specific tools as needed
5. **Adjust Accountability Thresholds**: Fine-tune thresholds for your agent's context

Example for a customer service agent:
```env
AGENT_ID=customer-service-agent-001
```

```python
# Custom system prompt for customer service
system_prompt = """
You are a helpful customer service AI agent with advanced accountability tracking.
You maintain narrative coherence in all customer interactions and take responsibility 
for providing accurate, helpful information. You reflect on your responses to ensure
they align with company values and customer satisfaction goals.
"""
```

## Development Stages

The agent progresses through development stages tracked by GNF:

1. **Nascent** (0-100 interactions): Learning basic patterns
2. **Developing** (100-500 interactions): Building core competencies  
3. **Established** (500-2000 interactions): Consistent performance
4. **Mature** (2000-10000 interactions): Advanced capabilities
5. **Evolved** (10000+ interactions): Sophisticated reasoning and reflection

## Monitoring & Alerts

The system provides real-time monitoring with alerts for:
- High story-loss values (narrative inconsistency)
- Low responsibility scores (ethical concerns)
- Degraded coherence (belief system conflicts)
- Performance anomalies
- System health issues

## Testing

Run the deployment test:
```bash
python deploy.py
```

This will test all core functionality including:
- Agent initialization
- Conversation handling
- Accountability tracking
- Tool execution
- Health monitoring

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This template is part of the Alchemist project and follows the project's licensing terms.

## Support

For questions or issues:
1. Check the logs for error details
2. Verify environment configuration
3. Ensure Firebase permissions are correct
4. Test with the provided example agent ID: `9cb4e76c-28bf-45d6-a7c0-e67607675457`

## Advanced Features

### Self-Reflection System
The agent automatically triggers self-reflection when:
- Story-loss exceeds thresholds
- Responsibility scores drop significantly  
- Narrative coherence degrades
- Manual triggers are activated

### Narrative Graph Management
Tracks relationships between:
- Beliefs and facts
- Goals and actions
- Values and decisions
- Past experiences and current behavior

### Dynamic Tool Loading
Supports runtime tool registration from:
- Built-in tool library
- External MCP servers
- Custom function definitions
- Knowledge base integrations

This template provides a complete foundation for building accountable AI agents that maintain narrative coherence and ethical responsibility throughout their development lifecycle.