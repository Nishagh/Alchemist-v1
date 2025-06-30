"""
Agent Lifecycle Service

This service tracks and manages agent lifecycle events from creation to deployment.
All events are stored in Firestore and published via the story event system.
"""
import os
import logging
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
from google.cloud import firestore
from ..events.story_events import (
    StoryEvent, 
    StoryEventType, 
    StoryEventPriority,
    get_story_event_publisher
)

logger = logging.getLogger(__name__)

class AgentLifecycleService:
    """
    Service for tracking agent lifecycle events and storing them in Firestore
    """
    
    def __init__(self, firestore_client: Optional[firestore.Client] = None):
        self.db = firestore_client or firestore.Client()
        self.collection_name = "agent_lifecycle_events"
        self.publisher = get_story_event_publisher()
        
    async def record_event(
        self,
        agent_id: str,
        event_type: StoryEventType,
        title: str,
        description: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None,
        priority: StoryEventPriority = StoryEventPriority.MEDIUM
    ) -> str:
        """
        Record a lifecycle event for an agent
        
        Args:
            agent_id: The agent's unique identifier
            event_type: Type of lifecycle event
            title: Short title for the event
            description: Detailed description of what happened
            user_id: User who triggered the event
            metadata: Additional event-specific data
            priority: Event priority level
            
        Returns:
            Event ID of the recorded event
        """
        try:
            # Create the lifecycle event
            timestamp = datetime.now(timezone.utc)
            event_data = {
                'agent_id': agent_id,
                'event_type': event_type.value,
                'title': title,
                'description': description,
                'user_id': user_id,
                'timestamp': timestamp,
                'metadata': metadata or {},
                'priority': priority.value
            }
            
            # Store in Firestore
            doc_ref = self.db.collection(self.collection_name).add(event_data)[1]
            event_id = doc_ref.id
            
            # Update with document ID
            doc_ref.update({'event_id': event_id})
            
            # Publish to story event system if publisher is available
            if self.publisher:
                story_event = StoryEvent(
                    agent_id=agent_id,
                    event_type=event_type,
                    content=f"{title}: {description}",
                    source_service="agent-lifecycle",
                    priority=priority,
                    metadata={
                        'lifecycle_event_id': event_id,
                        'user_id': user_id,
                        **(metadata or {})
                    }
                )
                await self.publisher.publish_event(story_event)
            
            logger.info(f"Recorded lifecycle event {event_id} for agent {agent_id}: {title}")
            return event_id
            
        except Exception as e:
            logger.error(f"Failed to record lifecycle event for agent {agent_id}: {e}")
            raise
    
    def get_agent_lifecycle_events(
        self, 
        agent_id: str, 
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get all lifecycle events for an agent, ordered by timestamp (newest first)
        
        Args:
            agent_id: The agent's unique identifier
            limit: Maximum number of events to return
            
        Returns:
            List of lifecycle events
        """
        try:
            events_ref = (self.db.collection(self.collection_name)
                         .where('agent_id', '==', agent_id)
                         .order_by('timestamp', direction=firestore.Query.DESCENDING)
                         .limit(limit))
            
            events = []
            for doc in events_ref.stream():
                event_data = doc.to_dict()
                event_data['id'] = doc.id
                events.append(event_data)
            
            logger.debug(f"Retrieved {len(events)} lifecycle events for agent {agent_id}")
            return events
            
        except Exception as e:
            logger.error(f"Failed to get lifecycle events for agent {agent_id}: {e}")
            return []
    
    # Convenience methods for common lifecycle events
    
    async def record_agent_created(
        self, 
        agent_id: str, 
        agent_name: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent creation event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_CREATED,
            title="Agent Created",
            description=f"Agent '{agent_name}' was created and initialized",
            user_id=user_id,
            metadata={'agent_name': agent_name, **(metadata or {})},
            priority=StoryEventPriority.HIGH
        )
    
    async def record_agent_named(
        self, 
        agent_id: str, 
        old_name: str, 
        new_name: str, 
        user_id: str
    ) -> str:
        """Record agent naming/renaming event"""
        description = (f"Agent renamed from '{old_name}' to '{new_name}'" 
                      if old_name else f"Agent named '{new_name}'")
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_NAMED,
            title="Agent Named" if not old_name else "Agent Renamed",
            description=description,
            user_id=user_id,
            metadata={'old_name': old_name, 'new_name': new_name}
        )
    
    async def record_description_updated(
        self, 
        agent_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent description update event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_DESCRIPTION_UPDATED,
            title="Description Updated",
            description="Agent description and instructions were updated",
            user_id=user_id,
            metadata=metadata
        )
    
    async def record_prompt_updated(
        self, 
        agent_id: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent prompt update event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.PROMPT_UPDATE,
            title="System Prompt Updated",
            description="Agent's system prompt and behavior instructions were modified",
            user_id=user_id,
            metadata=metadata
        )
    
    async def record_knowledge_file_added(
        self, 
        agent_id: str, 
        filename: str, 
        file_size: int,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record knowledge base file addition event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.KNOWLEDGE_BASE_FILE_ADDED,
            title="Knowledge File Added",
            description=f"Knowledge base file '{filename}' ({file_size} bytes) was added",
            user_id=user_id,
            metadata={'filename': filename, 'file_size': file_size, **(metadata or {})},
            priority=StoryEventPriority.HIGH
        )
    
    async def record_knowledge_file_removed(
        self, 
        agent_id: str, 
        filename: str, 
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record knowledge base file removal event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.KNOWLEDGE_BASE_FILE_REMOVED,
            title="Knowledge File Removed",
            description=f"Knowledge base file '{filename}' was removed",
            user_id=user_id,
            metadata={'filename': filename, **(metadata or {})},
            priority=StoryEventPriority.MEDIUM
        )
    
    async def record_api_attached(
        self, 
        agent_id: str, 
        api_name: str, 
        api_url: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record external API attachment event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.EXTERNAL_API_ATTACHED,
            title="External API Attached",
            description=f"External API '{api_name}' ({api_url}) was attached to agent",
            user_id=user_id,
            metadata={'api_name': api_name, 'api_url': api_url, **(metadata or {})},
            priority=StoryEventPriority.HIGH
        )
    
    async def record_api_detached(
        self, 
        agent_id: str, 
        api_name: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record external API detachment event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.EXTERNAL_API_DETACHED,
            title="External API Detached",
            description=f"External API '{api_name}' was detached from agent",
            user_id=user_id,
            metadata={'api_name': api_name, **(metadata or {})},
            priority=StoryEventPriority.MEDIUM
        )
    
    async def record_agent_deployed(
        self, 
        agent_id: str, 
        platform: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent deployment event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_DEPLOYED,
            title="Agent Deployed",
            description=f"Agent was successfully deployed to {platform}",
            user_id=user_id,
            metadata={'platform': platform, **(metadata or {})},
            priority=StoryEventPriority.CRITICAL
        )
    
    async def record_agent_undeployed(
        self, 
        agent_id: str, 
        platform: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent undeployment event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_UNDEPLOYED,
            title="Agent Undeployed",
            description=f"Agent was undeployed from {platform}",
            user_id=user_id,
            metadata={'platform': platform, **(metadata or {})},
            priority=StoryEventPriority.HIGH
        )
    
    async def record_status_changed(
        self, 
        agent_id: str, 
        old_status: str, 
        new_status: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent status change event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.AGENT_STATUS_CHANGED,
            title="Status Changed",
            description=f"Agent status changed from '{old_status}' to '{new_status}'",
            user_id=user_id,
            metadata={'old_status': old_status, 'new_status': new_status, **(metadata or {})},
            priority=StoryEventPriority.MEDIUM
        )
    
    async def record_configuration_updated(
        self, 
        agent_id: str, 
        config_section: str,
        user_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Record agent configuration update event"""
        return await self.record_event(
            agent_id=agent_id,
            event_type=StoryEventType.CONFIGURATION_UPDATED,
            title="Configuration Updated",
            description=f"Agent {config_section} configuration was updated",
            user_id=user_id,
            metadata={'config_section': config_section, **(metadata or {})},
            priority=StoryEventPriority.MEDIUM
        )

# Global instance for easy access
_global_lifecycle_service: Optional[AgentLifecycleService] = None

def get_agent_lifecycle_service() -> Optional[AgentLifecycleService]:
    """Get the global agent lifecycle service instance"""
    return _global_lifecycle_service

def init_agent_lifecycle_service(
    firestore_client: Optional[firestore.Client] = None
) -> AgentLifecycleService:
    """Initialize the global agent lifecycle service"""
    global _global_lifecycle_service
    _global_lifecycle_service = AgentLifecycleService(firestore_client)
    return _global_lifecycle_service