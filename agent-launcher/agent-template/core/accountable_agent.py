"""
Accountable AI Agent - Main orchestrator with GNF integration
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone

from core.llm_service import DirectLLMService
from core.conversation_manager import EnhancedConversationManager, ConversationResult
from services.firebase_service import firebase_service
from services.knowledge_service import KnowledgeService
from services.mcp_service import MCPService
from services.tool_registry import ToolRegistry
from config.agent_config import agent_config_loader
from config.settings import settings
from config.accountability_config import accountability_config

logger = logging.getLogger(__name__)


class AccountableAgent:
    """
    Main accountable AI agent with comprehensive GNF integration
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.agent_config: Dict[str, Any] = {}
        self.initialized = False
        
        # Core components
        self.llm_service: Optional[DirectLLMService] = None
        self.conversation_manager: Optional[EnhancedConversationManager] = None
        self.knowledge_service: Optional[KnowledgeService] = None
        self.mcp_service: Optional[MCPService] = None
        self.tool_registry: Optional[ToolRegistry] = None
        
        logger.info(f"AccountableAgent created for agent ID: {agent_id}")
    
    async def initialize(self) -> bool:
        """
        Initialize the accountable agent with full configuration
        
        Returns:
            True if initialization successful, False otherwise
        """
        try:
            logger.info(f"Initializing accountable agent: {self.agent_id}")
            
            # Load agent configuration
            self.agent_config = await agent_config_loader.load_agent_config(self.agent_id)
            
            # Validate configuration
            if not await agent_config_loader.validate_agent_config(self.agent_config):
                raise ValueError("Agent configuration validation failed")
            
            # Initialize core LLM service
            await self._initialize_llm_service()
            
            # Initialize tool registry
            await self._initialize_tool_registry()
            
            # Initialize knowledge service if enabled
            if settings.enable_knowledge_base:
                await self._initialize_knowledge_service()
            
            # Initialize MCP service if enabled
            if self.agent_config.get('mcp_server_url'):
                await self._initialize_mcp_service()
            
            # Initialize conversation manager with accountability
            await self._initialize_conversation_manager()
            
            # Perform health checks
            await self._perform_health_checks()
            
            self.initialized = True
            logger.info(f"Agent {self.agent_id} initialized successfully")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize agent {self.agent_id}: {e}")
            return False
    
    async def _initialize_llm_service(self):
        """Initialize the LLM service"""
        try:
            model = self.agent_config.get('model', settings.default_model)
            
            # Try to get API key from alchemist-shared first
            api_key = settings.get_openai_api_key()
            if not api_key:
                # Fallback to agent config
                api_key = self.agent_config.get('openai_api_key')
            
            if not api_key:
                raise ValueError("OpenAI API key not found in alchemist-shared or agent config")
            
            self.llm_service = DirectLLMService(api_key=api_key, model=model)
            
            # Verify LLM service health
            if not await self.llm_service.health_check():
                raise ValueError("LLM service health check failed")
            
            logger.info(f"LLM service initialized with model: {model}")
            
        except Exception as e:
            logger.error(f"Failed to initialize LLM service: {e}")
            raise
    
    async def _initialize_tool_registry(self):
        """Initialize the tool registry"""
        try:
            self.tool_registry = ToolRegistry(agent_id=self.agent_id)
            logger.info("Tool registry initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize tool registry: {e}")
            raise
    
    async def _initialize_knowledge_service(self):
        """Initialize embedded knowledge service"""
        try:
            self.knowledge_service = KnowledgeService(agent_id=self.agent_id)
            
            # Initialize the service
            await self.knowledge_service.initialize()
            
            # Register knowledge tools
            await self.knowledge_service.register_tools(self.tool_registry)
            
            logger.info(f"Embedded knowledge service initialized for agent {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to initialize knowledge service: {e}")
            # Don't raise - knowledge service is optional
    
    async def _initialize_mcp_service(self):
        """Initialize MCP service"""
        try:
            # Fetch MCP server URL from Firestore mcp_servers collection
            from services.firebase_service import firebase_service
            mcp_servers = await firebase_service.get_documents(f'mcp_servers')
            mcp_server_doc = None
            
            # Find the document for this agent
            for doc in mcp_servers or []:
                if doc.get('agent_id') == self.agent_id:
                    mcp_server_doc = doc
                    break
            
            if mcp_server_doc and mcp_server_doc.get('service_url'):
                mcp_server_url = mcp_server_doc.get('service_url')
                self.mcp_service = MCPService(
                    agent_id=self.agent_id,
                    mcp_server_url=mcp_server_url
                )
                
                # Register MCP tools
                await self.mcp_service.register_tools(self.tool_registry)
                
                logger.info(f"MCP service initialized: {mcp_server_url}")
            
        except Exception as e:
            logger.error(f"Failed to initialize MCP service: {e}")
            # Don't raise - MCP service is optional
    
    async def _initialize_conversation_manager(self):
        """Initialize the enhanced conversation manager"""
        try:
            if not self.llm_service:
                raise ValueError("LLM service must be initialized first")
            
            self.conversation_manager = EnhancedConversationManager(
                agent_id=self.agent_id,
                llm_service=self.llm_service,
                agent_config=self.agent_config
            )
            
            await self.conversation_manager.initialize()
            
            logger.info("Conversation manager initialized with accountability tracking")
            
        except Exception as e:
            logger.error(f"Failed to initialize conversation manager: {e}")
            raise
    
    async def _perform_health_checks(self):
        """Perform health checks on all components"""
        try:
            # LLM service health check
            if not await self.llm_service.health_check():
                logger.warning("LLM service health check failed")
            
            # Knowledge service health check
            if self.knowledge_service and not await self.knowledge_service.health_check():
                logger.warning("Knowledge service health check failed")
            
            # MCP service health check  
            if self.mcp_service and not await self.mcp_service.health_check():
                logger.warning("MCP service health check failed")
            
            logger.info("Health checks completed")
            
        except Exception as e:
            logger.error(f"Health checks failed: {e}")
    
    async def process_message(self, conversation_id: str, message: str,
                            user_id: Optional[str] = None) -> ConversationResult:
        """
        Process a user message with full accountability tracking
        
        Args:
            conversation_id: The conversation identifier
            message: User's message  
            user_id: Optional user identifier
            
        Returns:
            ConversationResult with response and accountability data
        """
        if not self.initialized:
            raise RuntimeError("Agent not initialized")
        
        try:
            # Get available tools
            tools = await self._get_available_tools()
            
            # Process message through conversation manager
            result = await self.conversation_manager.process_message(
                conversation_id=conversation_id,
                message=message,
                user_id=user_id,
                tools=tools
            )
            
            # Check for self-reflection triggers
            if result.success and result.accountability_data:
                await self._check_self_reflection_triggers(result.accountability_data)
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return ConversationResult(
                success=False,
                response="I apologize, but I encountered an error processing your message.",
                conversation_id=conversation_id,
                token_usage=self.llm_service.get_token_usage() if self.llm_service else None,
                accountability_data={},
                error=str(e)
            )
    
    async def stream_response(self, conversation_id: str, message: str,
                            user_id: Optional[str] = None):
        """
        Stream response with accountability tracking
        
        Args:
            conversation_id: The conversation identifier
            message: User's message
            user_id: Optional user identifier
            
        Yields:
            Response chunks as they arrive
        """
        if not self.initialized:
            raise RuntimeError("Agent not initialized")
        
        async for chunk in self.conversation_manager.stream_response(
            conversation_id=conversation_id,
            message=message,
            user_id=user_id
        ):
            yield chunk
    
    async def _get_available_tools(self) -> List[Dict[str, Any]]:
        """Get all available tools for the agent"""
        if not self.tool_registry:
            return []
        
        try:
            tools = await self.tool_registry.get_all_tools()
            logger.debug(f"Retrieved {len(tools)} available tools")
            return tools
            
        except Exception as e:
            logger.error(f"Failed to get available tools: {e}")
            return []
    
    async def _check_self_reflection_triggers(self, accountability_data: Dict[str, Any]):
        """Check if self-reflection should be triggered"""
        try:
            if not settings.enable_gnf or not accountability_config.self_reflection_settings.enable_automatic_reflection:
                return
            
            # Extract key metrics
            story_loss = accountability_data.get('story_loss', 0.0)
            responsibility_data = accountability_data.get('responsibility', {})
            responsibility_score = responsibility_data.get('accountability_score', 0.5)
            
            # Check trigger conditions
            metrics = {
                'story_loss': story_loss,
                'responsibility_score': responsibility_score,
                'responsibility_drop': max(0, 0.5 - responsibility_score),  # How much below neutral
                'coherence_score': accountability_data.get('gnf_analysis', {}).get('current_scores', {}).get('coherence', 0.5)
            }
            
            if accountability_config.should_trigger_self_reflection(metrics):
                await self._trigger_self_reflection(metrics, accountability_data)
            
        except Exception as e:
            logger.error(f"Failed to check self-reflection triggers: {e}")
    
    async def _trigger_self_reflection(self, metrics: Dict[str, float], 
                                     accountability_data: Dict[str, Any]):
        """Trigger self-reflection process"""
        try:
            logger.info(f"Triggering self-reflection for agent {self.agent_id}")
            
            # Create self-reflection prompt
            reflection_prompt = accountability_config.self_reflection_settings.reflection_prompt_template.format(
                story_loss=metrics.get('story_loss', 0.0),
                responsibility_score=metrics.get('responsibility_score', 0.5),
                coherence_score=metrics.get('coherence_score', 0.5)
            )
            
            # Generate self-reflection using LLM
            reflection_response = await self.llm_service.chat_completion([
                {"role": "system", "content": self.agent_config.get('system_prompt', '')},
                {"role": "user", "content": reflection_prompt}
            ])
            
            # Store self-reflection result
            reflection_data = {
                'agent_id': self.agent_id,
                'trigger_metrics': metrics,
                'reflection_content': reflection_response.content,
                'trigger_data': accountability_data,
                'reflection_type': 'automatic',
                'token_usage': reflection_response.token_usage.__dict__
            }
            
            # Store as agent memory
            await firebase_service.store_agent_memory({
                'agent_id': self.agent_id,
                'memory_type': 'self_reflection',
                'text_content': reflection_response.content,
                'consolidation_strength': 0.8,
                'importance_score': 0.9,
                'emotional_valence': 0.0,  # Neutral for self-reflection
                'tags': ['self_reflection', 'accountability', 'improvement'],
                'metadata': reflection_data
            })
            
            logger.info(f"Self-reflection completed for agent {self.agent_id}")
            
        except Exception as e:
            logger.error(f"Failed to trigger self-reflection: {e}")
    
    async def create_conversation(self, user_id: Optional[str] = None) -> str:
        """Create a new conversation"""
        if not self.initialized:
            raise RuntimeError("Agent not initialized")
        
        try:
            return await firebase_service.create_conversation(
                self.agent_id, user_id,
                metadata={
                    'agent_version': self.agent_config.get('version', '1.0'),
                    'accountability_enabled': settings.enable_gnf
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
            raise
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information and status"""
        try:
            tool_count = len(self.tool_registry.get_tools()) if self.tool_registry else 0
            
            return {
                'agent_id': self.agent_id,
                'name': self.agent_config.get('name', 'Unknown'),
                'description': self.agent_config.get('description', ''),
                'model': self.agent_config.get('model', settings.default_model),
                'initialized': self.initialized,
                'tools_count': tool_count,
                'knowledge_base_enabled': self.knowledge_service is not None,
                'mcp_enabled': self.mcp_service is not None,
                'accountability_enabled': settings.enable_gnf,
                'development_stage': self.agent_config.get('development_stage', 'nascent'),
                'narrative_coherence_score': self.agent_config.get('narrative_coherence_score', 0.5),
                'responsibility_score': self.agent_config.get('responsibility_score', 0.5),
                'version': '1.0.0',
                'last_updated': self.agent_config.get('loaded_at')
            }
            
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return {'error': str(e)}
    
    async def get_conversation_stats(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation statistics"""
        if not self.conversation_manager:
            return None
        
        return self.conversation_manager.get_conversation_stats(conversation_id)
    
    async def get_accountability_summary(self) -> Dict[str, Any]:
        """Get accountability summary"""
        if not self.conversation_manager:
            return {'error': 'Conversation manager not initialized'}
        
        return await self.conversation_manager.get_accountability_summary()
    
    def get_token_usage(self) -> Dict[str, Any]:
        """Get token usage statistics"""
        if not self.llm_service:
            return {'error': 'LLM service not initialized'}
        
        usage = self.llm_service.get_token_usage()
        return {
            'prompt_tokens': usage.prompt_tokens,
            'completion_tokens': usage.completion_tokens,
            'total_tokens': usage.total_tokens,
            'estimated_cost': self.llm_service.calculate_cost(usage),
            'model': self.llm_service.model
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check"""
        health_status = {
            'agent_id': self.agent_id,
            'initialized': self.initialized,
            'timestamp': datetime.utcnow().isoformat(),
            'components': {}
        }
        
        if self.initialized:
            # LLM service health
            if self.llm_service:
                health_status['components']['llm_service'] = await self.llm_service.health_check()
            
            # Knowledge service health
            if self.knowledge_service:
                health_status['components']['knowledge_service'] = await self.knowledge_service.health_check()
            
            # MCP service health
            if self.mcp_service:
                health_status['components']['mcp_service'] = await self.mcp_service.health_check()
            
            # Tool registry health
            if self.tool_registry:
                health_status['components']['tool_registry'] = len(self.tool_registry.get_tools()) > 0
            
            # Conversation manager health
            if self.conversation_manager:
                health_status['components']['conversation_manager'] = True
                health_status['active_conversations'] = self.conversation_manager.get_active_conversations_count()
        
        # Overall health
        component_health = list(health_status['components'].values())
        health_status['overall_healthy'] = all(component_health) if component_health else False
        
        return health_status
    
    async def shutdown(self):
        """Graceful shutdown of the agent"""
        try:
            logger.info(f"Shutting down agent {self.agent_id}")
            
            # Cleanup conversation manager
            if self.conversation_manager:
                await self.conversation_manager.cleanup_inactive_conversations(max_age_hours=0)
            
            # Reset components
            self.llm_service = None
            self.conversation_manager = None
            self.knowledge_service = None
            self.mcp_service = None
            self.tool_registry = None
            
            self.initialized = False
            
            logger.info(f"Agent {self.agent_id} shutdown completed")
            
        except Exception as e:
            logger.error(f"Error during agent shutdown: {e}")


# Global agent instance (will be initialized with actual agent_id)
_global_agent: Optional[AccountableAgent] = None


async def get_agent(agent_id: str) -> AccountableAgent:
    """Get or create the global agent instance"""
    global _global_agent
    
    if _global_agent is None or _global_agent.agent_id != agent_id:
        _global_agent = AccountableAgent(agent_id)
        await _global_agent.initialize()
    
    return _global_agent


async def initialize_agent(agent_id: str) -> AccountableAgent:
    """Initialize agent with given ID"""
    agent = AccountableAgent(agent_id)
    success = await agent.initialize()
    
    if not success:
        raise RuntimeError(f"Failed to initialize agent {agent_id}")
    
    return agent