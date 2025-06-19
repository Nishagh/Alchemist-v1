#!/usr/bin/env python3
"""
Universal Agent Template - Main Application

This is a universal, high-performance agent template that dynamically loads
configuration from Firestore and applies LLM-based optimizations for any domain.

Key features:
- Dynamic configuration loading from Firestore
- LLM-powered domain-specific optimizations
- Embedded vector search with pre-computed embeddings
- Enhanced MCP tool integration
- Universal compatibility for any agent type
- Direct API integration (no LangChain dependency)
"""

import os
import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from config_loader import load_agent_config
import firebase_admin
from firebase_admin import credentials, firestore

# Import our direct API services
from services.direct_llm_service import DirectLLMService, create_llm_service
from services.direct_tool_system import ToolRegistry, register_tool
from services.conversation_manager import ConversationManager, create_conversation_manager
from services.message_types import HumanMessage, AIMessage

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global configuration will be loaded dynamically
AGENT_CONFIG = {}

# Initialize FastAPI app
app = FastAPI(
    title="Universal Alchemist Agent",
    description="Universal AI Agent Service with Dynamic Configuration",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH", "HEAD"],
    allow_headers=["*"],
    max_age=1200,
)

# Request/Response models
class CreateConversationRequest(BaseModel):
    user_id: Optional[str] = None

class ProcessMessageRequest(BaseModel):
    conversation_id: str
    message: str
    user_id: Optional[str] = None

class ConversationResponse(BaseModel):
    status: str
    conversation_id: str

class MessageResponse(BaseModel):
    status: str
    response: str
    conversation_id: str
    token_usage: Optional[Dict[str, int]] = None

class WebhookNotification(BaseModel):
    event_type: str  # document_added, document_updated, document_deleted
    agent_id: str
    file_id: str
    filename: Optional[str] = None
    timestamp: str

# Global variables for pre-initialized components
llm_service = None
tool_registry = None
conversation_manager = None
firebase_service = None
conversation_repo = None
embedded_vector_search = None
whatsapp_service = None
whatsapp_webhook_handler = None


async def initialize_agent():
    """Initialize agent components with dynamically loaded configuration"""
    global llm_service, tool_registry, conversation_manager, firebase_service, conversation_repo, embedded_vector_search, whatsapp_service, whatsapp_webhook_handler, AGENT_CONFIG
    
    try:
        # Get agent ID from environment
        agent_id = os.getenv('AGENT_ID')
        if not agent_id:
            raise ValueError("AGENT_ID environment variable is required")
        
        logger.info(f"Initializing universal agent: {agent_id}")
        
        # Load dynamic configuration from Firestore with LLM optimizations
        AGENT_CONFIG = load_agent_config(agent_id)
        logger.info(f"Loaded optimized configuration for agent: {agent_id}")
        
        # Update FastAPI app metadata
        app.title = f"Alchemist Agent - {AGENT_CONFIG.get('name', agent_id)}"
        app.description = f"Universal AI Agent: {AGENT_CONFIG.get('description', 'Dynamic agent service')}"
        
        # Initialize Firebase with pre-configured settings
        firebase_service = initialize_firebase_service()
        conversation_repo = initialize_conversation_repository(firebase_service)
        
        # Initialize embedded vector search
        embedded_vector_search = initialize_embedded_vector_search()
        
        # Initialize direct LLM service
        llm_service = initialize_direct_llm_service()
        
        # Initialize tool registry and register tools
        tool_registry = initialize_tool_registry()
        
        # Initialize conversation manager
        conversation_manager = initialize_conversation_manager()
        
        # Initialize WhatsApp service if configured
        whatsapp_service = initialize_whatsapp_service()
        
        # Initialize WhatsApp webhook handler if WhatsApp is enabled
        if whatsapp_service and whatsapp_service.is_enabled():
            whatsapp_webhook_handler = initialize_whatsapp_webhook_handler()
            logger.info("WhatsApp webhook integration enabled")
        
        # Initialize vector sync with real-time Firestore listeners
        sync_config = AGENT_CONFIG.get('vector_sync', {})
        if sync_config.get('enabled', True):
            # Perform initial sync first if configured
            if sync_config.get('sync_on_startup', True):
                logger.info("Performing initial vector sync on startup")
                await sync_embeddings_from_firestore()
            
            # Start real-time Firestore listener after initial sync
            logger.info("Starting real-time Firestore embedding listener")
            await start_realtime_embedding_listener()
        else:
            logger.info("Vector sync disabled in configuration")
        
        logger.info("Universal agent initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize universal agent: {str(e)}")
        raise


