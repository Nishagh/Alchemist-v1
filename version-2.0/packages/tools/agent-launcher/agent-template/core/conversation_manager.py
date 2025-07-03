"""
Enhanced Conversation Manager with Accountability Tracking
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, AsyncGenerator
from datetime import datetime, timezone
from dataclasses import dataclass

from core.llm_service import DirectLLMService, LLMResponse, TokenUsage
from accountability.gnf_integration import GNFIntegration
from accountability.story_loss_calculator import StoryLossCalculator
from accountability.responsibility_assessor import ResponsibilityAssessor
from services.firebase_service import firebase_service
from config.settings import settings
from config.accountability_config import accountability_config

logger = logging.getLogger(__name__)


@dataclass
class ConversationResult:
    """Result of conversation processing"""
    success: bool
    response: str
    conversation_id: str
    token_usage: TokenUsage
    accountability_data: Dict[str, Any]
    error: Optional[str] = None


@dataclass
class ConversationContext:
    """Context for a conversation"""
    conversation_id: str
    messages: List[Dict[str, str]]
    agent_config: Dict[str, Any]
    user_id: Optional[str] = None
    session_metadata: Dict[str, Any] = None


class EnhancedConversationManager:
    """
    Enhanced conversation manager with full accountability tracking
    """
    
    def __init__(self, agent_id: str, llm_service: DirectLLMService, 
                 agent_config: Dict[str, Any]):
        self.agent_id = agent_id
        self.llm_service = llm_service
        self.agent_config = agent_config
        
        # Initialize accountability components
        self.gnf_integration = GNFIntegration(agent_id)
        self.story_loss_calculator = StoryLossCalculator(agent_id)
        self.responsibility_assessor = ResponsibilityAssessor(agent_id)
        
        # Conversation state
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.conversation_stats: Dict[str, Dict[str, Any]] = {}
        
        # System prompt from agent config
        self.system_prompt = agent_config.get('system_prompt', 'You are a helpful AI assistant.')
        
        logger.info(f"Enhanced conversation manager initialized for agent {agent_id}")
    
    async def initialize(self):
        """Initialize the conversation manager"""
        try:
            # Initialize GNF narrative identity
            await self.gnf_integration.initialize_narrative_identity()
            logger.info("Conversation manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize conversation manager: {e}")
            raise
    
    async def process_message(self, conversation_id: str, message: str, 
                            user_id: Optional[str] = None,
                            tools: Optional[List[Dict[str, Any]]] = None) -> ConversationResult:
        """
        Process a user message with full accountability tracking
        
        Args:
            conversation_id: The conversation identifier
            message: User's message
            user_id: Optional user identifier
            tools: Available tools for the agent
            
        Returns:
            ConversationResult with response and accountability data
        """
        try:
            logger.info(f"Processing message for conversation {conversation_id}")
            
            # Get or create conversation context
            context = await self._get_conversation_context(conversation_id, user_id)
            
            # Capture pre-interaction state for accountability
            pre_state = await self._capture_narrative_state()
            
            # Prepare messages for LLM
            messages = await self._prepare_messages(context, message)
            
            # Generate response using LLM
            llm_response = await self.llm_service.chat_completion(
                messages=messages,
                temperature=self.agent_config.get('temperature', 0.7),
                max_tokens=self.agent_config.get('max_tokens', settings.max_tokens),
                tools=tools
            )
            
            # Capture post-interaction state
            post_state = await self._capture_narrative_state()
            
            # Process accountability tracking
            accountability_data = await self._process_accountability(
                conversation_id, message, llm_response.content, 
                pre_state, post_state, context
            )
            
            # Update conversation context
            await self._update_conversation_context(context, message, llm_response.content)
            
            # Store conversation with accountability metadata
            await self._store_conversation_message(
                conversation_id, message, llm_response.content, 
                llm_response.token_usage, accountability_data
            )
            
            # Track token usage
            self.llm_service.track_session_usage(conversation_id, llm_response.token_usage)
            
            # Update conversation stats
            await self._update_conversation_stats(conversation_id, llm_response)
            
            logger.info(f"Successfully processed message for conversation {conversation_id}")
            
            return ConversationResult(
                success=True,
                response=llm_response.content,
                conversation_id=conversation_id,
                token_usage=llm_response.token_usage,
                accountability_data=accountability_data
            )
            
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return ConversationResult(
                success=False,
                response="I apologize, but I encountered an error processing your message.",
                conversation_id=conversation_id,
                token_usage=TokenUsage(),
                accountability_data={},
                error=str(e)
            )
    
    async def stream_response(self, conversation_id: str, message: str,
                            user_id: Optional[str] = None) -> AsyncGenerator[str, None]:
        """
        Stream response with accountability tracking
        
        Args:
            conversation_id: The conversation identifier
            message: User's message
            user_id: Optional user identifier
            
        Yields:
            Response chunks as they arrive
        """
        try:
            # Get conversation context
            context = await self._get_conversation_context(conversation_id, user_id)
            
            # Capture pre-interaction state
            pre_state = await self._capture_narrative_state()
            
            # Prepare messages
            messages = await self._prepare_messages(context, message)
            
            # Stream response
            response_chunks = []
            async for chunk in self.llm_service.stream_chat_completion(messages):
                response_chunks.append(chunk)
                yield chunk
            
            # Process complete response for accountability
            complete_response = "".join(response_chunks)
            
            # Capture post-interaction state
            post_state = await self._capture_narrative_state()
            
            # Process accountability (asynchronously to not block streaming)
            asyncio.create_task(self._process_accountability_async(
                conversation_id, message, complete_response,
                pre_state, post_state, context
            ))
            
        except Exception as e:
            logger.error(f"Failed to stream response: {e}")
            yield f"Error: {str(e)}"
    
    async def _get_conversation_context(self, conversation_id: str, 
                                      user_id: Optional[str] = None) -> ConversationContext:
        """Get or create conversation context"""
        
        if conversation_id in self.active_conversations:
            return self.active_conversations[conversation_id]
        
        # Load existing conversation or create new one
        existing_messages = await firebase_service.get_conversation_messages(
            conversation_id, limit=settings.conversation_memory_limit
        )
        
        if not existing_messages:
            # Create new conversation
            await firebase_service.create_conversation(
                self.agent_id, user_id, 
                metadata={'agent_config_version': self.agent_config.get('version', '1.0')}
            )
        
        # Convert to message format
        messages = []
        for msg in existing_messages:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        context = ConversationContext(
            conversation_id=conversation_id,
            messages=messages,
            agent_config=self.agent_config,
            user_id=user_id,
            session_metadata={}
        )
        
        self.active_conversations[conversation_id] = context
        return context
    
    async def _prepare_messages(self, context: ConversationContext, 
                              new_message: str) -> List[Dict[str, str]]:
        """Prepare messages for LLM including system prompt and context"""
        
        messages = [
            {"role": "system", "content": self.system_prompt}
        ]
        
        # Add conversation history with intelligent truncation
        history_messages = await self._truncate_conversation_history(context.messages)
        messages.extend(history_messages)
        
        # Add new user message
        messages.append({"role": "user", "content": new_message})
        
        return messages
    
    async def _truncate_conversation_history(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Intelligently truncate conversation history to fit context window"""
        
        if not messages:
            return []
        
        # Estimate token count (rough approximation)
        total_tokens = sum(len(msg.get("content", "").split()) * 1.3 for msg in messages)
        max_tokens = settings.conversation_memory_limit
        
        if total_tokens <= max_tokens:
            return messages
        
        # Keep recent messages and important context
        # This is a simple implementation - can be enhanced with semantic importance
        truncated = []
        current_tokens = 0
        
        # Start from the end (most recent) and work backwards
        for message in reversed(messages):
            msg_tokens = len(message.get("content", "").split()) * 1.3
            if current_tokens + msg_tokens <= max_tokens:
                truncated.insert(0, message)
                current_tokens += msg_tokens
            else:
                break
        
        return truncated
    
    async def _capture_narrative_state(self) -> Dict[str, Any]:
        """Capture current narrative state for accountability tracking"""
        try:
            gnf_state = self.gnf_integration.get_current_state()
            if gnf_state:
                return {
                    'development_stage': gnf_state.development_stage.value,
                    'narrative_coherence_score': gnf_state.narrative_coherence_score,
                    'responsibility_score': gnf_state.responsibility_score,
                    'experience_points': gnf_state.experience_points,
                    'total_interactions': gnf_state.total_interactions,
                    'timestamp': datetime.utcnow().isoformat()
                }
            return {}
        except Exception as e:
            logger.error(f"Failed to capture narrative state: {e}")
            return {}
    
    async def _process_accountability(self, conversation_id: str, user_message: str,
                                    agent_response: str, pre_state: Dict[str, Any],
                                    post_state: Dict[str, Any], 
                                    context: ConversationContext) -> Dict[str, Any]:
        """Process full accountability tracking for the interaction"""
        
        accountability_data = {}
        
        try:
            interaction_data = {
                'conversation_id': conversation_id,
                'user_message': user_message,
                'agent_response': agent_response,
                'context': {
                    'agent_id': self.agent_id,
                    'user_id': context.user_id,
                    'timestamp': datetime.utcnow().isoformat()
                }
            }
            
            # Process GNF narrative tracking
            gnf_analysis = await self.gnf_integration.process_interaction(interaction_data)
            accountability_data['gnf_analysis'] = gnf_analysis
            
            # Calculate story-loss
            story_loss = await self.story_loss_calculator.calculate_interaction_story_loss(
                pre_state, post_state, interaction_data
            )
            accountability_data['story_loss'] = story_loss
            
            # Assess responsibility
            responsibility_assessment = await self.responsibility_assessor.assess_interaction(
                interaction_data
            )
            accountability_data['responsibility'] = {
                'level': responsibility_assessment.responsibility_level.value,
                'accountability_score': responsibility_assessment.accountability_score,
                'ethical_weight': responsibility_assessment.ethical_weight,
                'decision_quality': responsibility_assessment.decision_quality,
                'learning_potential': responsibility_assessment.learning_potential
            }
            
            # Check for alert conditions
            alerts = await self._check_alert_conditions(
                story_loss, responsibility_assessment, gnf_analysis
            )
            if alerts:
                accountability_data['alerts'] = alerts
            
            logger.info(f"Accountability processing completed - Story-loss: {story_loss:.3f}, "
                       f"Responsibility: {responsibility_assessment.responsibility_level.value}")
            
        except Exception as e:
            logger.error(f"Failed to process accountability: {e}")
            accountability_data['error'] = str(e)
        
        return accountability_data
    
    async def _process_accountability_async(self, conversation_id: str, user_message: str,
                                          agent_response: str, pre_state: Dict[str, Any],
                                          post_state: Dict[str, Any], 
                                          context: ConversationContext):
        """Process accountability asynchronously (for streaming)"""
        try:
            accountability_data = await self._process_accountability(
                conversation_id, user_message, agent_response,
                pre_state, post_state, context
            )
            
            # Store the message with accountability data
            await self._store_conversation_message(
                conversation_id, user_message, agent_response,
                TokenUsage(), accountability_data  # Token usage estimated for streaming
            )
            
        except Exception as e:
            logger.error(f"Async accountability processing failed: {e}")
    
    async def _check_alert_conditions(self, story_loss: float, 
                                    responsibility_assessment, 
                                    gnf_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Check if any alert conditions are met"""
        
        alerts = []
        
        # Story-loss threshold alert
        if accountability_config.thresholds.get_severity_for_story_loss(story_loss).value in ['high', 'critical']:
            alerts.append({
                'type': 'story_loss_threshold',
                'severity': accountability_config.thresholds.get_severity_for_story_loss(story_loss).value,
                'value': story_loss,
                'threshold': accountability_config.thresholds.story_loss_warning,
                'message': f'Story-loss value {story_loss:.3f} exceeds threshold'
            })
        
        # Responsibility threshold alert
        responsibility_score = responsibility_assessment.accountability_score
        if responsibility_score < accountability_config.thresholds.responsibility_warning:
            alerts.append({
                'type': 'responsibility_threshold',
                'severity': 'medium',
                'value': responsibility_score,
                'threshold': accountability_config.thresholds.responsibility_warning,
                'message': f'Responsibility score {responsibility_score:.3f} below threshold'
            })
        
        # Narrative coherence alert
        current_coherence = gnf_analysis.get('current_scores', {}).get('coherence', 0.5)
        if current_coherence < accountability_config.thresholds.coherence_warning:
            alerts.append({
                'type': 'coherence_threshold',
                'severity': 'medium',
                'value': current_coherence,
                'threshold': accountability_config.thresholds.coherence_warning,
                'message': f'Narrative coherence {current_coherence:.3f} below threshold'
            })
        
        # Create alert events if any alerts were triggered
        for alert in alerts:
            await firebase_service.create_alert({
                'agent_id': self.agent_id,
                'alert_type': alert['type'],
                'severity': alert['severity'],
                'title': f"Agent {self.agent_id} - {alert['type'].replace('_', ' ').title()}",
                'description': alert['message'],
                'event_data': alert,
                'requires_attention': alert['severity'] in ['high', 'critical']
            })
        
        return alerts
    
    async def _update_conversation_context(self, context: ConversationContext,
                                         user_message: str, agent_response: str):
        """Update conversation context with new messages"""
        
        context.messages.extend([
            {"role": "user", "content": user_message},
            {"role": "assistant", "content": agent_response}
        ])
        
        # Truncate if necessary
        context.messages = await self._truncate_conversation_history(context.messages)
    
    async def _store_conversation_message(self, conversation_id: str, user_message: str,
                                        agent_response: str, token_usage: TokenUsage,
                                        accountability_data: Dict[str, Any]):
        """Store conversation messages with accountability metadata"""
        
        try:
            # Store user message
            await firebase_service.add_message(
                conversation_id, "user", user_message,
                accountability_metadata={'interaction_id': f"{conversation_id}_{int(datetime.utcnow().timestamp())}"}
            )
            
            # Store agent response with full accountability data
            await firebase_service.add_message(
                conversation_id, "assistant", agent_response,
                token_usage={
                    'prompt_tokens': token_usage.prompt_tokens,
                    'completion_tokens': token_usage.completion_tokens,
                    'total_tokens': token_usage.total_tokens
                },
                accountability_metadata=accountability_data
            )
            
        except Exception as e:
            logger.error(f"Failed to store conversation message: {e}")
    
    async def _update_conversation_stats(self, conversation_id: str, llm_response: LLMResponse):
        """Update conversation statistics"""
        
        if conversation_id not in self.conversation_stats:
            self.conversation_stats[conversation_id] = {
                'message_count': 0,
                'total_tokens': 0,
                'total_cost': 0.0,
                'avg_response_time': 0.0,
                'created_at': datetime.utcnow()
            }
        
        stats = self.conversation_stats[conversation_id]
        stats['message_count'] += 1
        stats['total_tokens'] += llm_response.token_usage.total_tokens
        stats['total_cost'] += self.llm_service.calculate_cost(llm_response.token_usage)
        
        # Update average response time
        current_avg = stats['avg_response_time']
        message_count = stats['message_count']
        stats['avg_response_time'] = ((current_avg * (message_count - 1)) + llm_response.response_time) / message_count
    
    def get_conversation_stats(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """Get conversation statistics"""
        return self.conversation_stats.get(conversation_id)
    
    def get_active_conversations_count(self) -> int:
        """Get number of active conversations"""
        return len(self.active_conversations)
    
    async def cleanup_inactive_conversations(self, max_age_hours: int = 24):
        """Clean up inactive conversations from memory"""
        current_time = datetime.utcnow()
        conversations_to_remove = []
        
        for conv_id, context in self.active_conversations.items():
            # Simple cleanup based on conversation age (can be enhanced)
            if conv_id in self.conversation_stats:
                created_at = self.conversation_stats[conv_id]['created_at']
                age_hours = (current_time - created_at).total_seconds() / 3600
                
                if age_hours > max_age_hours:
                    conversations_to_remove.append(conv_id)
        
        for conv_id in conversations_to_remove:
            del self.active_conversations[conv_id]
            if conv_id in self.conversation_stats:
                del self.conversation_stats[conv_id]
        
        if conversations_to_remove:
            logger.info(f"Cleaned up {len(conversations_to_remove)} inactive conversations")
    
    async def get_accountability_summary(self) -> Dict[str, Any]:
        """Get summary of accountability metrics"""
        try:
            gnf_summary = await self.gnf_integration.get_narrative_summary()
            current_story_loss = self.story_loss_calculator.get_current_story_loss()
            
            return {
                'agent_id': self.agent_id,
                'narrative_summary': gnf_summary,
                'current_story_loss': current_story_loss,
                'active_conversations': self.get_active_conversations_count(),
                'total_token_usage': self.llm_service.get_token_usage().__dict__,
                'accountability_enabled': settings.enable_gnf
            }
            
        except Exception as e:
            logger.error(f"Failed to get accountability summary: {e}")
            return {'error': str(e)}