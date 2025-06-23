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
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our modules
from config_loader import load_agent_config
import firebase_admin
from firebase_admin import credentials, firestore

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

class WebhookNotification(BaseModel):
    event_type: str  # document_added, document_updated, document_deleted
    agent_id: str
    file_id: str
    filename: Optional[str] = None
    timestamp: str

# Global variables for pre-initialized components
openai_client = None
firebase_service = None
conversation_repo = None
embedded_vector_search = None
whatsapp_service = None
whatsapp_webhook_handler = None


async def initialize_agent():
    """Initialize agent components with dynamically loaded configuration"""
    global openai_client, firebase_service, conversation_repo, embedded_vector_search, whatsapp_service, whatsapp_webhook_handler, AGENT_CONFIG
    
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
        
        # Initialize OpenAI client with pre-built tools and configuration
        openai_client = await initialize_openai_client()
        
        # Initialize WhatsApp service if configured (skip if module missing)
        try:
            whatsapp_service = initialize_whatsapp_service()
        except ImportError as e:
            logger.warning(f"WhatsApp service not available: {e}")
            whatsapp_service = None
        
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


async def initialize_openai_client():
    """Initialize OpenAI client with dynamically loaded configuration"""
    try:
        import openai
        
        # Initialize OpenAI client with configuration from Firestore
        openai_key = (AGENT_CONFIG.get('openai_api_key') or 
                     os.getenv('OPENAI_API_KEY') or 
                     os.getenv('openai_api_key'))
        
        if not openai_key:
            raise ValueError("OpenAI API key not found. Please check OPENAI_API_KEY environment variable.")
        
        # Create OpenAI client
        client = openai.OpenAI(api_key=openai_key)
        
        # Initialize tools with dynamic configuration
        tools = initialize_agent_tools()
        
        logger.info(f"OpenAI client initialized with {len(tools)} tools")
        return client
        
    except Exception as e:
        logger.error(f"OpenAI client initialization failed: {str(e)}")
        raise


def initialize_agent_tools():
    """Initialize all agent tools with dynamic configuration"""
    tools = []
    
    try:
        # Initialize Knowledge Base tools if configured
        if AGENT_CONFIG.get('knowledge_base_url'):
            kb_tools = initialize_knowledge_base_tools()
            tools.extend(kb_tools)
            logger.info(f"Initialized {len(kb_tools)} knowledge base tools")
        
        # Initialize MCP tools if configured  
        if AGENT_CONFIG.get('mcp_server_url'):
            mcp_tools = initialize_mcp_tools()
            tools.extend(mcp_tools)
            logger.info(f"Initialized {len(mcp_tools)} MCP tools")
        
        # Add custom tools
        custom_tools = initialize_custom_tools()
        tools.extend(custom_tools)
        
        logger.info(f"Total tools initialized: {len(tools)}")
        return tools
        
    except Exception as e:
        logger.error(f"Tool initialization failed: {str(e)}")
        return []


def initialize_knowledge_base_tools():
    """Initialize embedded vector search tools"""
    try:
        from embedded_vector_search import create_embedded_vector_tools
        kb_tools = create_embedded_vector_tools(AGENT_CONFIG)
        logger.info(f"Initialized {len(kb_tools)} embedded vector search tools")
        return kb_tools
    except Exception as e:
        logger.error(f"Failed to initialize embedded vector search tools: {str(e)}")
        return []


def initialize_mcp_tools():
    """Initialize MCP tools with dynamic optimizations"""
    tools = []
    try:
        mcp_server_url = AGENT_CONFIG.get('mcp_server_url')
        if mcp_server_url:
            # Import the MCP tools with optimization support
            from mcp_tool import get_mcp_tools_sync
            logger.info(f"🔗 Integrating MCP server: {mcp_server_url}")
            
            # Pass optimization config to MCP tools
            mcp_tools = get_mcp_tools_sync(mcp_server_url, AGENT_CONFIG)
            tools.extend(mcp_tools)
            logger.info(f"✅ Successfully integrated {len(mcp_tools)} MCP tools")
        else:
            logger.info("No MCP server URL configured")
    except Exception as e:
        logger.error(f"❌ Failed to integrate MCP server {mcp_server_url}: {str(e)}")
    
    return tools