def initialize_firebase_service():
    """Initialize Firebase service with pre-configured credentials"""
    try:
        import firebase_admin
        from firebase_admin import credentials, firestore
        
        # Initialize Firebase app if not already done by config_loader
        if not firebase_admin._apps:
            # Try multiple paths for Firebase credentials
            firebase_creds_paths = [
                'firebase-credentials.json',  # Local/template directory
                '/app/firebase-credentials.json',  # Container path
                os.getenv('FIREBASE_CREDENTIALS', ''),
                os.getenv('firebase_credentials', ''),
                os.getenv('GOOGLE_APPLICATION_CREDENTIALS', '')
            ]
            
            firebase_initialized = False
            for creds_path in firebase_creds_paths:
                if creds_path and os.path.exists(creds_path):
                    try:
                        cred = credentials.Certificate(creds_path)
                        firebase_admin.initialize_app(cred, {
                            'projectId': AGENT_CONFIG['firebase_project_id']
                        })
                        logger.info(f"Firebase initialized with credentials: {creds_path}")
                        firebase_initialized = True
                        break
                    except Exception as e:
                        logger.warning(f"Failed to initialize Firebase with {creds_path}: {str(e)}")
                        continue
            
            if not firebase_initialized:
                # Fall back to Application Default Credentials
                firebase_admin.initialize_app()
                logger.info("Firebase initialized with Application Default Credentials")
        
        db = firestore.client()
        logger.info("Firebase service initialized")
        return db
        
    except Exception as e:
        logger.error(f"Firebase initialization failed: {str(e)}")
        raise


