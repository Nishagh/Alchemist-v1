"""
Orchestrator Agent Module

This module contains the OrchestratorAgent class that serves as the main Alchemist agent,
coordinating all interactions with users and delegating tasks to specialized agents.
"""
import logging
import json
import asyncio
import os
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import BaseTool, tool, Tool
from langchain_core.messages import AIMessage, HumanMessage

from alchemist_shared.database.firebase_client import FirebaseClient
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.constants.collections import Collections
from alchemist_shared.models.agent_models import Agent
from alchemist_shared.models.base_models import TimestampedModel
from services.openai_service import default_openai_service

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import requests
from urllib.parse import urljoin
from knowledge_base_tool import get_knowledge_base_tools
from mcp_tool import get_mcp_tools_sync


load_dotenv()

logger = logging.getLogger(__name__)

def get_system_prompt(agent_id: str) -> str:
    """Get system prompt from agent document in Firestore."""
    firebase_client = FirebaseClient()
    agent_doc_ref = firebase_client.get_collection(Collections.AGENTS).document(agent_id)
    agent_doc = agent_doc_ref.get()
    
    if not agent_doc.exists:
        raise ValueError(f"Agent {agent_id} not found")
        
    agent_data = agent_doc.to_dict()
    
    # Try different field names for system prompt
    system_prompt = agent_data.get('system_prompt') or agent_data.get('prompt') or agent_data.get('description', '')
    if not system_prompt:
        logger.warning(f"No system prompt found for agent {agent_id}, using default")
        system_prompt = "You are a helpful AI assistant."
    
    return system_prompt

def get_messages(agent_id: str, conversation_id: str) -> List[Dict[str, Any]]:
    """Get conversation messages from Firestore."""
    firebase_client = FirebaseClient()
    
    # Get messages from conversations collection
    messages_query = firebase_client.db.collection(Collections.CONVERSATIONS)\
        .document(conversation_id)\
        .collection('messages')\
        .order_by('timestamp')
    
    messages_list = []
    for message_doc in messages_query.stream():
        message_data = message_doc.to_dict()
        messages_list.append(message_data)
    
    return messages_list

def get_mcp_server(agent_id: str) -> Optional[str]:
    """Get MCP server URL from mcp_servers collection and fallback to standard format."""
    firebase_client = FirebaseClient()
    
    try:
        # First, try to get MCP server info from mcp_servers collection
        mcp_doc_ref = firebase_client.get_collection(Collections.MCP_SERVERS).document(agent_id)
        mcp_doc = mcp_doc_ref.get()
        
        if mcp_doc.exists:
            mcp_data = mcp_doc.to_dict()
            
            # Check for service URL in MCP deployment document
            if 'service_url' in mcp_data:
                logger.info(f"Found MCP server URL in mcp_servers collection: {mcp_data['service_url']}")
                return mcp_data['service_url']
            
            # Check for deployment status and construct URL if deployed
            if mcp_data.get('status') == 'deployed' or mcp_data.get('deployment_status') == 'deployed':
                # Use the standard MCP server URL format
                mcp_url = f"https://mcp-{agent_id}-851487020021.us-central1.run.app"
                logger.info(f"MCP server marked as deployed, using standard URL format: {mcp_url}")
                return mcp_url
        
        # Fallback: Check if there's an active MCP deployment for this agent
        # by trying the standard URL format
        mcp_url = f"https://mcp-{agent_id}-851487020021.us-central1.run.app"
        logger.info(f"No MCP server document found, trying standard URL format: {mcp_url}")
        return mcp_url
        
    except Exception as e:
        logger.error(f"Error retrieving MCP server info for agent {agent_id}: {e}")
        
        # Final fallback: use standard format
        mcp_url = f"https://mcp-{agent_id}-851487020021.us-central1.run.app"
        logger.info(f"Error occurred, falling back to standard URL format: {mcp_url}")
        return mcp_url


