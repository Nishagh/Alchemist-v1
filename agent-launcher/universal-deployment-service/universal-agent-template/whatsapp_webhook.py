#!/usr/bin/env python3
"""
WhatsApp Webhook Handler for Universal Agent Template

Simplified webhook handler for existing WhatsApp Business users.
Provides webhook endpoints for verification and message processing.
"""

import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WhatsAppWebhookHandler:
    """
    Handler for WhatsApp webhook endpoints and message processing.
    """
    
    def __init__(self, whatsapp_service, conversation_repo, openai_client):
        """
        Initialize webhook handler with required services.
        
        Args:
            whatsapp_service: WhatsApp service instance
            conversation_repo: Conversation repository instance
            openai_client: OpenAI client instance
        """
        self.whatsapp_service = whatsapp_service
        self.conversation_repo = conversation_repo
        self.openai_client = openai_client
        self.router = APIRouter()
        
        # Add routes
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for WhatsApp webhook"""
        
        @self.router.get("/webhook/whatsapp")
        async def verify_webhook(
            hub_mode: str = Query(alias="hub.mode"),
            hub_challenge: str = Query(alias="hub.challenge"), 
            hub_verify_token: str = Query(alias="hub.verify_token")
        ):
            """WhatsApp webhook verification endpoint"""
            try:
                if not self.whatsapp_service.is_enabled():
                    raise HTTPException(status_code=404, detail="WhatsApp integration not configured")
                
                challenge = await self.whatsapp_service.verify_webhook(
                    hub_mode, hub_challenge, hub_verify_token
                )
                return challenge
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error in webhook verification: {str(e)}")
                raise HTTPException(status_code=500, detail="Verification failed")
        
        @self.router.post("/webhook/whatsapp")
        async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
            """WhatsApp webhook message handler"""
            try:
                if not self.whatsapp_service.is_enabled():
                    raise HTTPException(status_code=404, detail="WhatsApp integration not configured")
                
                # Get raw body and headers
                body = await request.body()
                signature = request.headers.get("x-hub-signature-256", "")
                
                # Verify webhook signature
                if not self.whatsapp_service.verify_signature(body, signature):
                    logger.warning("Invalid webhook signature")
                    raise HTTPException(status_code=403, detail="Invalid signature")
                
                # Parse JSON payload
                try:
                    webhook_data = await request.json()
                except Exception as e:
                    logger.error(f"Error parsing webhook JSON: {str(e)}")
                    raise HTTPException(status_code=400, detail="Invalid JSON")
                
                # Process message in background
                background_tasks.add_task(
                    self._process_webhook_message, 
                    webhook_data
                )
                
                # Return 200 immediately to acknowledge receipt
                return {"status": "success"}
                
            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error handling WhatsApp webhook: {str(e)}")
                raise HTTPException(status_code=500, detail="Internal server error")
    
    async def _process_webhook_message(self, webhook_data: Dict[str, Any]):
        """
        Process incoming WhatsApp message in background.
        
        Args:
            webhook_data: The webhook JSON data
        """
        try:
            # Parse the message
            message = self.whatsapp_service.parse_webhook_message(webhook_data)
            
            if not message:
                logger.info("No message found in webhook data")
                return
            
            logger.info(f"Processing WhatsApp message from {message['from_phone']}")
            
            # Mark message as read
            if message['message_id']:
                await self.whatsapp_service.mark_as_read(message['message_id'])
            
            # Handle different message types
            if message['type'] == 'text' and message['text']:
                await self._handle_text_message(message)
            elif message['type'] in ['image', 'document', 'audio']:
                await self._handle_media_message(message)
            else:
                logger.info(f"Unsupported message type: {message['type']}")
                
        except Exception as e:
            logger.error(f"Error processing webhook message: {str(e)}")
    
    async def _handle_text_message(self, message: Dict[str, Any]):
        """
        Handle incoming text message.
        
        Args:
            message: Parsed message data
        """
        try:
            phone_number = message['from_phone']
            message_text = message['text']
            
            # Generate consistent user ID for this phone number
            user_id = self.whatsapp_service.get_conversation_user_id(phone_number)
            
            # Find or create conversation for this user
            conversation_id = await self._get_or_create_conversation(user_id, phone_number)
            
            # Add user message to conversation
            self.conversation_repo.add_message(
                conversation_id,
                "user",
                message_text,
                metadata={
                    'source': 'whatsapp',
                    'phone_number': phone_number,
                    'contact_name': message.get('contact_name', 'Unknown'),
                    'message_id': message['message_id']
                }
            )
            
            # Get conversation history for context
            messages = self.conversation_repo.get_messages(conversation_id)
            
            # Convert to OpenAI message format
            chat_history = []
            for msg in messages[:-1]:  # Exclude the message we just added
                chat_history.append({
                    "role": msg['role'],
                    "content": msg['content']
                })
            
            # Add system prompt and process with OpenAI
            system_prompt = "You are a helpful AI assistant responding via WhatsApp. Keep responses concise and friendly."
            messages_for_openai = [{"role": "system", "content": system_prompt}] + chat_history + [{"role": "user", "content": message_text}]
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=messages_for_openai,
                temperature=0.7,
                max_tokens=500  # Shorter for WhatsApp
            )
            
            response_text = response.choices[0].message.content
            
            # Format response for WhatsApp
            formatted_response = self.whatsapp_service.format_agent_response(response_text)
            
            # Add agent response to conversation
            self.conversation_repo.add_message(
                conversation_id,
                "assistant",
                formatted_response,
                metadata={
                    'source': 'whatsapp',
                    'phone_number': phone_number
                }
            )
            
            # Send response via WhatsApp
            success = await self.whatsapp_service.send_text_message(
                phone_number, 
                formatted_response
            )
            
            if success:
                logger.info(f"Successfully sent WhatsApp response to {phone_number}")
            else:
                logger.error(f"Failed to send WhatsApp response to {phone_number}")
                
        except Exception as e:
            logger.error(f"Error handling text message: {str(e)}")
            # Send error message to user
            try:
                await self.whatsapp_service.send_text_message(
                    message['from_phone'],
                    "Sorry, I encountered an error processing your message. Please try again."
                )
            except:
                pass
    
    async def _handle_media_message(self, message: Dict[str, Any]):
        """
        Handle incoming media message.
        
        Args:
            message: Parsed message data
        """
        try:
            phone_number = message['from_phone']
            media_info = message['media']
            
            # For now, respond with a message about media handling
            response = f"I received your {media_info['type']} message. "
            
            if media_info['type'] == 'image' and media_info.get('caption'):
                # If image has caption, process the caption as text
                caption = media_info['caption']
                response += f"I can see you sent an image with the caption: '{caption}'. How can I help you with this?"
                
                # Process the caption as a text message
                message_copy = message.copy()
                message_copy['type'] = 'text'
                message_copy['text'] = caption
                await self._handle_text_message(message_copy)
                return
            else:
                response += "I can process text messages to help you. Please describe what you need assistance with."
            
            # Send response
            await self.whatsapp_service.send_text_message(phone_number, response)
            
        except Exception as e:
            logger.error(f"Error handling media message: {str(e)}")
    
    async def _get_or_create_conversation(self, user_id: str, phone_number: str) -> str:
        """
        Get existing conversation or create a new one for the user.
        
        Args:
            user_id: Consistent user ID for this phone number
            phone_number: WhatsApp phone number
            
        Returns:
            Conversation ID
        """
        try:
            # Try to find existing conversation for this user
            # This is a simplified approach - in production, you might want
            # to search for existing conversations by user_id
            
            # For now, create a new conversation each time
            # You can modify this to implement conversation persistence
            conversation_id = self.conversation_repo.create_conversation(
                user_id=user_id,
                metadata={
                    'source': 'whatsapp',
                    'phone_number': phone_number
                }
            )
            
            logger.info(f"Created conversation {conversation_id} for WhatsApp user {phone_number}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error getting/creating conversation: {str(e)}")
            raise
    
    def get_router(self) -> APIRouter:
        """Get the FastAPI router with WhatsApp webhook endpoints"""
        return self.router