def initialize_conversation_repository(db):
    """Initialize conversation repository"""
    from firebase_admin import firestore
    
    class ConversationRepository:
        def __init__(self, firestore_client):
            self.db = firestore_client
            self.agent_id = AGENT_CONFIG['agent_id']
        
        def create_conversation(self, user_id: Optional[str] = None, metadata: Optional[Dict[str, Any]] = None):
            """Create a new conversation"""
            conversation_data = {
                'agent_id': self.agent_id,
                'user_id': user_id,
                'status': 'active',
                'message_count': 0,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP
            }
            
            # Add metadata if provided
            if metadata:
                conversation_data['metadata'] = metadata
            
            conversation_ref = self.db.collection('alchemist_agents').document(self.agent_id).collection('conversations')
            doc_ref = conversation_ref.add(conversation_data)[1]
            return doc_ref.id
        
        def add_message(self, conversation_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
            """Add message to conversation"""
            message_data = {
                'role': role,
                'content': content,
                'timestamp': firestore.SERVER_TIMESTAMP
            }
            
            # Add metadata if provided
            if metadata:
                message_data['metadata'] = metadata
            
            conversation_ref = self.db.collection('alchemist_agents').document(self.agent_id).collection('conversations').document(conversation_id)
            message_ref = conversation_ref.collection('messages').add(message_data)[1]
            
            # Update conversation metadata
            conversation_ref.update({
                'updated_at': firestore.SERVER_TIMESTAMP,
                'message_count': firestore.Increment(1),
                'last_message': content[:100]
            })
            
            return message_ref.id
        
        def get_messages(self, conversation_id: str, limit: int = 50):
            """Get conversation messages"""
            messages_ref = (
                self.db.collection('alchemist_agents')
                .document(self.agent_id)
                .collection('conversations')
                .document(conversation_id)
                .collection('messages')
                .order_by('timestamp')
                .limit(limit)
            )
            
            messages = []
            for msg_doc in messages_ref.stream():
                msg_data = msg_doc.to_dict()
                messages.append(msg_data)
            
            return messages
    
    return ConversationRepository(db)


def initialize_direct_llm_service():
    """Initialize direct LLM service with dynamically loaded configuration"""
    try:
        # Get configuration
        model = AGENT_CONFIG.get('model', 'gpt-4')
        openai_key = (AGENT_CONFIG.get('openai_api_key') or 
                     os.getenv('OPENAI_API_KEY') or 
                     os.getenv('openai_api_key'))
        
        if not openai_key:
            raise ValueError("OpenAI API key not found. Please check OPENAI_API_KEY environment variable.")
        
        # Create direct LLM service
        service = create_llm_service(api_key=openai_key, model=model)
        
        logger.info(f"Direct LLM service initialized with model: {model}")
        return service
        
    except Exception as e:
        logger.error(f"Direct LLM service initialization failed: {str(e)}")
        raise


def initialize_tool_registry():
    """Initialize tool registry and register all available tools"""
    try:
        # Create tool registry
        registry = ToolRegistry(namespace=AGENT_CONFIG.get('agent_id', 'default'))
        
        # Register tools with dynamic configuration
        register_agent_tools(registry)
        
        logger.info(f"Tool registry initialized with {len(registry.list_tools())} tools")
        return registry
        
    except Exception as e:
        logger.error(f"Tool registry initialization failed: {str(e)}")
        raise


def initialize_conversation_manager():
    """Initialize conversation manager with LLM service and tools"""
    try:
        # Get system prompt
        system_prompt = AGENT_CONFIG.get('system_prompt', 'You are a helpful AI assistant.')
        
        # Create conversation manager
        manager = create_conversation_manager(
            llm_service=llm_service,
            tool_registry=tool_registry,
            system_prompt=system_prompt,
            max_turns_per_conversation=50,
            max_tool_iterations=25
        )
        
        logger.info("Conversation manager initialized successfully")
        return manager
        
    except Exception as e:
        logger.error(f"Conversation manager initialization failed: {str(e)}")
        raise


def register_agent_tools(registry: ToolRegistry):
    """Register all agent tools with the tool registry"""
    try:
        # Register Knowledge Base tools if configured
        if AGENT_CONFIG.get('knowledge_base_url'):
            register_knowledge_base_tools(registry)
            logger.info("Registered knowledge base tools")
        
        # Register MCP tools if configured  
        if AGENT_CONFIG.get('mcp_server_url'):
            register_mcp_tools(registry)
            logger.info("Registered MCP tools")
        
        # Register custom tools
        register_custom_tools(registry)
        logger.info("Registered custom tools")
        
        logger.info(f"Total tools registered: {len(registry.list_tools())}")
        
    except Exception as e:
        logger.error(f"Tool registration failed: {str(e)}")
        raise


def register_knowledge_base_tools(registry: ToolRegistry):
    """Register embedded vector search tools"""
    try:
        from embedded_vector_search import register_embedded_vector_tools
        register_embedded_vector_tools(registry, AGENT_CONFIG)
        logger.info("Registered embedded vector search tools")
    except Exception as e:
        logger.error(f"Failed to register embedded vector search tools: {str(e)}")


def register_mcp_tools(registry: ToolRegistry):
    """Register MCP tools with dynamic optimizations"""
    try:
        mcp_server_url = AGENT_CONFIG.get('mcp_server_url')
        if mcp_server_url:
            # Import the MCP tools with optimization support
            from mcp_tool import register_mcp_tools_with_registry_sync
            logger.info(f"🔗 Integrating MCP server: {mcp_server_url}")
            
            # Pass optimization config to MCP tools
            register_mcp_tools_with_registry_sync(registry, mcp_server_url, AGENT_CONFIG)
            logger.info(f"✅ Successfully integrated MCP tools")
        else:
            logger.info("No MCP server URL configured")
    except Exception as e:
        logger.error(f"❌ Failed to integrate MCP server: {str(e)}")


def register_custom_tools(registry: ToolRegistry):
    """Register custom utility tools"""
    try:        
        def get_current_time() -> str:
            """Get the current date and time"""
            from datetime import datetime
            return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        def agent_info() -> str:
            """Get information about this AI agent"""
            domain_info = AGENT_CONFIG.get('_domain_info', {})
            tool_count = len(registry.list_tools()) + 2  # +2 for the tools we're about to add
            return f"""
Agent Information:
- Agent ID: {AGENT_CONFIG['agent_id']}
- Name: {AGENT_CONFIG.get('name', 'Unknown')}
- Domain: {domain_info.get('detected_domain', 'general')}
- Model: {AGENT_CONFIG.get('model', 'gpt-4')}
- Tools Available: {tool_count}
- Knowledge Base: {'Enabled' if AGENT_CONFIG.get('knowledge_base_url') else 'Disabled'}
- MCP Tools: {'Enabled' if AGENT_CONFIG.get('mcp_server_url') else 'Disabled'}
- Optimization Applied: {'Yes' if '_domain_info' in AGENT_CONFIG else 'No'}
"""
        
        # Register custom tools with the registry
        registry.register_tool(
            name="get_current_time",
            func=get_current_time,
            description="Get the current date and time"
        )
        
        registry.register_tool(
            name="agent_info",
            func=agent_info,
            description="Get information about this AI agent's capabilities and configuration"
        )
        
        logger.info("Registered custom utility tools")
        
    except Exception as e:
        logger.error(f"Failed to register custom tools: {str(e)}")
        raise


def initialize_embedded_vector_search():
    """Initialize embedded vector search for sync operations"""
    try:
        from embedded_vector_search import EmbeddedVectorSearch
        
        openai_key = (AGENT_CONFIG.get('openai_api_key') or 
                     os.getenv('OPENAI_API_KEY') or 
                     os.getenv('openai_api_key'))
        
        if not openai_key:
            raise ValueError("OpenAI API key not found for vector search. Please check OPENAI_API_KEY environment variable.")
        
        vector_search = EmbeddedVectorSearch(
            agent_id=AGENT_CONFIG['agent_id'],
            openai_api_key=openai_key
        )
        
        logger.info("Embedded vector search initialized for sync operations")
        return vector_search
        
    except Exception as e:
        logger.error(f"Failed to initialize embedded vector search: {str(e)}")
        return None


async def start_realtime_embedding_listener():
    """Start real-time Firestore listener for embeddings"""
    try:
        from knowledge_service import default_knowledge_client
        
        if not embedded_vector_search:
            logger.error("Embedded vector search not initialized")
            return
        
        def on_embeddings_change(embeddings):
            """Handle real-time embedding changes"""
            try:
                logger.info(f"Real-time update: {len(embeddings)} embeddings received")
                
                if not embeddings:
                    logger.info("No embeddings to sync")
                    return
                
                # Group embeddings by file_id
                files_data = {}
                for emb in embeddings:
                    file_id = emb.get('file_id')
                    if file_id:
                        if file_id not in files_data:
                            files_data[file_id] = []
                        
                        files_data[file_id].append({
                            'content': emb.get('content', ''),
                            'embedding': emb.get('embedding', []),  # Include pre-computed embedding vector
                            'metadata': {
                                'filename': emb.get('filename', 'unknown'),
                                'file_id': file_id,
                                'chunk_index': emb.get('chunk_index'),
                                'source': 'firestore_embeddings'
                            }
                        })
                
                # Sync each file's embeddings
                synced_files = 0
                for file_id, vectors_data in files_data.items():
                    try:
                        if embedded_vector_search.sync_document_vectors(file_id, vectors_data):
                            synced_files += 1
                            logger.info(f"Synced {len(vectors_data)} embeddings for file {file_id}")
                        else:
                            logger.error(f"Failed to sync embeddings for file {file_id}")
                    except Exception as e:
                        logger.error(f"Error syncing file {file_id}: {str(e)}")
                
                logger.info(f"Real-time sync completed: {synced_files}/{len(files_data)} files synced")
                
            except Exception as e:
                logger.error(f"Error in real-time embedding callback: {str(e)}")
        
        # Start the listener
        listener = default_knowledge_client.listen_to_embeddings(
            AGENT_CONFIG['agent_id'], 
            on_embeddings_change
        )
        
        if listener:
            logger.info("Real-time Firestore embedding listener started successfully")
        else:
            logger.error("Failed to start real-time embedding listener")
        
    except Exception as e:
        logger.error(f"Error starting real-time embedding listener: {str(e)}")


async def sync_embeddings_from_firestore():
    """Perform initial sync of embeddings from Firestore"""
    try:
        from knowledge_service import default_knowledge_client
        
        if not embedded_vector_search:
            logger.error("Embedded vector search not initialized")
            return
        
        # Get all embeddings for this agent
        embeddings = default_knowledge_client.get_embeddings(AGENT_CONFIG['agent_id'])
        
        if not embeddings:
            logger.info("No embeddings found in Firestore")
            return
        
        logger.info(f"Found {len(embeddings)} embeddings in Firestore")
        
        # Group embeddings by file_id
        files_data = {}
        for emb in embeddings:
            file_id = emb.get('file_id')
            if file_id:
                if file_id not in files_data:
                    files_data[file_id] = []
                
                files_data[file_id].append({
                    'content': emb.get('content', ''),
                    'embedding': emb.get('embedding', []),  # Include pre-computed embedding vector
                    'metadata': {
                        'filename': emb.get('filename', 'unknown'),
                        'file_id': file_id,
                        'chunk_index': emb.get('chunk_index'),
                        'source': 'firestore_embeddings'
                    }
                })
        
        # Sync each file's embeddings
        synced_files = 0
        for file_id, vectors_data in files_data.items():
            try:
                if embedded_vector_search.sync_document_vectors(file_id, vectors_data):
                    synced_files += 1
                    logger.info(f"Synced {len(vectors_data)} embeddings for file {file_id}")
                else:
                    logger.error(f"Failed to sync embeddings for file {file_id}")
            except Exception as e:
                logger.error(f"Error syncing file {file_id}: {str(e)}")
        
        logger.info(f"Initial Firestore sync completed: {synced_files}/{len(files_data)} files synced")
        
    except Exception as e:
        logger.error(f"Error syncing embeddings from Firestore: {str(e)}")


def initialize_whatsapp_service():
    """Initialize WhatsApp service with agent configuration"""
    try:
        from whatsapp_service import WhatsAppService
        
        whatsapp_service = WhatsAppService(AGENT_CONFIG)
        
        if whatsapp_service.is_enabled():
            logger.info("WhatsApp service initialized successfully")
        else:
            logger.info("WhatsApp service disabled - no configuration found")
        
        return whatsapp_service
        
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp service: {str(e)}")
        return None


def initialize_whatsapp_webhook_handler():
    """Initialize WhatsApp webhook handler"""
    try:
        from whatsapp_webhook import WhatsAppWebhookHandler
        
        if not whatsapp_service or not whatsapp_service.is_enabled():
            logger.warning("Cannot initialize WhatsApp webhook handler - service not available")
            return None
        
        if not conversation_repo or not agent_executor:
            logger.warning("Cannot initialize WhatsApp webhook handler - dependencies not available")
            return None
        
        webhook_handler = WhatsAppWebhookHandler(
            whatsapp_service=whatsapp_service,
            conversation_repo=conversation_repo,
            agent_executor=agent_executor
        )
        
        # Include WhatsApp webhook routes in the app
        app.include_router(webhook_handler.get_router(), tags=["WhatsApp"])
        
        logger.info("WhatsApp webhook handler initialized successfully")
        return webhook_handler
        
    except Exception as e:
        logger.error(f"Failed to initialize WhatsApp webhook handler: {str(e)}")
        return None


# FastAPI Routes
@app.get("/")
async def root():
    """Health check and agent info"""
    return {
        "status": "success",
        "message": f"Universal Alchemist Agent {AGENT_CONFIG.get('agent_id', 'unknown')} is running",
        "agent_id": AGENT_CONFIG.get('agent_id'),
        "name": AGENT_CONFIG.get('name'),
        "domain": AGENT_CONFIG.get('_domain_info', {}).get('detected_domain', 'general'),
        "model": AGENT_CONFIG.get('model'),
        "tools_count": len(tool_registry.list_tools()) if tool_registry else 0,
        "llm_service": "direct_api" if llm_service else "not_initialized",
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False,
        "version": "2.0.0",
        "type": "universal_direct_api"
    }


@app.post("/api/conversation/create", response_model=ConversationResponse)
async def create_conversation(request: CreateConversationRequest):
    """Create a new conversation"""
    try:
        conversation_id = conversation_repo.create_conversation(request.user_id)
        return ConversationResponse(
            status="success",
            conversation_id=conversation_id
        )
    except Exception as e:
        logger.error(f"Error creating conversation: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/message", response_model=MessageResponse)
async def process_message(request: ProcessMessageRequest):
    """Process a user message and return agent response"""
    try:
        # Process message using conversation manager
        result = await conversation_manager.process_message(
            conversation_id=request.conversation_id,
            message=request.message,
            user_id=request.user_id
        )
        
        if not result.success:
            logger.error(f"Message processing failed: {result.error}")
            raise HTTPException(status_code=500, detail=result.error or "Message processing failed")
        
        # Also add to conversation repository for backward compatibility
        try:
            conversation_repo.add_message(request.conversation_id, "user", request.message)
            conversation_repo.add_message(request.conversation_id, "assistant", result.response)
        except Exception as e:
            logger.warning(f"Failed to update conversation repository: {str(e)}")
        
        return MessageResponse(
            status="success",
            response=result.response,
            conversation_id=result.conversation_id,
            token_usage={
                "prompt_tokens": result.token_usage.prompt_tokens,
                "completion_tokens": result.token_usage.completion_tokens,
                "total_tokens": result.token_usage.total_tokens
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/message/stream")
async def process_message_stream(request: ProcessMessageRequest):
    """Process a user message and return streaming response"""
    try:
        async def generate():
            async for chunk in conversation_manager.stream_response(
                conversation_id=request.conversation_id,
                message=request.message,
                user_id=request.user_id
            ):
                # Format as Server-Sent Events
                yield f"data: {chunk}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/plain",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Disable nginx buffering
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing streaming message: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str, limit: int = 50):
    """Get messages from a conversation"""
    try:
        messages = conversation_repo.get_messages(conversation_id, limit)
        return {
            "status": "success",
            "conversation_id": conversation_id,
            "messages": messages,
            "count": len(messages)
        }
    except Exception as e:
        logger.error(f"Error getting messages: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/conversation/{conversation_id}/stats")
async def get_conversation_stats(conversation_id: str):
    """Get conversation statistics including token usage"""
    try:
        stats = conversation_manager.get_conversation_stats(conversation_id)
        if not stats:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        # Add LLM service token usage
        llm_usage = llm_service.get_token_usage()
        stats["llm_total_tokens"] = {
            "prompt_tokens": llm_usage.prompt_tokens,
            "completion_tokens": llm_usage.completion_tokens,
            "total_tokens": llm_usage.total_tokens
        }
        
        return {
            "status": "success",
            "stats": stats
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting conversation stats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/token-usage")
async def get_token_usage():
    """Get overall token usage statistics"""
    try:
        llm_usage = llm_service.get_token_usage()
        
        return {
            "status": "success",
            "token_usage": {
                "prompt_tokens": llm_usage.prompt_tokens,
                "completion_tokens": llm_usage.completion_tokens,
                "total_tokens": llm_usage.total_tokens
            },
            "model": llm_service.model,
            "service_type": "direct_api"
        }
        
    except Exception as e:
        logger.error(f"Error getting token usage: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# Health check for Cloud Run
@app.get("/healthz")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_id": AGENT_CONFIG.get('agent_id', 'unknown'),
        "config_loaded": bool(AGENT_CONFIG),
        "llm_service_ready": llm_service is not None,
        "conversation_manager_ready": conversation_manager is not None,
        "tools_count": len(tool_registry.list_tools()) if tool_registry else 0,
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False
    }


# Configuration endpoint for debugging
@app.get("/api/config")
async def get_config():
    """Get current agent configuration (excluding sensitive data)"""
    safe_config = {
        "agent_id": AGENT_CONFIG.get('agent_id'),
        "name": AGENT_CONFIG.get('name'),
        "domain": AGENT_CONFIG.get('_domain_info', {}),
        "has_mcp_server": bool(AGENT_CONFIG.get('mcp_server_url')),
        "has_knowledge_base": bool(AGENT_CONFIG.get('knowledge_base_url')),
        "model": AGENT_CONFIG.get('model'),
        "tools_count": len(tool_registry.list_tools()) if tool_registry else 0,
        "llm_service_model": llm_service.model if llm_service else None,
        "conversation_manager_ready": conversation_manager is not None,
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False,
        "whatsapp_phone_id": AGENT_CONFIG.get('whatsapp', {}).get('phone_id') if whatsapp_service and whatsapp_service.is_enabled() else None
    }
    return safe_config


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    await initialize_agent()


if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8080))
    
    logger.info(f"Starting universal agent on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Disable reload for production
        log_level="info"
    )