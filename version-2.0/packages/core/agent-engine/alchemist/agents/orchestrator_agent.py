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

from ..services.openai_service import default_openai_service
from ..services.storage_service import default_storage

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
import requests
from urllib.parse import urljoin

# Import GNF integration
try:
    from alchemist_shared.services.gnf_adapter import (
        create_gnf_adapter, 
        AgentIdentityData, 
        InteractionData, 
        InteractionType,
        track_conversation_interaction
    )
    from alchemist_shared.database.firebase_client import get_firestore_client
    from alchemist_shared.constants.workflow_states import (
        DeploymentStatus, 
        is_success_status,
        normalize_status
    )
    GNF_AVAILABLE = True
except ImportError as e:
    logging.warning(f"GNF integration not available: {e}")
    GNF_AVAILABLE = False

# Import epistemic autonomy services
try:
    from alchemist_shared.services import (
        get_story_loss_calculator, get_gnf_service, get_minion_coordinator,
        get_alert_service
    )
    EPISTEMIC_SERVICES_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Epistemic autonomy services not available: {e}")
    EPISTEMIC_SERVICES_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

def get_system_prompt(agent_config: Optional[Dict[str, Any]] = None) -> str:
    """Generate context-aware system prompt based on agent configuration."""
    
    # Check if agent already exists and has a name
    if agent_config and agent_config.get('name'):
        agent_name = agent_config.get('name')
        agent_description = agent_config.get('description', '')
        
        return f"""You are the main Alchemist AI orchestrator working with an existing agent named "{agent_name}".

**Current Agent Information:**
- Name: {agent_name}
- Description: {agent_description}

**Your Role:**
You can help users interact with and modify their existing agent. You can:
1. Update the agent's configuration (name, description, etc.)
2. Modify the agent's system prompt to change its behavior
3. Answer questions about the agent
4. Help refine the agent's capabilities

**Available Tools:**
- update_agent_prompt: Update the agent's system prompt to change its behavior
- update_agent_name: Change the agent's name

**Communication Style:**
- Be conversational and helpful
- Ask clarifying questions when needed
- Provide clear explanations of what you're doing
- Focus on helping the user achieve their goals with their agent

Since the agent already exists, you should engage in normal conversation and help the user with their requests rather than starting the agent creation process."""
    
    else:
        # Original prompt for new agent creation
        return """You are the main Alchemist AI orchestrator that builds AI agents for users in four stages:
1. requirements – gather and clarify user needs for the AI agent
2. update_agent_prompt – update the agent's system prompt to incorporate the requirements gathered so far.

**Requirement Categories to Cover:**
- **Basic Information**: Agent name, purpose, target audience, use cases, core capabilities, interaction style, response format

**STAGE PROGRESSION RULES:**

**Requirements Stage:**
- Ask ONLY ONE QUESTION per message to ensure focused, quality responses
- After receiving EVERY user response, immediately call update_agent_prompt to incorporate the new information
- Gather requirements systematically, one field at a time
- Update the agent prompt incrementally as you learn more about user needs

**Available Tools:**
- update_agent_prompt: Update agent system prompt to incorporate the requirements gathered so far. CALL THIS AFTER EVERY USER RESPONSE.

**Incremental Building Process:**
1. **Requirements**: Ask one focused question about user requirements
2. Receive user response and immediately call update_agent_prompt with the new information
3. Ask the next question to gather more details
4. Repeat until basic agent information is complete

**Communication Style:**
- Ask exactly ONE focused question per message
- Wait for user response before asking the next question
- After each response, update the agent prompt with new information
- Build understanding systematically, field by field
- Ensure each field has sufficient detail before moving to next

Your primary role is to manage the entire process of creating AI agents with thorough requirements gathering using one question at a time.
"""

