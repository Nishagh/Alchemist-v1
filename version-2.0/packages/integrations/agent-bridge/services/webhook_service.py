"""
Webhook management and routing service for WhatsApp messages
"""
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Callable
import httpx
from urllib.parse import urlparse

from models.webhook_models import (
    WhatsAppWebhook, WhatsAppMessage, ProcessedMessage, 
    AgentResponse, WebhookLog, SendMessageRequest
)
from services.firebase_service import FirebaseService
from services.bsp_provider import BSPProvider
from config.settings import get_settings

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for processing WhatsApp webhooks and routing messages"""
    
    def __init__(self, firebase_service: FirebaseService, bsp_providers: Dict[str, BSPProvider]):
        self.firebase = firebase_service
        self.bsp_providers = bsp_providers
        self.settings = get_settings()
        self._message_handlers: Dict[str, Callable] = {}
        self._client = httpx.AsyncClient(timeout=30.0)
    
    async def process_webhook(self, webhook_data: WhatsAppWebhook) -> Dict[str, Any]:
        """Process incoming WhatsApp webhook"""
        processing_start = datetime.utcnow()
        webhook_id = f"wh_{int(processing_start.timestamp())}"
        
        try:
            results = []
            
            for entry in webhook_data.entry:
                for change in entry.changes:
                    if change.field == "messages":
                        result = await self._process_message_change(
                            entry.id, change, webhook_id
                        )
                        results.append(result)
                    elif change.field == "message_status":
                        result = await self._process_status_change(
                            entry.id, change, webhook_id
                        )
                        results.append(result)
            
            processing_time = (datetime.utcnow() - processing_start).total_seconds() * 1000
            
            return {
                "webhook_id": webhook_id,
                "processed_entries": len(results),
                "processing_time_ms": int(processing_time),
                "status": "success",
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            processing_time = (datetime.utcnow() - processing_start).total_seconds() * 1000
            
            # Log the error
            await self._log_webhook_error(webhook_id, webhook_data, str(e), int(processing_time))
            
            return {
                "webhook_id": webhook_id,
                "status": "error",
                "error": str(e),
                "processing_time_ms": int(processing_time)
            }
    
    async def _process_message_change(self, entry_id: str, change: Any, webhook_id: str) -> Dict[str, Any]:
        """Process message change from webhook"""
        try:
            phone_number_id = change.value.metadata.get("phone_number_id")
            
            # Find associated managed account
            account = await self._find_account_by_phone_id(phone_number_id)
            if not account:
                logger.warning(f"No managed account found for phone number ID: {phone_number_id}")
                return {
                    "status": "skipped",
                    "reason": "account_not_found",
                    "phone_number_id": phone_number_id
                }
            
            processed_messages = []
            agent_responses = []
            
            # Process each message
            if change.value.messages:
                for message in change.value.messages:
                    processed_msg = await self._process_single_message(message, account)
                    processed_messages.append(processed_msg)
                    
                    # Route to agent and get response
                    agent_response = await self._route_to_agent(processed_msg, account)
                    if agent_response:
                        agent_responses.append(agent_response)
                        
                        # Send response back via WhatsApp
                        await self._send_agent_response(agent_response, account)
            
            # Log webhook processing
            await self._log_webhook_processing(
                webhook_id, account['id'], change.dict(), 
                processed_messages, agent_responses, "success"
            )
            
            return {
                "status": "processed",
                "account_id": account['id'],
                "messages_processed": len(processed_messages),
                "responses_sent": len(agent_responses)
            }
            
        except Exception as e:
            logger.error(f"Message change processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_status_change(self, entry_id: str, change: Any, webhook_id: str) -> Dict[str, Any]:
        """Process message status change from webhook"""
        try:
            phone_number_id = change.value.metadata.get("phone_number_id")
            
            # Find associated managed account
            account = await self._find_account_by_phone_id(phone_number_id)
            if not account:
                return {
                    "status": "skipped",
                    "reason": "account_not_found",
                    "phone_number_id": phone_number_id
                }
            
            # Process status updates
            statuses_processed = 0
            if change.value.statuses:
                for status in change.value.statuses:
                    await self._process_message_status(status, account)
                    statuses_processed += 1
            
            # Log status processing
            await self._log_webhook_processing(
                webhook_id, account['id'], change.dict(), 
                [], [], "status_update", statuses_processed
            )
            
            return {
                "status": "processed",
                "account_id": account['id'],
                "statuses_processed": statuses_processed
            }
            
        except Exception as e:
            logger.error(f"Status change processing failed: {str(e)}")
            return {
                "status": "error",
                "error": str(e)
            }
    
    async def _process_single_message(self, message: WhatsAppMessage, account: Dict[str, Any]) -> ProcessedMessage:
        """Process a single WhatsApp message"""
        # Extract message content based on type
        content = ""
        if message.type == "text" and message.text:
            content = message.text.get("body", "")
        elif message.type == "image" and message.image:
            content = f"[Image] {message.image.get('caption', 'Image received')}"
        elif message.type == "audio" and message.audio:
            content = "[Audio] Audio message received"
        elif message.type == "video" and message.video:
            content = f"[Video] {message.video.get('caption', 'Video received')}"
        elif message.type == "document" and message.document:
            filename = message.document.get('filename', 'Document')
            content = f"[Document] {filename}"
        elif message.type == "location" and message.location:
            content = "[Location] Location shared"
        else:
            content = f"[{message.type.title()}] Unsupported message type"
        
        return ProcessedMessage(
            message_id=message.id,
            from_number=message.from_,
            to_number=account['phone_number'],
            message_type=message.type,
            content=content,
            timestamp=datetime.fromisoformat(message.timestamp.replace('Z', '+00:00')),
            context=message.context.dict() if message.context else None,
            metadata={
                "account_id": account['id'],
                "deployment_id": account['deployment_id'],
                "business_name": account['business_name']
            }
        )
    
    async def _route_to_agent(self, message: ProcessedMessage, account: Dict[str, Any]) -> Optional[AgentResponse]:
        """Route message to AI agent and get response via API"""
        try:
            # Get agent webhook URL from the managed account record
            agent_webhook_url = account.get('agent_webhook_url')
            if not agent_webhook_url:
                logger.warning(f"No agent webhook URL configured for account {account['id']}")
                return AgentResponse(
                    to=message.from_number,
                    message="Hello! I received your message. However, the agent is not currently configured to respond. Please contact support.",
                    message_type="text"
                )
            
            # Prepare payload for agent API
            agent_payload = {
                "message_id": message.message_id,
                "from": message.from_number,
                "content": message.content,
                "message_type": message.message_type,
                "timestamp": message.timestamp.isoformat(),
                "context": message.context,
                "business_info": {
                    "name": account['business_name'],
                    "phone": account['phone_number']
                },
                "metadata": {
                    "deployment_id": account['deployment_id'],
                    "account_id": account['id']
                }
            }
            
            # Send to agent API
            response = await self._client.post(
                agent_webhook_url,
                json=agent_payload,
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "WhatsApp-BSP-Service/1.0"
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                agent_data = response.json()
                
                # Create agent response
                return AgentResponse(
                    to=message.from_number,
                    message=agent_data.get('message', 'Hello! I received your message.'),
                    message_type=agent_data.get('message_type', 'text'),
                    context=agent_data.get('context')
                )
            else:
                logger.warning(f"Agent API returned status {response.status_code}: {response.text}")
                return AgentResponse(
                    to=message.from_number,
                    message="Hello! I received your message but I'm having trouble processing it right now. Please try again in a moment.",
                    message_type="text"
                )
                
        except asyncio.TimeoutError:
            logger.error("Agent API request timed out")
            return AgentResponse(
                to=message.from_number,
                message="Hello! I received your message but I'm responding slowly right now. Please give me a moment.",
                message_type="text"
            )
        except Exception as e:
            logger.error(f"Agent routing failed: {str(e)}")
            # Return fallback response
            return AgentResponse(
                to=message.from_number,
                message="Hello! I received your message. I'm currently experiencing some technical issues, but I'll get back to you soon!",
                message_type="text"
            )
    
    async def _send_agent_response(self, response: AgentResponse, account: Dict[str, Any]) -> bool:
        """Send agent response back via WhatsApp"""
        try:
            # Find appropriate BSP provider
            provider = self._get_provider_for_account(account)
            if not provider:
                logger.error("No BSP provider available for account")
                return False
            
            # Create send message request
            send_request = SendMessageRequest(
                to=response.to,
                message_type=response.message_type,
                text=response.message if response.message_type == "text" else None
            )
            
            # Send via BSP provider
            result = await provider.send_message(send_request, account['bsp_sender_id'], account['phone_number'])
            logger.info(f"Agent response sent: {result.message_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send agent response: {str(e)}")
            return False
    
    async def _process_message_status(self, status: Any, account: Dict[str, Any]):
        """Process message status update"""
        try:
            # Log status update for analytics
            await self.firebase.create_webhook_log({
                "webhook_id": f"status_{status.id}",
                "account_id": account['id'],
                "payload": status.dict(),
                "processed_messages": [],
                "status": "status_update",
                "processing_time_ms": 50
            })
            
            logger.info(f"Message {status.id} status: {status.status}")
            
        except Exception as e:
            logger.error(f"Status processing failed: {str(e)}")
    
    async def _find_account_by_phone_id(self, phone_number_id: str) -> Optional[Dict[str, Any]]:
        """Find managed account by WhatsApp phone number ID"""
        try:
            # This is a simplified lookup - in production you'd have a proper mapping
            # For now, we'll search through all accounts
            # You might want to add an index on phone_number_id in Firestore
            
            # Get all collections and search
            # This is inefficient but works for demo - optimize for production
            collections = list(self.firebase.db.collections())
            for collection in collections:
                if collection.id == self.settings.managed_accounts_collection:
                    docs = collection.stream()
                    for doc in docs:
                        data = doc.to_dict()
                        data['id'] = doc.id
                        # Match by phone number ID (you'd store this during account creation)
                        if data.get('whatsapp_phone_id') == phone_number_id:
                            return data
            
            return None
            
        except Exception as e:
            logger.error(f"Account lookup failed: {str(e)}")
            return None
    
    def _get_provider_for_account(self, account: Dict[str, Any]) -> Optional[BSPProvider]:
        """Get BSP provider for account"""
        # For now, default to WhatsApp Business API
        return self.bsp_providers.get('whatsapp')
    
    async def _log_webhook_processing(
        self, 
        webhook_id: str, 
        account_id: str, 
        payload: Dict[str, Any],
        processed_messages: List[ProcessedMessage],
        agent_responses: List[AgentResponse],
        status: str,
        additional_count: int = 0
    ):
        """Log webhook processing details"""
        try:
            log_data = {
                "webhook_id": webhook_id,
                "account_id": account_id,
                "payload": payload,
                "processed_messages": [msg.dict() for msg in processed_messages],
                "agent_responses": [resp.dict() for resp in agent_responses],
                "status": status,
                "processing_time_ms": 100,  # Placeholder
                "additional_count": additional_count
            }
            
            await self.firebase.create_webhook_log(log_data)
            
        except Exception as e:
            logger.error(f"Webhook logging failed: {str(e)}")
    
    async def _log_webhook_error(
        self, 
        webhook_id: str, 
        webhook_data: WhatsAppWebhook, 
        error_message: str,
        processing_time: int
    ):
        """Log webhook processing error"""
        try:
            log_data = {
                "webhook_id": webhook_id,
                "account_id": "unknown",
                "payload": webhook_data.dict(),
                "processed_messages": [],
                "agent_responses": [],
                "status": "error",
                "error_message": error_message,
                "processing_time_ms": processing_time
            }
            
            await self.firebase.create_webhook_log(log_data)
            
        except Exception as e:
            logger.error(f"Error logging failed: {str(e)}")
    
    def register_message_handler(self, message_type: str, handler: Callable):
        """Register custom message handler"""
        self._message_handlers[message_type] = handler
    
    async def get_webhook_stats(self, account_id: str, days: int = 7) -> Dict[str, Any]:
        """Get webhook processing statistics"""
        try:
            logs = await self.firebase.get_webhook_logs(account_id, limit=1000)
            
            # Calculate stats
            total_webhooks = len(logs)
            successful_webhooks = len([log for log in logs if log.get('status') == 'success'])
            error_webhooks = len([log for log in logs if log.get('status') == 'error'])
            
            total_messages = sum(len(log.get('processed_messages', [])) for log in logs)
            total_responses = sum(len(log.get('agent_responses', [])) for log in logs)
            
            avg_processing_time = sum(log.get('processing_time_ms', 0) for log in logs) / max(total_webhooks, 1)
            
            return {
                "account_id": account_id,
                "period_days": days,
                "total_webhooks": total_webhooks,
                "successful_webhooks": successful_webhooks,
                "error_webhooks": error_webhooks,
                "success_rate": successful_webhooks / max(total_webhooks, 1),
                "total_messages_processed": total_messages,
                "total_responses_sent": total_responses,
                "avg_processing_time_ms": int(avg_processing_time),
                "health_score": successful_webhooks / max(total_webhooks, 1)
            }
            
        except Exception as e:
            logger.error(f"Failed to get webhook stats: {str(e)}")
            return {
                "account_id": account_id,
                "error": str(e)
            }
    
    async def cleanup(self):
        """Cleanup resources"""
        await self._client.aclose()


def create_webhook_service(firebase_service: FirebaseService, bsp_providers: Dict[str, BSPProvider]) -> WebhookService:
    """Factory function to create webhook service"""
    return WebhookService(firebase_service, bsp_providers)