class UserAgent():
    """
    Main Alchemist agent that coordinates all user interactions and delegates tasks to specialized agents.
    
    This agent analyzes user requests, delegates specific tasks to specialized agents,
    and manages the overall process of creating AI agents for the user.
    
    This implementation uses a conversation-centric model rather than maintaining agent state,
    allowing for better scalability and handling of multiple simultaneous users.
    """
    
    def __init__(self, agent_id: str, conversation_id: str):
        """
        Initialize the Orchestrator agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for the agent
        """
        # Get config from alchemist-shared settings
        self.settings = BaseSettings()
        self.openai_api_key = self.settings.openai_api_key
        self.model = self.settings.openai_model or os.getenv('AGENT_MODEL', 'gpt-4')
        
        # Log configuration info for debugging
        logger.info(f"Agent initialization - Using OpenAI key ending: ...{self.openai_api_key[-4:] if self.openai_api_key else 'None'}")
        logger.info(f"Agent initialization - Using model: {self.model}")
        
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.firebase_client = FirebaseClient()
        self.mcp_server = None
        self.init_langchain()        
        
    def init_langchain(self):
        """Initialize the LangChain agent with tools for specialized agents."""
        try:
            # Validate the API key
            if not self.openai_api_key:
                logger.warning("OpenAI API key is missing. LangChain initialization will fail.")
                raise ValueError("OpenAI API key is required for LangChain initialization")
            
            # Force use of alchemist-shared OpenAI API key
            os.environ['OPENAI_API_KEY'] = self.openai_api_key
            logger.info(f"✅ Set environment OPENAI_API_KEY from alchemist-shared (ending: ...{self.openai_api_key[-4:] if self.openai_api_key else 'None'})")
            
            # Verify the key is properly set
            verify_key = os.getenv('OPENAI_API_KEY')
            if verify_key != self.openai_api_key:
                logger.warning(f"⚠️  Environment key mismatch after setting: {verify_key[-4:] if verify_key else 'None'} vs {self.openai_api_key[-4:] if self.openai_api_key else 'None'}")
            else:
                logger.info(f"✅ Environment key verification successful")
            
            self.llm = init_chat_model(self.model, model_provider="openai")            
            # Test the LLM connection
            logger.info(f"Testing connection to OpenAI with model {self.model}")
            
            # Create tools for all specialized agent types
            self.tools = self.create_agent_tools()
            
            system_prompt = get_system_prompt(self.agent_id)
            
            # Create prompt template
            self.prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent with tools
            logger.info(f"Creating OpenAI tools agent with {len(self.tools)} tools")
            self.agent = create_openai_tools_agent(
                self.llm,
                self.tools,
                self.prompt
            )
            
            if not self.agent:
                raise ValueError("Failed to create LangChain agent")
            
            # Create agent executor
            logger.info("Creating AgentExecutor")
            self.agent_executor = AgentExecutor(
                agent=self.agent,
                tools=self.tools,
                verbose=True,
                max_iterations=25,
                return_intermediate_steps=True  # Set this at initialization
            )
            
            if not self.agent_executor:
                raise ValueError("Failed to create AgentExecutor")
                
            logger.info("Orchestrator agent initialized successfully.")
        
        except Exception as e:
            logger.error(f"Error initializing LangChain agent: {str(e)}")
            # Make sure we set these to None so we can check their status
            self.agent_executor = None
            self.agent = None
    
    def create_agent_tools(self) -> List[BaseTool]:
        """Create tools for all specialized agent types."""
        tools = []
        
        # Add knowledge base tools
        kb_tools = get_knowledge_base_tools(agent_id=self.agent_id)
        tools.extend(kb_tools)

        mcp_server_url = get_mcp_server(self.agent_id)
        if mcp_server_url is not None:
            # Add MCP server tools
            try:
                logger.info(f"🔗 Integrating MCP server: {mcp_server_url}")
                mcp_tools = get_mcp_tools_sync(mcp_server_url)
                tools.extend(mcp_tools)
                logger.info(f"✅ Successfully integrated {len(mcp_tools)} MCP tools")
            except Exception as e:
                logger.error(f"❌ Failed to integrate MCP server {mcp_server_url}: {str(e)}")
                # Continue without MCP tools if there's an error
        
        return tools
    
    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process the input data using LangChain for orchestration.
        
        Args:
            input_data: Dictionary containing input data
                - input: The user message to process
                
        Returns:
            Dictionary containing the response
        """
        
        try:
            input_text = input_data.get('message', '')
            chat_history = []
            
            conversation_messages = get_messages(agent_id=self.agent_id, conversation_id=self.conversation_id)
            for msg in conversation_messages:
                if msg['role'] == 'user':
                    chat_history.append(HumanMessage(content=msg['content']))
                elif msg['role'] == 'assistant':
                    chat_history.append(AIMessage(content=msg['content']))       
                
            # Execute the LangChain agent with the user message
            invoke_input = {
                "input": input_text,
                "chat_history": chat_history,
            }
            print("invoke_input: ", invoke_input)
            
            # Execute the agent with the enhanced context
            try:
                # Try the new API approach (return_intermediate_steps set at initialization)
                result = await self.agent_executor.ainvoke(invoke_input)
                
                # Extract response and intermediate steps from the result
                response = result.get('output', '')
            except Exception as e:
                logger.error(f"Error processing input: {str(e)}", exc_info=True)
                return {
                    'status': 'error',
                    'message': f'Error processing input: {str(e)}',
                    'conversation_id': self.conversation_id
                }
                
            return {
                'status': 'success',
                'response': response,
                'conversation_id': self.conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error processing input: {str(e)}',
                'conversation_id': self.conversation_id
            }