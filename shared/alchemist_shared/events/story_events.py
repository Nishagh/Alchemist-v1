"""
Story Event System for Alchemist Agent Narratives

This module implements Cloud Pub/Sub based story event publishing and subscribing
for maintaining coherent agent life-stories across microservices.
"""
import os
import json
import logging
import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import uuid
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID=os.getenv('PROJECT_ID')

# Google Cloud Pub/Sub
try:
    from google.cloud import pubsub_v1
    from google.cloud.pubsub_v1.types import PubsubMessage
    from concurrent.futures import ThreadPoolExecutor
    PUBSUB_AVAILABLE = True
except ImportError:
    logging.warning("Google Cloud Pub/Sub not available - story events will work in local mode only")
    PUBSUB_AVAILABLE = False

logger = logging.getLogger(__name__)

class StoryEventType(Enum):
    """Types of story events that can occur in agent narratives"""
    CONVERSATION = "conversation"
    KNOWLEDGE_ACQUISITION = "knowledge_acquisition"
    KNOWLEDGE_REMOVAL = "knowledge_removal"
    PROMPT_UPDATE = "prompt_update"
    GOAL_CHANGE = "goal_change"
    DECISION_MADE = "decision_made"
    BELIEF_REVISION = "belief_revision"
    REFLECTION = "reflection"
    ERROR_ENCOUNTERED = "error_encountered"
    TOOL_USAGE = "tool_usage"
    SYSTEM_UPDATE = "system_update"
    
    # Life Journey Events
    AGENT_CREATED = "agent_created"
    AGENT_NAMED = "agent_named"
    AGENT_DESCRIPTION_UPDATED = "agent_description_updated"
    KNOWLEDGE_BASE_FILE_ADDED = "knowledge_base_file_added"
    KNOWLEDGE_BASE_FILE_REMOVED = "knowledge_base_file_removed"
    EXTERNAL_API_ATTACHED = "external_api_attached"
    EXTERNAL_API_DETACHED = "external_api_detached"
    AGENT_DEPLOYED = "agent_deployed"
    AGENT_UNDEPLOYED = "agent_undeployed"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    CONFIGURATION_UPDATED = "configuration_updated"
    TRAINING_STARTED = "training_started"
    TRAINING_COMPLETED = "training_completed"
    
    # Additional comprehensive tracking events
    BILLING_TRANSACTION = "billing_transaction"
    INTEGRATION_CONNECTED = "integration_connected"
    INTEGRATION_DISCONNECTED = "integration_disconnected"
    PERFORMANCE_ISSUE = "performance_issue"
    SECURITY_EVENT = "security_event"
    USER_FEEDBACK = "user_feedback"
    MODEL_VERSION_UPDATED = "model_version_updated"
    MEMORY_ARCHIVED = "memory_archived"
    COLLABORATION_EVENT = "collaboration_event"
    EXPERIMENT_STARTED = "experiment_started"
    EXPERIMENT_COMPLETED = "experiment_completed"

class StoryEventPriority(Enum):
    """Priority levels for story event processing"""
    LOW = "low"
    MEDIUM = "medium" 
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class StoryEvent:
    """
    A story event represents a significant occurrence in an agent's life-story
    that should be tracked in the narrative spine.
    """
    agent_id: str
    event_type: StoryEventType
    content: str
    source_service: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    confidence: float = 0.8
    priority: StoryEventPriority = StoryEventPriority.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    local_reference: Optional[str] = None
    causal_parents: List[str] = field(default_factory=list)
    narrative_context: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        # Convert enums to strings
        data['event_type'] = self.event_type.value
        data['priority'] = self.priority.value
        # Convert datetime to ISO string
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StoryEvent':
        """Create StoryEvent from dictionary"""
        # Convert strings back to enums
        data['event_type'] = StoryEventType(data['event_type'])
        data['priority'] = StoryEventPriority(data['priority'])
        # Convert ISO string back to datetime
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        return cls(**data)
    
    def to_pubsub_message(self) -> bytes:
        """Convert to Pub/Sub message format"""
        return json.dumps(self.to_dict()).encode('utf-8')
    
    @classmethod
    def from_pubsub_message(cls, message: bytes) -> 'StoryEvent':
        """Create StoryEvent from Pub/Sub message"""
        data = json.loads(message.decode('utf-8'))
        return cls.from_dict(data)

