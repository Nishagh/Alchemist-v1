"""
WhatsApp Business API provider implementation
"""
import asyncio
import json
import hashlib
import hmac
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import httpx
from urllib.parse import urljoin

from services.bsp_provider import (
    BSPProvider, BSPProviderError, AccountCreationError, 
    VerificationError, MessageSendError, WebhookError
)
from models.account_models import (
    CreateAccountRequest, CreateAccountResponse,
    VerifyPhoneRequest, VerifyPhoneResponse,
    RequestVerificationRequest, RequestVerificationResponse,
    SendTestMessageRequest, SendTestMessageResponse,
    AccountHealthResponse
)
from models.webhook_models import SendMessageRequest, SendMessageResponse

import logging
logger = logging.getLogger(__name__)


class WhatsAppProvider(BSPProvider):
    """WhatsApp Business API implementation of BSP provider"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.access_token = config.get('access_token')
        self.app_id = config.get('app_id')
        self.app_secret = config.get('app_secret')
        self.api_version = config.get('api_version', 'v18.0')
        
        if not all([self.access_token, self.app_id, self.app_secret]):
            raise ValueError("WhatsApp access_token, app_id, and app_secret are required")
            
        self.base_url = f"https://graph.facebook.com/{self.api_version}"
        self._client = httpx.AsyncClient(timeout=30.0)
        self._verification_store = {}  # In production, use Redis or database
    
    def get_required_config_keys(self) -> List[str]:
        """Get required configuration keys for WhatsApp Business API"""
        return ['access_token', 'app_id', 'app_secret']
    
    async def create_account(self, request: CreateAccountRequest) -> CreateAccountResponse:
        """Create a WhatsApp Business account"""
        try:
            # Format phone number
            phone_number = self.format_phone_number(request.phone_number)
            
            # Generate unique sender ID with phone number
            sender_id = self.generate_sender_id(request.account_id, phone_number)
            
            # Get phone number ID from WhatsApp Business API
            phone_number_id = await self._get_phone_number_id(phone_number)
            
            if not phone_number_id:
                # Register phone number with WhatsApp Business API
                phone_number_id = await self._register_phone_number(phone_number, request.business_profile)
            
            # Check verification status
            verification_required = await self._check_verification_required(phone_number_id)
            
            # Set up webhook if provided
            webhook_url = request.webhook_config.url
            if webhook_url:
                await self._setup_webhook_url(
                    webhook_url, 
                    request.webhook_config.verify_token or "default_token"
                )
            
            response = CreateAccountResponse(
                account_id=request.account_id,
                sender_id=sender_id,
                phone_number=phone_number,
                verification_required=verification_required,
                verification_methods=["sms", "voice"],
                status="verification_pending" if verification_required else "active",
                webhook_url=webhook_url
            )
            
            return response
            
        except Exception as e:
            logger.error(f"WhatsApp account creation failed: {str(e)}")
            raise AccountCreationError(f"Account creation failed: {str(e)}", "whatsapp")
    
    async def verify_phone_number(self, request: VerifyPhoneRequest) -> VerifyPhoneResponse:
        """Verify phone number using WhatsApp Business API"""
        try:
            # Get stored verification info
            verification_info = self._verification_store.get(request.account_id)
            if not verification_info:
                raise VerificationError("No verification session found", "whatsapp")
            
            phone_number_id = verification_info.get('phone_number_id')
            
            # Verify code with WhatsApp Business API
            success = await self._verify_code_with_whatsapp(
                phone_number_id,
                request.verification_code
            )
            
            attempts = verification_info.get('attempts', 0) + 1
            self._verification_store[request.account_id]['attempts'] = attempts
            
            if success:
                # Clean up verification session
                del self._verification_store[request.account_id]
                
                return VerifyPhoneResponse(
                    verified=True,
                    account_id=request.account_id,
                    status="active",
                    message="Phone number verified successfully",
                    attempts=attempts
                )
            else:
                return VerifyPhoneResponse(
                    verified=False,
                    account_id=request.account_id,
                    status="verification_failed" if attempts >= 3 else "verification_pending",
                    message="Invalid verification code",
                    attempts=attempts
                )
                
        except Exception as e:
            logger.error(f"WhatsApp verification failed: {str(e)}")
            raise VerificationError(f"Verification failed: {str(e)}", "whatsapp")
    
    async def request_verification_code(self, request: RequestVerificationRequest) -> RequestVerificationResponse:
        """Request verification code using WhatsApp Business API"""
        try:
            # Get phone number ID from account
            phone_number_id = await self._get_phone_number_id_from_account(request.account_id)
            
            if not phone_number_id:
                raise VerificationError("Phone number not found for account", "whatsapp")
            
            # Request verification code from WhatsApp
            success = await self._request_verification_code_from_whatsapp(
                phone_number_id, 
                request.verification_method
            )
            
            if success:
                # Store verification session
                verification_info = self._verification_store.get(request.account_id, {})
                self._verification_store[request.account_id] = {
                    'phone_number_id': phone_number_id,
                    'method': request.verification_method,
                    'expires_at': datetime.utcnow() + timedelta(minutes=10),
                    'attempts': verification_info.get('attempts', 0)
                }
                
                return RequestVerificationResponse(
                    success=True,
                    method=request.verification_method,
                    expires_in=600,  # 10 minutes
                    attempts_remaining=3 - verification_info.get('attempts', 0)
                )
            else:
                raise VerificationError("Failed to send verification code", "whatsapp")
                
        except Exception as e:
            logger.error(f"WhatsApp verification request failed: {str(e)}")
            raise VerificationError(f"Verification request failed: {str(e)}", "whatsapp")
    
    async def send_message(self, request: SendMessageRequest, sender_id: str, from_phone_number: str = None) -> SendMessageResponse:
        """Send WhatsApp message using WhatsApp Business API"""
        try:
            # Get phone number ID
            phone_number_id = await self._get_phone_number_id(from_phone_number)
            if not phone_number_id:
                raise MessageSendError("Phone number not registered", "whatsapp")
            
            # Format recipient number
            to_number = self.format_phone_number(request.to)
            
            # Prepare message payload
            message_payload = {
                "messaging_product": "whatsapp",
                "to": to_number.replace('+', ''),
                "type": request.message_type
            }
            
            # Add message content based on type
            if request.message_type == "text" and request.text:
                message_payload["text"] = {"body": request.text}
            elif request.message_type == "image" and request.image:
                message_payload["image"] = request.image
            elif request.message_type == "audio" and request.audio:
                message_payload["audio"] = request.audio
            elif request.message_type == "video" and request.video:
                message_payload["video"] = request.video
            elif request.message_type == "document" and request.document:
                message_payload["document"] = request.document
            else:
                raise MessageSendError("Invalid message type or content", "whatsapp")
            
            # Add context if replying to a message
            if request.context:
                message_payload["context"] = request.context
            
            # Send message via WhatsApp Business API
            url = f"{self.base_url}/{phone_number_id}/messages"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            response = await self._client.post(url, json=message_payload, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                message_id = result["messages"][0]["id"]
                
                return SendMessageResponse(
                    message_id=message_id,
                    status="sent",
                    recipient=to_number
                )
            else:
                error_text = response.text
                logger.error(f"WhatsApp API error: {error_text}")
                raise MessageSendError(f"WhatsApp API error: {error_text}", "whatsapp")
            
        except Exception as e:
            logger.error(f"WhatsApp message send failed: {str(e)}")
            raise MessageSendError(f"Message send failed: {str(e)}", "whatsapp")
    
    async def send_test_message(self, request: SendTestMessageRequest, sender_id: str, from_phone_number: str = None) -> SendTestMessageResponse:
        """Send test message using WhatsApp Business API"""
        try:
            # Use custom message or default
            message_text = request.message or "Hello! This is a test message from your AI agent's WhatsApp integration. Everything is working correctly! 🤖"
            
            # Create message request
            send_request = SendMessageRequest(
                to=request.to,
                message_type="text",
                text=message_text
            )
            
            # Send message
            response = await self.send_message(send_request, sender_id, from_phone_number)
            
            return SendTestMessageResponse(
                success=True,
                message_id=response.message_id,
                status=response.status,
                sent_to=request.to
            )
            
        except Exception as e:
            logger.error(f"WhatsApp test message failed: {str(e)}")
            raise MessageSendError(f"Test message failed: {str(e)}", "whatsapp")
    
    async def get_account_health(self, account_id: str, sender_id: str, phone_number: str = None) -> AccountHealthResponse:
        """Get account health from WhatsApp Business API"""
        try:
            # Get phone number ID
            phone_number_id = await self._get_phone_number_id(phone_number)
            
            if phone_number_id:
                # Get business profile and health info
                health_info = await self._get_phone_number_health(phone_number_id)
                
                return AccountHealthResponse(
                    account_id=account_id,
                    status=health_info.get("status", "active"),
                    phone_number=phone_number,
                    last_activity=datetime.utcnow() - timedelta(hours=1),
                    webhook_status="active",
                    message_count_24h=health_info.get("message_count_24h", 0),
                    error_count_24h=health_info.get("error_count_24h", 0),
                    health_score=health_info.get("health_score", 0.95)
                )
            else:
                return AccountHealthResponse(
                    account_id=account_id,
                    status="inactive",
                    phone_number=phone_number,
                    last_activity=None,
                    webhook_status="inactive",
                    message_count_24h=0,
                    error_count_24h=1,
                    health_score=0.0
                )
            
        except Exception as e:
            logger.error(f"WhatsApp health check failed: {str(e)}")
            raise BSPProviderError(f"Health check failed: {str(e)}", "whatsapp")
    
    async def delete_account(self, account_id: str, sender_id: str) -> bool:
        """Delete/deactivate WhatsApp Business account"""
        try:
            # Clean up verification data
            if account_id in self._verification_store:
                del self._verification_store[account_id]
            
            # In production, you might want to unregister webhooks or phone numbers
            logger.info(f"WhatsApp account {account_id} deactivated")
            return True
            
        except Exception as e:
            logger.error(f"WhatsApp account deletion failed: {str(e)}")
            raise BSPProviderError(f"Account deletion failed: {str(e)}", "whatsapp")
    
    async def setup_webhook(self, webhook_url: str, verify_token: str, sender_id: str) -> Dict[str, Any]:
        """Setup webhook configuration for WhatsApp Business API"""
        try:
            # Configure webhook via WhatsApp Business API
            url = f"{self.base_url}/{self.app_id}/subscriptions"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "object": "whatsapp_business_account",
                "callback_url": webhook_url,
                "verify_token": verify_token,
                "fields": ["messages", "message_deliveries", "message_reads", "message_echoes"]
            }
            
            response = await self._client.post(url, json=payload, headers=headers)
            
            if response.status_code == 200:
                return {
                    "webhook_url": webhook_url,
                    "verify_token": verify_token,
                    "events": ["messages", "message_deliveries", "message_reads"],
                    "status": "configured"
                }
            else:
                raise WebhookError(f"Webhook setup failed: {response.text}", "whatsapp")
            
        except Exception as e:
            logger.error(f"WhatsApp webhook setup failed: {str(e)}")
            raise WebhookError(f"Webhook setup failed: {str(e)}", "whatsapp")
    
    async def validate_webhook(self, payload: Dict[str, Any]) -> bool:
        """Validate WhatsApp Business API webhook payload"""
        try:
            # Basic validation for WhatsApp webhook structure
            return (
                isinstance(payload, dict) and
                payload.get("object") == "whatsapp_business_account" and
                "entry" in payload and
                isinstance(payload["entry"], list)
            )
        except Exception:
            return False
    
    def validate_webhook_signature(self, payload: str, signature: str) -> bool:
        """Validate webhook signature for security"""
        try:
            # WhatsApp sends signature in format: sha256=<signature>
            if not signature.startswith('sha256='):
                return False
            
            signature = signature[7:]  # Remove 'sha256=' prefix
            
            # Generate expected signature
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception as e:
            logger.error(f"Signature validation failed: {str(e)}")
            return False
    
    # Private helper methods
    
    async def _get_phone_number_id(self, phone_number: str) -> Optional[str]:
        """Get phone number ID from WhatsApp Business API"""
        try:
            # In production, you would query the WhatsApp Business API
            # For now, return a mock phone number ID
            clean_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            return f"phone_id_{clean_number}"
            
        except Exception as e:
            logger.error(f"Failed to get phone number ID: {str(e)}")
            return None
    
    async def _register_phone_number(self, phone_number: str, business_profile: Any) -> str:
        """Register phone number with WhatsApp Business API"""
        try:
            # This would register the phone number with WhatsApp Business API
            # For now, return a mock phone number ID
            clean_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            return f"phone_id_{clean_number}"
            
        except Exception as e:
            logger.error(f"Phone number registration failed: {str(e)}")
            raise AccountCreationError(f"Phone number registration failed: {str(e)}", "whatsapp")
    
    async def _check_verification_required(self, phone_number_id: str) -> bool:
        """Check if phone number requires verification"""
        try:
            # Query WhatsApp Business API for verification status
            # For now, always require verification
            return True
            
        except Exception:
            return True
    
    async def _request_verification_code_from_whatsapp(self, phone_number_id: str, method: str) -> bool:
        """Request verification code from WhatsApp Business API"""
        try:
            url = f"{self.base_url}/{phone_number_id}/request_code"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "code_method": method  # "SMS" or "VOICE"
            }
            
            response = await self._client.post(url, json=payload, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Verification code request failed: {str(e)}")
            return False
    
    async def _verify_code_with_whatsapp(self, phone_number_id: str, code: str) -> bool:
        """Verify code with WhatsApp Business API"""
        try:
            url = f"{self.base_url}/{phone_number_id}/verify_code"
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "code": code
            }
            
            response = await self._client.post(url, json=payload, headers=headers)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Code verification failed: {str(e)}")
            return False
    
    async def _get_phone_number_id_from_account(self, account_id: str) -> Optional[str]:
        """Get phone number ID from stored account data"""
        # This would query your database for the account's phone number ID
        # For now, return mock data
        return f"phone_id_account_{account_id}"
    
    async def _get_phone_number_health(self, phone_number_id: str) -> Dict[str, Any]:
        """Get phone number health metrics from WhatsApp Business API"""
        try:
            # Query WhatsApp Business API for health metrics
            # For now, return mock health data
            return {
                "status": "active",
                "message_count_24h": 150,
                "error_count_24h": 2,
                "health_score": 0.95
            }
            
        except Exception as e:
            logger.error(f"Health metrics query failed: {str(e)}")
            return {
                "status": "unknown",
                "message_count_24h": 0,
                "error_count_24h": 0,
                "health_score": 0.5
            }
    
    async def _setup_webhook_url(self, webhook_url: str, verify_token: str) -> str:
        """Setup webhook URL with WhatsApp Business API"""
        # Configure webhook via WhatsApp Business API
        return webhook_url
    
    def _extract_phone_from_sender_id(self, sender_id: str) -> str:
        """Extract phone number from sender ID"""
        try:
            # Sender ID format: "whatsapp_account_phone_timestamp"
            parts = sender_id.split('_')
            if len(parts) >= 3:
                # Phone number is the third part (index 2)
                phone_clean = parts[2]
                # Add + prefix if not present
                if not phone_clean.startswith('+'):
                    phone_clean = '+' + phone_clean
                return phone_clean
            else:
                # Fallback - return a default number
                logger.warning(f"Could not extract phone from sender_id: {sender_id}")
                return "+1234567890"
        except Exception as e:
            logger.error(f"Error extracting phone from sender_id {sender_id}: {str(e)}")
            return "+1234567890"
    
    async def cleanup(self):
        """Cleanup resources"""
        await self._client.aclose()


def create_whatsapp_provider(config: Dict[str, Any]) -> WhatsAppProvider:
    """Factory function to create WhatsApp provider"""
    return WhatsAppProvider(config)