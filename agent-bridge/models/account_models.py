"""
Pydantic models for WhatsApp managed account operations
"""
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
import phonenumbers


class BusinessProfile(BaseModel):
    """Business profile information for WhatsApp Business account"""
    name: str = Field(..., min_length=1, max_length=100, description="Business name")
    industry: str = Field(default="technology", description="Business industry")
    description: Optional[str] = Field(None, max_length=500, description="Business description")
    website: Optional[str] = Field(None, description="Business website URL")
    email: Optional[str] = Field(None, description="Business email address")


class WebhookConfig(BaseModel):
    """Webhook configuration for WhatsApp messaging"""
    url: str = Field(..., description="Webhook URL for receiving messages")
    events: List[str] = Field(
        default=["message.received", "message.delivered", "message.read"],
        description="Events to subscribe to"
    )
    verify_token: Optional[str] = Field(None, description="Webhook verification token")


class CreateAccountRequest(BaseModel):
    """Request model for creating a managed WhatsApp account"""
    account_id: str = Field(..., description="Unique account identifier")
    phone_number: str = Field(..., description="WhatsApp Business phone number")
    business_profile: BusinessProfile = Field(..., description="Business profile information")
    webhook_config: WebhookConfig = Field(..., description="Webhook configuration")
    agent_webhook_url: Optional[str] = Field(None, description="AI agent webhook URL for message routing")
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate phone number format"""
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid phone number format")


class CreateAccountResponse(BaseModel):
    """Response model for account creation"""
    account_id: str = Field(..., description="Account identifier")
    sender_id: str = Field(..., description="BSP sender identifier")
    phone_number: str = Field(..., description="Formatted phone number")
    verification_required: bool = Field(..., description="Whether phone verification is required")
    verification_methods: List[str] = Field(default=["sms", "voice"], description="Available verification methods")
    status: str = Field(..., description="Account status")
    webhook_url: str = Field(..., description="Configured webhook URL")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")


class VerifyPhoneRequest(BaseModel):
    """Request model for phone number verification"""
    account_id: str = Field(..., description="Account identifier")
    verification_code: str = Field(..., min_length=4, max_length=8, description="Verification code")
    verification_method: str = Field(default="sms", description="Verification method used")
    
    @validator('verification_code')
    def validate_verification_code(cls, v):
        """Validate verification code contains only digits"""
        if not v.isdigit():
            raise ValueError("Verification code must contain only digits")
        return v


class VerifyPhoneResponse(BaseModel):
    """Response model for phone verification"""
    verified: bool = Field(..., description="Whether verification was successful")
    account_id: str = Field(..., description="Account identifier")
    status: str = Field(..., description="Updated account status")
    message: str = Field(..., description="Verification result message")
    attempts: int = Field(..., description="Number of verification attempts")


class RequestVerificationRequest(BaseModel):
    """Request model for requesting verification code"""
    account_id: str = Field(..., description="Account identifier")
    verification_method: str = Field(default="sms", description="Verification method (sms, voice)")
    
    @validator('verification_method')
    def validate_verification_method(cls, v):
        """Validate verification method"""
        if v not in ["sms", "voice"]:
            raise ValueError("Verification method must be 'sms' or 'voice'")
        return v


class RequestVerificationResponse(BaseModel):
    """Response model for verification code request"""
    success: bool = Field(..., description="Whether request was successful")
    method: str = Field(..., description="Verification method used")
    expires_in: int = Field(..., description="Code expiry time in seconds")
    attempts_remaining: int = Field(..., description="Remaining verification attempts")


class SendTestMessageRequest(BaseModel):
    """Request model for sending test messages"""
    account_id: str = Field(..., description="Account identifier")
    to: str = Field(..., description="Recipient phone number")
    message: Optional[str] = Field(None, description="Custom test message")
    
    @validator('to')
    def validate_recipient_phone(cls, v):
        """Validate recipient phone number"""
        try:
            parsed = phonenumbers.parse(v, None)
            if not phonenumbers.is_valid_number(parsed):
                raise ValueError("Invalid recipient phone number")
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError("Invalid recipient phone number format")


class SendTestMessageResponse(BaseModel):
    """Response model for test message sending"""
    success: bool = Field(..., description="Whether message was sent successfully")
    message_id: str = Field(..., description="Message identifier")
    status: str = Field(..., description="Message status")
    sent_to: str = Field(..., description="Recipient phone number")


class DeleteAccountRequest(BaseModel):
    """Request model for account deletion"""
    account_id: str = Field(..., description="Account identifier")
    bsp_account_id: Optional[str] = Field(None, description="BSP-specific account ID")
    sender_id: Optional[str] = Field(None, description="BSP sender ID")


class DeleteAccountResponse(BaseModel):
    """Response model for account deletion"""
    success: bool = Field(..., description="Whether deletion was successful")
    account_id: str = Field(..., description="Deleted account identifier")
    message: str = Field(..., description="Deletion result message")


class AccountHealthResponse(BaseModel):
    """Response model for account health check"""
    account_id: str = Field(..., description="Account identifier")
    status: str = Field(..., description="Account status")
    phone_number: str = Field(..., description="Phone number")
    last_activity: Optional[datetime] = Field(None, description="Last activity timestamp")
    webhook_status: str = Field(..., description="Webhook status")
    message_count_24h: int = Field(default=0, description="Messages sent in last 24 hours")
    error_count_24h: int = Field(default=0, description="Errors in last 24 hours")
    health_score: float = Field(..., ge=0, le=1, description="Health score (0-1)")


class ManagedAccount(BaseModel):
    """Complete managed account model"""
    id: str = Field(..., description="Account document ID")
    deployment_id: str = Field(..., description="Associated deployment ID")
    phone_number: str = Field(..., description="WhatsApp Business phone number")
    business_name: str = Field(..., description="Business name")
    business_industry: str = Field(..., description="Business industry")
    business_description: Optional[str] = Field(None, description="Business description")
    webhook_url: str = Field(..., description="Webhook URL")
    agent_webhook_url: Optional[str] = Field(None, description="AI agent webhook URL for message routing")
    bsp_account_id: Optional[str] = Field(None, description="BSP-specific account ID")
    bsp_sender_id: Optional[str] = Field(None, description="BSP sender ID")
    status: str = Field(..., description="Account status")
    verification_required: bool = Field(default=True, description="Whether verification is required")
    verification_methods: List[str] = Field(default=["sms", "voice"], description="Available verification methods")
    verification_attempts: int = Field(default=0, description="Number of verification attempts")
    last_verification_request: Optional[datetime] = Field(None, description="Last verification request time")
    verified_at: Optional[datetime] = Field(None, description="Verification completion time")
    last_test_sent: Optional[datetime] = Field(None, description="Last test message time")
    last_test_recipient: Optional[str] = Field(None, description="Last test recipient")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ErrorResponse(BaseModel):
    """Standard error response model"""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")