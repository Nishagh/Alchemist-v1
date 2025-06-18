"""
Abstract BSP (Business Solution Provider) interface for WhatsApp integrations
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime

from models.account_models import (
    CreateAccountRequest, CreateAccountResponse,
    VerifyPhoneRequest, VerifyPhoneResponse,
    RequestVerificationRequest, RequestVerificationResponse,
    SendTestMessageRequest, SendTestMessageResponse,
    AccountHealthResponse
)
from models.webhook_models import SendMessageRequest, SendMessageResponse


class BSPProvider(ABC):
    """Abstract base class for BSP providers"""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize BSP provider with configuration"""
        self.config = config
        self.provider_name = self.__class__.__name__.lower().replace('provider', '')
    
    @abstractmethod
    async def create_account(self, request: CreateAccountRequest) -> CreateAccountResponse:
        """Create a new WhatsApp Business account"""
        pass
    
    @abstractmethod
    async def verify_phone_number(self, request: VerifyPhoneRequest) -> VerifyPhoneResponse:
        """Verify phone number ownership"""
        pass
    
    @abstractmethod
    async def request_verification_code(self, request: RequestVerificationRequest) -> RequestVerificationResponse:
        """Request a new verification code"""
        pass
    
    @abstractmethod
    async def send_message(self, request: SendMessageRequest, sender_id: str, from_phone_number: str = None) -> SendMessageResponse:
        """Send a WhatsApp message"""
        pass
    
    @abstractmethod
    async def send_test_message(self, request: SendTestMessageRequest, sender_id: str, from_phone_number: str = None) -> SendTestMessageResponse:
        """Send a test message"""
        pass
    
    @abstractmethod
    async def get_account_health(self, account_id: str, sender_id: str, phone_number: str = None) -> AccountHealthResponse:
        """Get account health status"""
        pass
    
    @abstractmethod
    async def delete_account(self, account_id: str, sender_id: str) -> bool:
        """Delete/deactivate an account"""
        pass
    
    @abstractmethod
    async def setup_webhook(self, webhook_url: str, verify_token: str, sender_id: str) -> Dict[str, Any]:
        """Setup webhook configuration"""
        pass
    
    @abstractmethod
    async def validate_webhook(self, payload: Dict[str, Any]) -> bool:
        """Validate incoming webhook payload"""
        pass
    
    def get_provider_name(self) -> str:
        """Get provider name"""
        return self.provider_name
    
    def get_supported_message_types(self) -> List[str]:
        """Get supported message types"""
        return ["text", "image", "audio", "video", "document"]
    
    def get_supported_verification_methods(self) -> List[str]:
        """Get supported verification methods"""
        return ["sms", "voice"]
    
    def format_phone_number(self, phone_number: str) -> str:
        """Format phone number for the provider"""
        # Remove any non-digit characters except +
        cleaned = ''.join(c for c in phone_number if c.isdigit() or c == '+')
        
        # Ensure it starts with +
        if not cleaned.startswith('+'):
            cleaned = '+' + cleaned
            
        return cleaned
    
    def generate_sender_id(self, account_id: str, phone_number: str = None) -> str:
        """Generate a unique sender ID"""
        timestamp = str(int(datetime.utcnow().timestamp()))
        if phone_number:
            # Clean phone number for ID (remove + and spaces)
            clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')
            return f"{self.provider_name}_{account_id}_{clean_phone}_{timestamp}"
        else:
            return f"{self.provider_name}_{account_id}_{timestamp}"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check provider health status"""
        return {
            "provider": self.provider_name,
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "config_valid": await self._validate_config()
        }
    
    async def _validate_config(self) -> bool:
        """Validate provider configuration"""
        try:
            required_keys = self.get_required_config_keys()
            for key in required_keys:
                if key not in self.config or not self.config[key]:
                    return False
            return True
        except Exception:
            return False
    
    @abstractmethod
    def get_required_config_keys(self) -> List[str]:
        """Get list of required configuration keys"""
        pass


class BSPProviderError(Exception):
    """Base exception for BSP provider errors"""
    
    def __init__(self, message: str, provider: str, error_code: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.provider = provider
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.utcnow()


class AccountCreationError(BSPProviderError):
    """Exception raised when account creation fails"""
    pass


class VerificationError(BSPProviderError):
    """Exception raised when phone verification fails"""
    pass


class MessageSendError(BSPProviderError):
    """Exception raised when message sending fails"""
    pass


class WebhookError(BSPProviderError):
    """Exception raised when webhook operations fail"""
    pass


class ConfigurationError(BSPProviderError):
    """Exception raised when provider configuration is invalid"""
    pass