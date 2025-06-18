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

from services.openai_init import get_openai_service, initialize_openai
from services.openai_service import default_openai_service
from services.firebase_service import get_conversation_repository

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import requests
from urllib.parse import urljoin
from knowledge_base_tool import get_knowledge_base_tools
from mcp_tool import get_mcp_tools_sync


load_dotenv()

logger = logging.getLogger(__name__)

def get_system_prompt(agent_id: str):
    from services.firebase_service import get_firestore_service
    firestore_service = get_firestore_service()
    agent_doc = firestore_service.collection('alchemist_agents').document(agent_id).get().to_dict()
    system_prompt = agent_doc['system_prompt']
    return system_prompt

def get_messages(agent_id: str, conversation_id: str):
    repo = get_conversation_repository()
    messages = repo.get_messages(agent_id, conversation_id)
    messages_list = []
    for message in messages:
        messages_list.append(message.to_dict())
    # Reverse to maintain descending order (newest first) as in original implementation
    return list(reversed(messages_list))

def get_mcp_server(agent_id: str):
    from services.firebase_service import get_firestore_service
    firestore_service = get_firestore_service()
    mcp_url = None
    agent_ref = firestore_service.collection('alchemist_agents').document(agent_id).get()
    if agent_ref.exists:
        agent_doc = agent_ref.to_dict()
        if 'api_integration' in agent_doc.keys():
            if 'service_url' in agent_doc['api_integration'].keys():
                mcp_url = agent_doc['api_integration']['service_url']
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
        # Get config with defaults
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('AGENT_MODEL')   
        self.agent_id = agent_id
        self.conversation_id = conversation_id
        self.mcp_server = None
        self.init_langchain()        
        
    def init_langchain(self):
        """Initialize the LangChain agent with tools for specialized agents."""
        try:
            # Validate the API key using the service
            if not default_openai_service.validate_api_key():
                logger.warning("OpenAI API key is missing. LangChain initialization will fail.")
                raise ValueError("OpenAI API key is required for LangChain initialization")
            
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