def initialize_custom_tools():
    """Initialize custom utility tools"""
    tools = []
    
    try:
        # Using dict-based tools with direct OpenAI integration
        
        def get_current_time() -> str:
            """Get the current date and time"""
            from datetime import datetime
            return f"Current date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')}"
        
        def agent_info() -> str:
            """Get information about this AI agent"""
            domain_info = AGENT_CONFIG.get('_domain_info', {})
            return f"""
Agent Information:
- Agent ID: {AGENT_CONFIG['agent_id']}
- Name: {AGENT_CONFIG.get('name', 'Unknown')}
- Domain: {domain_info.get('detected_domain', 'general')}
- Model: {AGENT_CONFIG.get('model', 'gpt-4')}
- Tools Available: {len(initialize_agent_tools())}
- Knowledge Base: {'Enabled' if AGENT_CONFIG.get('knowledge_base_url') else 'Disabled'}
- MCP Tools: {'Enabled' if AGENT_CONFIG.get('mcp_server_url') else 'Disabled'}
- Optimization Applied: {'Yes' if '_domain_info' in AGENT_CONFIG else 'No'}
"""
        
        # Create custom tools (dict-based format)
        time_tool = {
            "name": "get_current_time",
            "description": "Get the current date and time",
            "function": get_current_time
        }
        
        info_tool = {
            "name": "agent_info", 
            "description": "Get information about this AI agent's capabilities and configuration",
            "function": agent_info
        }
        
        tools.extend([time_tool, info_tool])
        logger.info("Initialized custom utility tools")
        
    except Exception as e:
        logger.error(f"Failed to initialize custom tools: {str(e)}")
    
    return tools


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
        
    except ImportError as e:
        logger.warning(f"WhatsApp service module not available: {str(e)}")
        return None
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
        
        if not conversation_repo or not openai_client:
            logger.warning("Cannot initialize WhatsApp webhook handler - dependencies not available")
            return None
        
        webhook_handler = WhatsAppWebhookHandler(
            whatsapp_service=whatsapp_service,
            conversation_repo=conversation_repo,
            openai_client=openai_client
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
        "tools_count": len(initialize_agent_tools()) if openai_client else 0,
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False,
        "version": "1.0.0",
        "type": "universal"
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


@app.post("/api/conversation/message/stream")
async def process_message_stream(request: ProcessMessageRequest):
    """Process a user message and return streaming agent response"""
    
    async def generate_stream():
        try:
            # Add user message to conversation
            conversation_repo.add_message(
                request.conversation_id, 
                "user", 
                request.message
            )
            
            # Get conversation history
            messages = conversation_repo.get_messages(request.conversation_id)
            
            # Convert to OpenAI message format
            chat_history = []
            for msg in messages[:-1]:  # Exclude the message we just added
                chat_history.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            
            # Add system prompt
            system_prompt = AGENT_CONFIG.get('system_prompt', 'You are a helpful AI assistant.')
            messages_for_openai = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": request.message}]
            
            # Process with OpenAI streaming
            global openai_client
            model = AGENT_CONFIG.get('model', 'gpt-4')
            
            full_response = ""
            prompt_tokens = 0
            completion_tokens = 0
            
            stream = openai_client.chat.completions.create(
                model=model,
                messages=messages_for_openai,
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    
                    # Send content chunk
                    yield f"data: {json.dumps({'type': 'content', 'content': content})}\n\n"
                
                # Check for usage info in the final chunk
                if hasattr(chunk, 'usage') and chunk.usage:
                    prompt_tokens = chunk.usage.prompt_tokens
                    completion_tokens = chunk.usage.completion_tokens
            
            # Estimate token usage if not provided
            if prompt_tokens == 0:
                prompt_tokens = len(' '.join([msg['content'] for msg in messages_for_openai])) // 4
            if completion_tokens == 0:
                completion_tokens = len(full_response) // 4
                
            total_tokens = prompt_tokens + completion_tokens
            
            # Send token usage
            yield f"data: {json.dumps({'type': 'tokens', 'tokens': {'prompt': prompt_tokens, 'completion': completion_tokens, 'total': total_tokens}})}\n\n"
            
            # Add agent response to conversation
            conversation_repo.add_message(
                request.conversation_id,
                "assistant", 
                full_response
            )
            
            # Send completion signal
            yield "data: [DONE]\n\n"
            
        except Exception as e:
            logger.error(f"Error in streaming message: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/plain",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/plain; charset=utf-8"
        }
    )


@app.post("/api/conversation/message", response_model=MessageResponse)
async def process_message_legacy(request: ProcessMessageRequest):
    """Legacy non-streaming endpoint - redirects to streaming for consistency"""
    # For backward compatibility, we'll collect the streaming response
    # and return it as a single response
    try:
        full_response = ""
        tokens = {"prompt": 0, "completion": 0, "total": 0}
        
        # Get streaming response
        stream_response = await process_message_stream(request)
        
        # Note: This is a simplified version for compatibility
        # In practice, the frontend should use the streaming endpoint
        return MessageResponse(
            status="success",
            response="This endpoint is deprecated. Please use /api/conversation/message/stream for better performance.",
            conversation_id=request.conversation_id
        )
        
    except Exception as e:
        logger.error(f"Error in legacy message endpoint: {str(e)}")
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


# Health check for Cloud Run
@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "agent_id": AGENT_CONFIG.get('agent_id', 'unknown'),
        "config_loaded": bool(AGENT_CONFIG),
        "tools_initialized": openai_client is not None,
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False
    }

@app.get("/healthz")
async def health_check_legacy():
    """Legacy health check endpoint for backward compatibility"""
    return await health_check()


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
        "tools_count": len(initialize_agent_tools()) if openai_client else 0,
        "whatsapp_enabled": whatsapp_service.is_enabled() if whatsapp_service else False,
        "whatsapp_phone_id": AGENT_CONFIG.get('whatsapp', {}).get('phone_id') if whatsapp_service and whatsapp_service.is_enabled() else None
    }
    return safe_config

@app.get("/api/debug/routes")
async def debug_routes():
    """Debug endpoint to list all registered routes"""
    routes = []
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            routes.append({
                "path": route.path,
                "methods": list(route.methods),
                "name": getattr(route, 'name', 'unknown')
            })
    return {"routes": routes}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize agent on startup"""
    try:
        await initialize_agent()
        logger.info("Agent initialization completed successfully")
    except Exception as e:
        logger.error(f"Agent initialization failed, but continuing with limited functionality: {str(e)}")
        # Set minimal config to ensure routes still work
        global AGENT_CONFIG
        if not AGENT_CONFIG:
            AGENT_CONFIG = {
                'agent_id': os.getenv('AGENT_ID', 'unknown'),
                'name': 'Fallback Agent',
                'model': 'gpt-4',
                'system_prompt': 'You are a helpful AI assistant.'
            }


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