"""
Storage Service Module

This module provides database persistence for agent states, conversations,
and artifacts. It supports Firestore backends.
"""
import logging
import json
import os
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
import uuid
import time
from firebase_admin import firestore
from .agent_generation_service import generate_agent_name, generate_agent_description, generate_agent_purpose
from ..config.firebase_config import get_firestore_client
# Set up module-level logger early
logger = logging.getLogger(__name__)

# STATE_SCHEMA_VERSION constant
STATE_SCHEMA_VERSION = 1  # Increment when the persisted state structure changes

class StorageService:
    """
    Service for storing and retrieving conversation-centric data.
    
    This class provides persistence for conversations, messages, and artifacts,
    supporting Firestore as the backend storage solution.
    
    The storage model focuses on conversations rather than agent states,
    which allows for better scaling and handling of multiple simultaneous users.
    """
    
    def __init__(self):
        self.db = get_firestore_client()
        
    async def get_agent_config(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """
        Get agent configuration by ID.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            Agent configuration dictionary or None if not found
        """
        try:
            # First, try to get agent document directly
            agent_ref = self.db.collection('alchemist_agents').document(agent_id)
            doc = agent_ref.get()
            
            if doc.exists:
                agent_config = doc.to_dict()
                logger.debug(f"Retrieved agent config {agent_id} from main document")
                return agent_config
            else:
                # If not found in main document, try the config subcollection
                logger.debug(f"Agent config {agent_id} not found in main document, checking config subcollection")
                return None                
        except Exception as e:
            logger.error(f"Error retrieving agent config {agent_id}: {str(e)}")
            return None
        
    async def create_agent_config(self, agent_id: str, message: str, userId: str) -> Optional[Dict[str, Any]]:
            """Create a new agent configuration.
            
            Args:
                agent_id: ID of the agent
                agent_config: Configuration data for the agent
                
            Returns:
                Agent configuration dictionary or None if not found
            """
            agent_ref = self.db.collection('alchemist_agents').document(agent_id)
            agent_name = await generate_agent_name(message)
            agent_description = await generate_agent_description(message)
            agent_purpose = await generate_agent_purpose(message)
            agent_config = {
                'agent_id': agent_id,
                'name': agent_name,
                'description': agent_description,
                'purpose': agent_purpose,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'userId': userId
            }
            
            agent_ref.set(agent_config)
            logger.debug(f"Created agent config {agent_id}")
            return agent_config
        
    async def get_agent_prompt(self, agent_id: str) -> Optional[str]:
        """Get the prompt for an agent."""
        try:
            agent_ref = self.db.collection('alchemist_agents').document(agent_id).collection('system_prompt').order_by('created_at', direction=firestore.Query.DESCENDING).limit(1).get()
            doc = agent_ref[0].to_dict()
            return doc.get('content', '')
        except Exception as e:
            logger.error(f"Error getting agent prompt for agent {agent_id}: {str(e)}")
            return None
        
    async def create_conversation(self, user_id: str) -> str:
        """
        Create a new conversation.
        
        Args:
            user_id: ID of the user who owns this conversation
            metadata: Optional metadata about the conversation
            
        Returns:
            Conversation ID
        """
        
        conversation_id = str(uuid.uuid4())
        
        try:
            # Create conversation document
            conversation_data = {
                'conversation_id': conversation_id,
                'user_id': user_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active',
                'message_count': 0
            }                
            # Save to Firestore
            doc_ref = self.db.collection('conversations').document(conversation_id)
            doc_ref.set(conversation_data)
            
            logger.info(f"Created conversation {conversation_id} for user {user_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error creating conversation: {str(e)}")
            raise
    
    async def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Get conversation data.
        
        Args:
            conversation_id: ID of the conversation to retrieve
            
        Returns:
            Conversation data dictionary or None if not found
        """
        try:
            # Get conversation document
            doc_ref = self.db.collection('conversations').document(conversation_id)
            doc = doc_ref.get()
            
            if doc.exists:
                conversation_data = doc.to_dict()
                logger.debug(f"Retrieved conversation {conversation_id}")
                return conversation_data
            else:
                logger.warning(f"Conversation {conversation_id} not found")
                return None
                
        except Exception as e:
            logger.error(f"Error retrieving conversation {conversation_id}: {str(e)}")
            return None
    
    async def update_conversation(self, conversation_id: str, data: Dict[str, Any]) -> bool:
        """
        Update conversation data.
        
        Args:
            conversation_id: ID of the conversation to update
            data: Data to update
            
        Returns:
            True if successful, False otherwise
        """
        
        try:
            # Add updated_at timestamp
            data['updated_at'] = firestore.SERVER_TIMESTAMP
            
            # Update conversation document
            doc_ref = self.db.collection('conversations').document(conversation_id)
            doc_ref.update(data)
            
            logger.debug(f"Updated conversation {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating conversation {conversation_id}: {str(e)}")
            return False
        
    async def add_message(self, conversation_id: str, message: Dict[str, Any]) -> str:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: ID of the conversation
            message: Message data (should include 'role', 'content', and optional 'metadata')
            
        Returns:
            Message ID
        """
        
        try:
            # Generate message ID
            message_id = str(uuid.uuid4())
            
            # Prepare message data
            message_data = {
                'message_id': message_id,
                'conversation_id': conversation_id,
                'created_at': firestore.SERVER_TIMESTAMP,
                'role': message.get('role', 'user'),  # default to user if not specified
                'content': message.get('content', ''),
            }
                            
            # Save message to Firestore
            message_ref = self.db.collection('conversations').document(conversation_id) \
                            .collection('messages').document(message_id)
            message_ref.set(message_data)
            
            # Check if the conversation document exists before updating it
            conversation_ref = self.db.collection('conversations').document(conversation_id)
            conversation_doc = conversation_ref.get()
            
            if conversation_doc.exists:
                # Update existing conversation document
                conversation_ref.update({
                    'message_count': firestore.Increment(1),
                    'last_message': {
                        'role': message_data['role'],
                        'content': message_data['content'][:100] + ('...' if len(message_data['content']) > 100 else ''),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    },
                    'updated_at': firestore.SERVER_TIMESTAMP
                })
            else:
                # Create a new conversation document if it doesn't exist
                conversation_data = {
                    'conversation_id': conversation_id,
                    'user_id': 'system',  # Default user ID if not provided
                    'created_at': firestore.SERVER_TIMESTAMP,
                    'updated_at': firestore.SERVER_TIMESTAMP,
                    'status': 'active',
                    'message_count': 1,
                    'last_message': {
                        'role': message_data['role'],
                        'content': message_data['content'][:100] + ('...' if len(message_data['content']) > 100 else ''),
                        'timestamp': firestore.SERVER_TIMESTAMP
                    }
                }
                conversation_ref.set(conversation_data)
            
            logger.debug(f"Added message {message_id} to conversation {conversation_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
            raise
    
    async def get_messages(self, conversation_id: str, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: ID of the conversation
            limit: Maximum number of messages to retrieve
            offset: Number of messages to skip
            
        Returns:
            List of message dictionaries
        """
        try:
            # Query messages
            query = self.db.collection('conversations').document(conversation_id) \
                       .collection('messages') \
                       .order_by('created_at', direction=firestore.Query.DESCENDING) \
                       .limit(limit).offset(offset)
                       
            # Execute query
            docs = query.get()
            
            # Convert to list of dictionaries
            messages = [doc.to_dict() for doc in docs]
            messages.reverse()
            
            logger.debug(f"Retrieved {len(messages)} messages from conversation {conversation_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error retrieving messages from conversation {conversation_id}: {str(e)}")
            return []
                    
    async def list_agents(self, limit: int = 50, offset: int = 0, userId: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all agent configurations.
        
        Args:
            limit: Maximum number of agents to retrieve
            offset: Number of agents to skip
            userId: Optional user ID to filter agents by owner
            
        Returns:
            List of agent configuration dictionaries
        """
        if not hasattr(self, 'db'):
            logger.warning("Firestore DB not initialized")
            return []
            
        try:
            # Query agents
            query = self.db.collection('alchemist_agents')
            
            # Filter by userId if provided
            if userId:
                query = query.where('userId', '==', userId)
                
            query = query.order_by('created_at', direction=firestore.Query.DESCENDING) \
                .limit(limit).offset(offset)
            
            # Execute query
            docs = query.get()
            
            # Convert to list of dictionaries
            agents = []
            for doc in docs:
                agent_data = doc.to_dict()
                
                # Include the document ID if not already present
                if 'agent_id' not in agent_data:
                    agent_data['agent_id'] = doc.id
                
                # Filter out large fields if needed
                for key, value in list(agent_data.items()):
                    if isinstance(value, dict) and len(str(value)) > 1000:
                        agent_data[key] = f"<large {key} object>"
                
                agents.append(agent_data)
            
            logger.info(f"Retrieved {len(agents)} agents from Firestore")
            return agents
        
        except Exception as e:
            logger.error(f"Error listing agents: {str(e)}")
            return []
                
    async def update_agent_config(self, agent_id: str, config_updates: Dict[str, Any]) -> bool:
        """
        Update an existing agent configuration.
        
        Args:
            agent_id: ID of the agent to update
            config_updates: Configuration updates to apply
            
        Returns:
            True if successful, False otherwise
        """

        try:
            # Add updated_at timestamp
            config_updates['updated_at'] = firestore.SERVER_TIMESTAMP
            print(f"Updating agent config {agent_id} with {config_updates}")
            
            # Update agent document
            agent_ref = self.db.collection('alchemist_agents').document(agent_id)
            agent_ref.update(config_updates)
            
            logger.debug(f"Updated agent config {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating agent config {agent_id}: {str(e)}")
            return False
                        
# Create default storage service with *local* persistence by default. To use
# StorageService.
default_storage = StorageService()