class StoryEventPublisher:
    """
    Publisher for story events using Google Cloud Pub/Sub
    
    Handles async publishing of story events to the narrative spine.
    Requires Google Cloud Pub/Sub to be available.
    """
    
    def __init__(
        self, 
        project_id: str,
        topic_name: str = "agent-story-events"
    ):
        self.project_id = project_id
        self.topic_name = topic_name
        
        if not PUBSUB_AVAILABLE:
            raise RuntimeError("Google Cloud Pub/Sub is required but not available. Install google-cloud-pubsub.")
        
        self.publisher = pubsub_v1.PublisherClient()
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
        self._ensure_topic_exists()
        logger.info(f"Story event publisher initialized for topic: {self.topic_path}")
        
        # Async executor for non-blocking operations
        self.executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="story-event")
    
    def _ensure_topic_exists(self):
        """Create topic if it doesn't exist"""
        try:
            self.publisher.get_topic(request={"topic": self.topic_path})
            logger.debug(f"Topic {self.topic_name} already exists")
        except Exception:
            try:
                self.publisher.create_topic(request={"name": self.topic_path})
                logger.info(f"Created topic: {self.topic_name}")
            except Exception as e:
                logger.error(f"Failed to create topic {self.topic_name}: {e}")
                raise
    
    async def publish_event(self, event: StoryEvent) -> bool:
        """
        Publish a story event asynchronously to Google Cloud Pub/Sub
        
        Returns True if published successfully, raises exception otherwise
        """
        return await self._publish_pubsub(event)
    
    async def _publish_pubsub(self, event: StoryEvent) -> bool:
        """Publish event to Google Cloud Pub/Sub"""
        message_data = event.to_pubsub_message()
        
        # Add message attributes for filtering
        attributes = {
            "agent_id": event.agent_id,
            "event_type": event.event_type.value,
            "source_service": event.source_service,
            "priority": event.priority.value,
            "timestamp": event.timestamp.isoformat()
        }
        
        # Publish async using executor
        loop = asyncio.get_event_loop()
        future = self.publisher.publish(
            self.topic_path,
            message_data,
            **attributes
        )
        
        # Wait for publish with timeout
        message_id = await loop.run_in_executor(
            self.executor,
            lambda: future.result(timeout=10.0)
        )
        
        logger.debug(f"Published story event {event.event_id} with message ID: {message_id}")
        return True
    
    async def publish_conversation_event(
        self,
        agent_id: str,
        user_message: str,
        agent_response: str,
        conversation_id: str,
        source_service: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Convenience method for publishing conversation events"""
        event = StoryEvent(
            agent_id=agent_id,
            event_type=StoryEventType.CONVERSATION,
            content=f"User: '{user_message[:100]}...' → Agent: '{agent_response[:100]}...'",
            source_service=source_service,
            priority=StoryEventPriority.MEDIUM,
            metadata={
                "conversation_id": conversation_id,
                "user_message": user_message,
                "agent_response": agent_response,
                **(metadata or {})
            }
        )
        return await self.publish_event(event)
    
    async def publish_knowledge_event(
        self,
        agent_id: str,
        filename: str,
        action: str,  # "acquired" or "removed"
        source_service: str,
        narrative_content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Convenience method for publishing knowledge events"""
        event_type = (
            StoryEventType.KNOWLEDGE_ACQUISITION if action == "acquired"
            else StoryEventType.KNOWLEDGE_REMOVAL
        )
        
        event = StoryEvent(
            agent_id=agent_id,
            event_type=event_type,
            content=narrative_content,
            source_service=source_service,
            priority=StoryEventPriority.HIGH,
            metadata={
                "filename": filename,
                "action": action,
                **(metadata or {})
            }
        )
        return await self.publish_event(event)
    
    def close(self):
        """Clean up resources"""
        if hasattr(self, 'executor'):
            self.executor.shutdown(wait=True)

class StoryEventSubscriber:
    """
    Subscriber for story events using Google Cloud Pub/Sub
    
    Handles receiving and processing story events from the narrative spine.
    Requires Google Cloud Pub/Sub to be available.
    """
    
    def __init__(
        self,
        project_id: str,
        subscription_name: str,
        topic_name: str = "agent-story-events"
    ):
        self.project_id = project_id
        self.subscription_name = subscription_name
        self.topic_name = topic_name
        
        if not PUBSUB_AVAILABLE:
            raise RuntimeError("Google Cloud Pub/Sub is required but not available. Install google-cloud-pubsub.")
        
        self.event_handlers: Dict[StoryEventType, List[Callable]] = {}
        self.running = False
        
        self.subscriber = pubsub_v1.SubscriberClient()
        self.publisher = pubsub_v1.PublisherClient()
        self.subscription_path = self.subscriber.subscription_path(
            project_id, subscription_name
        )
        self.topic_path = self.publisher.topic_path(project_id, topic_name)
        self._ensure_subscription_exists()
        logger.info(f"Story event subscriber initialized: {self.subscription_path}")
    
    def _ensure_subscription_exists(self):
        """Create subscription if it doesn't exist"""
        try:
            self.subscriber.get_subscription(request={"subscription": self.subscription_path})
            logger.debug(f"Subscription {self.subscription_name} already exists")
        except Exception:
            try:
                self.subscriber.create_subscription(
                    request={
                        "name": self.subscription_path,
                        "topic": self.topic_path
                    }
                )
                logger.info(f"Created subscription: {self.subscription_name}")
            except Exception as e:
                logger.error(f"Failed to create subscription {self.subscription_name}: {e}")
                raise
    
    def add_handler(
        self, 
        event_type: StoryEventType, 
        handler: Callable[[StoryEvent], None]
    ):
        """Add an event handler for specific story event types"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        logger.debug(f"Added handler for {event_type.value} events")
    
    def add_global_handler(self, handler: Callable[[StoryEvent], None]):
        """Add a handler that receives all story events"""
        for event_type in StoryEventType:
            self.add_handler(event_type, handler)
    
    def _test_pubsub_connectivity(self):
        """Test Pub/Sub connectivity (synchronous method for thread execution)"""
        try:
            # Test subscription exists and is accessible
            self.subscriber.get_subscription(request={"subscription": self.subscription_path})
            return True
        except Exception as e:
            logger.error(f"Pub/Sub connectivity test failed: {e}")
            raise
    
    async def start_listening(self):
        """Start listening for story events from Google Cloud Pub/Sub using thread-based approach"""
        self.running = True
        logger.info(f"Starting story event subscriber: {self.subscription_name}")
        
        # Add initialization timeout to prevent blocking startup
        initialization_timeout = 10  # seconds
        
        try:
            # Test Pub/Sub connectivity with timeout
            logger.info("Testing Pub/Sub connectivity...")
            await asyncio.wait_for(
                asyncio.to_thread(self._test_pubsub_connectivity),
                timeout=initialization_timeout
            )
            logger.info("Pub/Sub connectivity confirmed")
            
            # Start the event processing loop
            while self.running:
                try:
                    # Use asyncio.to_thread to make blocking pull operation non-blocking
                    response = await asyncio.to_thread(
                        self.subscriber.pull,
                        request={
                            "subscription": self.subscription_path,
                            "max_messages": 10,
                        },
                        timeout=5.0  # Shorter timeout to prevent long blocking
                    )
                    
                    ack_ids = []
                    for received_message in response.received_messages:
                        try:
                            # Process the message
                            await self._process_message(received_message.message)
                            ack_ids.append(received_message.ack_id)
                        except Exception as e:
                            logger.error(f"Failed to process story event message: {e}")
                            # Still acknowledge to avoid redelivery of bad messages
                            ack_ids.append(received_message.ack_id)
                    
                    # Acknowledge processed messages using thread
                    if ack_ids:
                        await asyncio.to_thread(
                            self.subscriber.acknowledge,
                            request={
                                "subscription": self.subscription_path,
                                "ack_ids": ack_ids
                            }
                        )
                        
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    logger.debug("Pub/Sub pull timeout (normal)")
                    continue
                except Exception as e:
                    # 504 Deadline Exceeded is normal when no messages are available
                    if "504" in str(e) and "Deadline Exceeded" in str(e):
                        logger.debug(f"Pub/Sub deadline exceeded (normal - no messages): {e}")
                        await asyncio.sleep(1)  # Short pause for empty queue
                    else:
                        logger.error(f"Error in story event subscriber loop: {e}")
                        await asyncio.sleep(5)  # Brief pause before retrying
                    
        except asyncio.TimeoutError:
            logger.error(f"Pub/Sub initialization timeout after {initialization_timeout}s - event processing disabled")
            self.running = False
            raise
        except Exception as e:
            logger.error(f"Failed to initialize Pub/Sub connection: {e}")
            self.running = False
            raise
                    
        except Exception as e:
            logger.error(f"Story event subscriber failed: {e}")
        finally:
            self.running = False
    
    async def _process_message(self, message: PubsubMessage):
        """Process a received Pub/Sub message"""
        try:
            # Parse the story event
            event = StoryEvent.from_pubsub_message(message.data)
            
            # Get handlers for this event type
            handlers = self.event_handlers.get(event.event_type, [])
            
            # Process with all relevant handlers
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(event)
                    else:
                        handler(event)
                except Exception as e:
                    logger.error(f"Story event handler failed for {event.event_id}: {e}")
            
            logger.debug(f"Processed story event: {event.event_id}")
            
        except Exception as e:
            logger.error(f"Failed to parse story event message: {e}")
            raise
    
    def stop_listening(self):
        """Stop listening for story events"""
        self.running = False
        logger.info("Story event subscriber stopped")

# Global publisher instance for easy access
_global_publisher: Optional[StoryEventPublisher] = None

def get_story_event_publisher() -> Optional[StoryEventPublisher]:
    """Get the global story event publisher instance"""
    return _global_publisher

def init_story_event_publisher(
    project_id: str,
    topic_name: str = "agent-story-events"
) -> StoryEventPublisher:
    """Initialize the global story event publisher"""
    global _global_publisher
    _global_publisher = StoryEventPublisher(project_id, topic_name)
    return _global_publisher