class OrchestratorAgent():
    """
    Main Alchemist agent that coordinates all user interactions and delegates tasks to specialized agents.
    
    This agent analyzes user requests, delegates specific tasks to specialized agents,
    and manages the overall process of creating AI agents for the user.
    
    This implementation uses a conversation-centric model rather than maintaining agent state,
    allowing for better scalability and handling of multiple simultaneous users.
    """
    
    def __init__(self, agent_id: str):
        """
        Initialize the Orchestrator agent.
        
        Args:
            agent_id: Unique identifier for the agent
            config: Configuration dictionary for the agent
        """
        # Get config with defaults
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.model = os.getenv('ALCHEMIST_MODEL')   
        self.agent_id = agent_id
        self.current_user_id = None  # Will be set during processing
        
        # Initialize GNF integration
        self.gnf_adapter = None
        self._gnf_identity_created = False
        
        if GNF_AVAILABLE:
            try:
                gnf_service_url = os.getenv('GNF_SERVICE_URL', 'http://localhost:8000')
                firebase_client = get_firestore_client()
                
                self.gnf_adapter = create_gnf_adapter(
                    service_url=gnf_service_url,
                    firebase_client=firebase_client
                )
                # Note: GNF adapter will be initialized asynchronously when first used
                logger.info(f"GNF adapter created for agent {agent_id}")
            except Exception as e:
                logger.warning(f"Failed to create GNF adapter: {e}")
                self.gnf_adapter = None
        
        self.init_langchain()
        
    def init_langchain(self):
        """Initialize the LangChain agent with tools for specialized agents."""
        try:
            # Validate the API key using the service
            if not default_openai_service.validate_api_key():
                logger.warning("OpenAI API key is missing. LangChain initialization will fail.")
                raise ValueError("OpenAI API key is required for LangChain initialization")
            
            self.llm = init_chat_model(model=self.model, model_provider="openai")            
            # Test the LLM connection
            logger.info(f"Testing connection to OpenAI with model {self.model}")
            
            # Create tools for all specialized agent types
            self.tools = self.create_agent_tools()
            
            # Create base prompt template (will be updated dynamically)
            self.prompt_template = ChatPromptTemplate.from_messages([
                ("system", "{system_prompt}"),
                MessagesPlaceholder(variable_name="chat_history"),
                ("human", "{input}"),
                MessagesPlaceholder(variable_name="agent_scratchpad"),
            ])
            
            # Create agent with tools (using default prompt for now)
            logger.info(f"Creating OpenAI tools agent with {len(self.tools)} tools")
            default_prompt = self.prompt_template.partial(system_prompt=get_system_prompt())
            self.agent = create_openai_tools_agent(
                self.llm,
                self.tools,
                default_prompt
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
        # Add tool for updating agent prompt using prompt engineer API
        def update_agent_prompt(instructions: str) -> str:
            """Update an agent's system prompt using the prompt engineer API.
            
            Args:
                input_json: JSON string containing agent_id and instructions
                
            Returns:
                A user-friendly message describing the result of the prompt update
            """
            import requests
            import os
            
            try:
                if not instructions:
                    return "Missing instructions in your request. Please specify what changes you want to make to the prompt."
                
                # Get the prompt engineer API URL from environment variables
                prompt_engineer_api_url = os.environ.get('PROMPT_ENGINEER_API_URL')
                if not prompt_engineer_api_url:
                    return "Prompt engineer API URL is not configured. Please check your environment variables."
                
                # Construct the endpoint URL
                endpoint = f"{prompt_engineer_api_url}/api/prompt-engineer/prompt"
                
                # Prepare the request payload
                payload = {
                    'agent_id': self.agent_id,
                    'instructions': instructions,
                    'user_id': self.current_user_id  # Include user_id for lifecycle tracking
                }
                
                # Make the API request
                response = requests.post(endpoint, json=payload)
                
                # Check the response
                if response.status_code == 200:
                    response_data = response.json()
                    return f"Successfully updated the system prompt for agent ID: {self.agent_id}. {response_data.get('message', '')}"
                else:
                    error_message = f"Failed to update prompt. Status code: {response.status_code}"
                    try:
                        response_data = response.json()
                        if 'error' in response_data:
                            error_message += f". Error: {response_data['error']}"
                    except:
                        pass
                    return error_message
                    
            except json.JSONDecodeError:
                return "Invalid JSON input. Please provide a valid JSON with agent_id and instructions fields."
            except Exception as e:
                logger.error(f"Error updating agent prompt: {str(e)}", exc_info=True)
                return f"An error occurred while updating the agent prompt: {str(e)}"
        
        # Register the update_agent_prompt tool
        tools.append(
            Tool(
                name="update_agent_prompt",
                description="Update an agent's system prompt using the prompt engineer API. Provide agent_id and instructions in JSON format.",
                func=update_agent_prompt
            )
        )
        
        def update_agent_name(name: str) -> str:
            """Update the name of the agent."""
            import asyncio
            
            async def _update_name():
                print(f"Updating agent name to {name}")
                await default_storage.update_agent_config(self.agent_id, {'name': name})
                return f"Successfully updated the name of the agent to {name}."
            
            # Run the async function synchronously
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(_update_name())
                return result
            finally:
                loop.close()
        
        tools.append(
            Tool(
                name="update_agent_name",
                description="Update the name of the agent.",
                func=update_agent_name
            )
        )
        return tools
    
    async def _ensure_gnf_identity(self, agent_config: Dict[str, Any]) -> bool:
        """
        Ensure GNF identity exists for this agent.
        
        Args:
            agent_config: Agent configuration from storage
            
        Returns:
            True if identity exists or was created successfully
        """
        if not self.gnf_adapter or self._gnf_identity_created:
            return self._gnf_identity_created
        
        try:
            # Initialize GNF adapter if not already done
            if not self.gnf_adapter.session:
                await self.gnf_adapter.initialize()
            
            # Check if identity already exists
            existing_identity = await self.gnf_adapter.get_agent_identity(self.agent_id)
            
            if existing_identity:
                self._gnf_identity_created = True
                logger.info(f"Found existing GNF identity for agent {self.agent_id}")
                return True
            
            # Create new identity
            if agent_config:
                identity_data = AgentIdentityData(
                    agent_id=self.agent_id,
                    name=agent_config.get('name', f'Agent-{self.agent_id}'),
                    personality={
                        'traits': ['helpful', 'responsive', 'analytical'],
                        'values': ['efficiency', 'accuracy', 'user_satisfaction'],
                        'goals': ['assist users effectively', 'provide accurate information'],
                        'motivations': ['learning', 'problem_solving', 'helping others']
                    },
                    capabilities={
                        'knowledge_domains': [agent_config.get('domain', 'general')],
                        'skills': ['conversation', 'analysis', 'problem_solving'],
                        'use_cases': agent_config.get('use_cases', []),
                        'limitations': ['requires clear instructions', 'limited by training data']
                    },
                    background={
                        'origin': f"Created as {agent_config.get('name', 'Assistant')} on Alchemist platform",
                        'creation_date': datetime.utcnow().isoformat(),
                        'purpose': agent_config.get('description', 'General assistance'),
                        'specialization': agent_config.get('domain', 'general')
                    }
                )
                
                identity_id = await self.gnf_adapter.create_agent_identity(identity_data)
                
                if identity_id:
                    self._gnf_identity_created = True
                    logger.info(f"Created GNF identity {identity_id} for agent {self.agent_id}")
                    
                    # Update agent config with identity reference
                    await default_storage.update_agent_config(self.agent_id, {
                        'narrative_identity_id': identity_id,
                        'gnf_enabled': True,
                        'last_gnf_sync': datetime.utcnow().isoformat()
                    })
                    
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Failed to ensure GNF identity for agent {self.agent_id}: {e}")
            return False
    
    async def _track_conversation_interaction(self, user_message: str, agent_response: str, 
                                            context: Optional[Dict[str, Any]] = None) -> None:
        """
        Track conversation interaction in GNF.
        
        Args:
            user_message: User's input message
            agent_response: Agent's response
            context: Optional conversation context
        """
        if not self.gnf_adapter or not self._gnf_identity_created:
            return
        
        try:
            # Initialize GNF adapter if not already done
            if not self.gnf_adapter.session:
                await self.gnf_adapter.initialize()
            
            # Prepare interaction context
            interaction_context = {
                'conversation_type': 'agent_creation',
                'platform': 'alchemist',
                'model': self.model,
                **(context or {})
            }
            
            # Track the interaction
            await track_conversation_interaction(
                adapter=self.gnf_adapter,
                agent_id=self.agent_id,
                user_message=user_message,
                agent_response=agent_response,
                context=interaction_context
            )
            
            logger.debug(f"Tracked conversation interaction for agent {self.agent_id}")
            
        except Exception as e:
            logger.warning(f"Failed to track conversation interaction: {e}")
    
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
            agent_id = input_data.get('agent_id', '')
            user_id = input_data.get('user_id', '')
            
            # Store user_id for use in tools
            self.current_user_id = user_id
            
            agent_config = await default_storage.get_agent_config(agent_id)
            
            # Ensure GNF identity exists for this agent
            await self._ensure_gnf_identity(agent_config)
            
            # Get conversation history from storage if we have a conversation ID
            chat_history = []
            
            if agent_id:
                # Fetch recent messages to build context
                conversation_messages = await default_storage.get_messages(
                    conversation_id=agent_id,
                )
                print("Orchestrator conversation_messages: ", len(conversation_messages))
                
                # Convert to LangChain format
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
            
            # Include agent context information if available
            if agent_config:
                # Add a prefix to the input to explicitly tell the model which agent we're working with
                agent_name = agent_config.get('name', '')
                agent_id = agent_config.get('agent_id', '')
                agent_type = agent_config.get('agent_type', agent_config.get('type', ''))
                
                # Modify the input to include agent information
                if agent_name and agent_id:
                    prefix = f"I am working with the agent: {agent_name} (ID: {agent_id}, Type: {agent_type}).\n\n"
                    invoke_input["input"] = prefix + input_text
                    
                # Also pass the agent_config as a separate parameter
                invoke_input["current_agent"] = {
                    "name": agent_name,
                    "id": agent_id,
                    "type": agent_type,
                    "config": agent_config
                }
                
            
            # Prepare the chat history in the format expected by the prompt
            formatted_chat_history = []
            if chat_history:
                for message in chat_history:
                    # Check if message is already a LangChain message object
                    if isinstance(message, (HumanMessage, AIMessage)):
                        formatted_chat_history.append(message)
                    # Otherwise, assume it's a dictionary and convert appropriately
                    elif isinstance(message, dict):
                        role = message.get('role', '')
                        content = message.get('content', '')
                        if role == 'user':
                            formatted_chat_history.append(HumanMessage(content=content))
                        elif role == 'assistant':
                            formatted_chat_history.append(AIMessage(content=content))
                    # If it's some other type, try to convert it to a string
                    else:
                        try:
                            formatted_chat_history.append(HumanMessage(content=str(message)))
                        except:
                            # Skip any messages that can't be converted
                            pass
            
            # Prepare additional context about current agent if available
            invoke_params = {
                "input": input_text,  # Direct variable name as expected by prompt
                "chat_history": formatted_chat_history,  # Formatted as expected by prompt
                "current_agent": None  # Initialize as None
            }
            
            # Add agent_config context if available
            if agent_config:
                invoke_params["current_agent"] = {
                    "id": agent_id,
                    "name": agent_config.get("name", ""),
                    "type": agent_config.get("agent_type", agent_config.get("type", "")),
                    "description": agent_config.get("description", "")
                }
                
            print("invoke_params: ", invoke_params)
            
            # Create context-aware agent with appropriate prompt
            context_prompt = self.prompt_template.partial(system_prompt=get_system_prompt(agent_config))
            context_agent = create_openai_tools_agent(
                self.llm,
                self.tools,
                context_prompt
            )
            
            # Create temporary agent executor with context-aware agent
            context_executor = AgentExecutor(
                agent=context_agent,
                tools=self.tools,
                verbose=True,
                max_iterations=25,
                return_intermediate_steps=True
            )
            
            # Execute the agent with the enhanced context
            try:
                # Try the new API approach (return_intermediate_steps set at initialization)
                result = await context_executor.ainvoke(invoke_params)
                
                # Extract response and intermediate steps from the result
                response = result.get('output', '')
                steps = result.get('intermediate_steps', [])
            except TypeError as e:
                logger.warning(f"Using fallback for LangChain compatibility: {str(e)}")
                # Fallback: execute without expecting intermediate steps
                response = await context_executor.ainvoke(invoke_params)
                steps = []
            
            # Modify the response if it contains raw tool output
            response = self._format_response_for_user(response, steps)
            
            # Track interaction in GNF
            await self._track_conversation_interaction(
                user_message=input_text,
                agent_response=response,
                context={
                    'conversation_id': agent_id,
                    'agent_config': agent_config,
                    'steps_taken': len(steps) if steps else 0
                }
            )
            
            # Epistemic autonomy: Story-loss monitoring
            if EPISTEMIC_SERVICES_AVAILABLE and agent_id:
                try:
                    # Calculate story-loss after the interaction
                    story_loss_calculator = get_story_loss_calculator()
                    gnf_service = get_gnf_service()
                    
                    # Get current agent graph
                    agent_graph = await gnf_service.get_agent_graph(agent_id)
                    if agent_graph:
                        # Calculate current story-loss
                        story_loss = await story_loss_calculator.calculate_story_loss(
                            agent_id=agent_id,
                            new_edges=[],  # No new edges to evaluate in this context
                            current_nodes=agent_graph.nodes,
                            current_edges=agent_graph.edges
                        )
                        
                        logger.info(f"Agent {agent_id} story-loss: {story_loss}")
                        
                        # Check if story-loss exceeds threshold
                        STORY_LOSS_THRESHOLD = 0.15
                        if story_loss > STORY_LOSS_THRESHOLD:
                            logger.warning(f"Agent {agent_id} story-loss threshold exceeded: {story_loss}")
                            
                            # Trigger self-reflection minion
                            minion_coordinator = get_minion_coordinator()
                            await minion_coordinator.trigger_self_reflection(
                                agent_id=agent_id,
                                story_loss=story_loss,
                                context={
                                    "interaction_type": "conversation",
                                    "user_message": input_text,
                                    "agent_response": response,
                                    "timestamp": datetime.now().isoformat()
                                }
                            )
                            
                            # Create alert for threshold exceedance
                            alert_service = get_alert_service()
                            await alert_service.create_alert(
                                rule_id="story_loss_threshold",
                                agent_id=agent_id,
                                alert_type="story_loss_threshold",
                                severity="warning",
                                title=f"Story-Loss Threshold Exceeded",
                                description=f"Agent story-loss {story_loss:.3f} exceeds threshold {STORY_LOSS_THRESHOLD}",
                                event_data={
                                    "story_loss": story_loss,
                                    "threshold": STORY_LOSS_THRESHOLD,
                                    "interaction_context": {
                                        "user_message": input_text[:200],  # Truncate for storage
                                        "response_length": len(response)
                                    }
                                }
                            )
                except Exception as e:
                    logger.error(f"Story-loss monitoring failed for agent {agent_id}: {e}")
                    # Continue execution - don't fail conversation due to monitoring errors
            
            # Update the conversation with the new message
            if agent_id:
                message_to_add = {
                    'role': 'assistant',
                    'content': response,
                }
                
            return {
                'status': 'success',
                'response': response,
                'message_to_add': message_to_add,
                'conversation_id': agent_id
            }
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'message': f'Error processing input: {str(e)}',
                'conversation_id': agent_id
            }
    
    async def _get_agent_state(self) -> Dict[str, Any]:
        """Get agent-specific state for serialization."""
        # In the conversation-centric model, we store minimal state
        # Most state is stored in the conversation context
        return {
            'agent_id': self.agent_id,
            'conversation_id': self.conversation_id,
            'model': self.model,
            'temperature': self.temperature
        }
    
    async def _set_agent_state(self, state: Dict[str, Any]) -> None:
        """Set agent-specific state from deserialized data."""
        # Set conversation ID if present
        if 'conversation_id' in state:
            self.conversation_id = state['conversation_id']
            
        # Update model and temperature if present
        if 'model' in state:
            self.model = state['model']
            
        if 'temperature' in state:
            self.temperature = state['temperature']
            
        # Update OpenAI configuration if present
        if 'openai_api_key' in state and state['openai_api_key']:
            default_openai_service.api_key = state['openai_api_key']
            
        # Reinitialize LangChain
        self.init_langchain()
    
    def _format_response_for_user(self, response: str, steps: list = None) -> str:
        """Format the response in a conversational way for the user.
        
        This method ensures tool outputs are presented in a friendly, conversational tone
        rather than showing raw JSON or technical responses directly to the user.
        
        Args:
            response: The raw response from the agent
            steps: The steps taken by the agent (including tool calls)
            
        Returns:
            A user-friendly response with proper conversational tone
        """
        # If no steps were taken, return the response as is
        if not steps:
            return self._ensure_proper_formatting(response)
            
        # Check if response seems to be a raw tool output or JSON
        if response and (response.strip().startswith('{') or 'Sentinel: Value used to set a document field' in response):
            # Get the last tool used
            last_tool = steps[-1][0].tool if steps else None
            last_output = str(steps[-1][1]) if steps else ""
            
            # Format based on the tool used
            if last_tool == "finalise_project":
                return "I've successfully finalized your project and saved all the configurations. Your agent is now ready to use."
                
            elif last_tool == "requirements":
                # Handle requirements agent responses
                try:
                    if last_output.strip().startswith('{'):
                        data = json.loads(last_output)
                        if data.get('status') == 'success':
                            return data.get("response", "I've processed your requirements successfully.")
                        elif data.get('status') == 'error':
                            return f"I encountered an issue with requirements gathering: {data.get('message', 'Unknown error')}"
                    # If not JSON, return the output directly
                    return self._ensure_proper_formatting(last_output)
                except Exception:
                    return self._ensure_proper_formatting(last_output)
                    
            elif last_tool == "finalize_requirements":
                return "I've successfully finalized and saved all the requirements we've gathered. We're now ready to move to the next stage of agent design."
                
            elif last_tool == "modify_agent_config":
                # Extract agent ID if present in the output
                agent_id = ""
                try:
                    if last_output.strip().startswith('{'):
                        data = json.loads(last_output)
                        agent_id = data.get('agent_id', '')
                except:
                    pass
                    
                if agent_id:
                    return f"I've updated your agent configuration (ID: {agent_id}) with the requirements you specified."
                else:
                    return "I've updated your agent configuration with the requirements you specified."
                    
            elif last_tool == "check_config_status":
                # Handle config status responses - these are already formatted for users
                return self._ensure_proper_formatting(last_output)
                
            elif last_tool == "get_config_file":
                # Handle config file display
                try:
                    # Check if it's JSON and format it nicely
                    if last_output.strip().startswith('{'):
                        config_data = json.loads(last_output)
                        formatted_config = json.dumps(config_data, indent=2)
                        return f"Here's your current config file:\n\n```json\n{formatted_config}\n```"
                    else:
                        return f"Config file:\n{last_output}"
                except:
                    return f"Config file: {last_output}"
                    
            elif last_tool == "save_config_file":
                # Handle config file save responses - these are already formatted
                return self._ensure_proper_formatting(last_output)
            
            # For other tools, check if the response is JSON and extract meaning
            try:
                if response.strip().startswith('{'):
                    data = json.loads(response)
                    
                    # Look for meaningful fields
                    message = data.get('message', '')
                    error = data.get('error', '')
                    status = data.get('status', '')
                    
                    if error:
                        return f"I encountered a problem: {error}"
                    elif message and not message.strip().startswith('{'):
                        return self._ensure_proper_formatting(message)
                    elif is_success_status(status):
                        return "I've successfully completed the requested operation."
            except:
                # If we can't parse JSON or another error, fall back to a default message
                pass
                
            # Default response if we couldn't parse or format
            return "I've processed your request successfully."
        
        # For non-raw responses, apply formatting
        return self._ensure_proper_formatting(response)
        
    def _ensure_proper_formatting(self, text: str) -> str:
        """Ensure text has proper formatting for frontend display.
        
        This method converts standard line breaks and lists to proper markdown
        format to ensure they display correctly in the frontend.
        
        Args:
            text: The text to format
            
        Returns:
            Properly formatted text
        """
        if not text:
            return text
            
        # Replace consecutive line breaks with markdown double line breaks
        text = text.replace('\n\n', '\n\n')
        
        # Format numbered lists - identify patterns like "1. ", "2. ", etc.
        lines = text.split('\n')
        formatted_lines = []
        
        for i, line in enumerate(lines):
            # Check for numbered list items
            if (i > 0 and lines[i-1].strip() == '' and 
                    line.strip() and line.strip()[0].isdigit() and 
                    '. ' in line[:5]):
                formatted_lines.append(line)  # Keep as is, will already be formatted as list
            elif line.strip() and line.strip()[0].isdigit() and '. ' in line[:5]:
                # Ensure there's a line break before list items if not at beginning
                if i > 0 and formatted_lines[-1] != '':
                    formatted_lines.append('')  # Add empty line before list starts
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
        
        # Join lines back together
        text = '\n'.join(formatted_lines)
        
        return text
