"""
Pydantic models for WhatsApp webhook payloads
"""
from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field


class WhatsAppContact(BaseModel):
    """WhatsApp contact information"""
    wa_id: str = Field(..., description="WhatsApp ID")
    profile: Optional[Dict[str, str]] = Field(None, description="Profile information")


class WhatsAppMessage(BaseModel):
    """WhatsApp message content"""
    id: str = Field(..., description="Message ID")
    from_: str = Field(..., alias="from", description="Sender phone number")
    timestamp: str = Field(..., description="Message timestamp")
    type: str = Field(..., description="Message type (text, image, audio, etc.)")
    text: Optional[Dict[str, str]] = Field(None, description="Text message content")
    image: Optional[Dict[str, Any]] = Field(None, description="Image message content")
    audio: Optional[Dict[str, Any]] = Field(None, description="Audio message content")
    video: Optional[Dict[str, Any]] = Field(None, description="Video message content")
    document: Optional[Dict[str, Any]] = Field(None, description="Document message content")
    location: Optional[Dict[str, Any]] = Field(None, description="Location message content")
    contacts: Optional[List[Dict[str, Any]]] = Field(None, description="Contact message content")
    button: Optional[Dict[str, Any]] = Field(None, description="Button interaction")
    interactive: Optional[Dict[str, Any]] = Field(None, description="Interactive message content")
    context: Optional[Dict[str, str]] = Field(None, description="Message context (reply info)")


class WhatsAppStatus(BaseModel):
    """WhatsApp message status update"""
    id: str = Field(..., description="Message ID")
    status: str = Field(..., description="Status (sent, delivered, read, failed)")
    timestamp: str = Field(..., description="Status timestamp")
    recipient_id: str = Field(..., description="Recipient phone number")
    conversation: Optional[Dict[str, Any]] = Field(None, description="Conversation info")
    pricing: Optional[Dict[str, Any]] = Field(None, description="Pricing info")
    errors: Optional[List[Dict[str, Any]]] = Field(None, description="Error details")


class WhatsAppError(BaseModel):
    """WhatsApp error information"""
    code: int = Field(..., description="Error code")
    title: str = Field(..., description="Error title")
    message: str = Field(..., description="Error message")
    error_data: Optional[Dict[str, Any]] = Field(None, description="Additional error data")


class WhatsAppValue(BaseModel):
    """WhatsApp webhook value container"""
    messaging_product: str = Field(..., description="Messaging product (whatsapp)")
    metadata: Dict[str, Any] = Field(..., description="Metadata including phone number ID")
    contacts: Optional[List[WhatsAppContact]] = Field(None, description="Contact information")
    messages: Optional[List[WhatsAppMessage]] = Field(None, description="Received messages")
    statuses: Optional[List[WhatsAppStatus]] = Field(None, description="Message status updates")
    errors: Optional[List[WhatsAppError]] = Field(None, description="Error information")


class WhatsAppChange(BaseModel):
    """WhatsApp webhook change entry"""
    value: WhatsAppValue = Field(..., description="Change value")
    field: str = Field(..., description="Changed field")


class WhatsAppEntry(BaseModel):
    """WhatsApp webhook entry"""
    id: str = Field(..., description="WhatsApp Business Account ID")
    changes: List[WhatsAppChange] = Field(..., description="List of changes")


class WhatsAppWebhook(BaseModel):
    """Complete WhatsApp webhook payload"""
    object: str = Field(..., description="Object type (whatsapp_business_account)")
    entry: List[WhatsAppEntry] = Field(..., description="List of entries")


class WebhookVerification(BaseModel):
    """Webhook verification challenge"""
    hub_mode: str = Field(..., alias="hub.mode", description="Verification mode")
    hub_challenge: str = Field(..., alias="hub.challenge", description="Challenge token")
    hub_verify_token: str = Field(..., alias="hub.verify_token", description="Verification token")


class ProcessedMessage(BaseModel):
    """Processed message for routing to agent"""
    message_id: str = Field(..., description="Original message ID")
    from_number: str = Field(..., description="Sender phone number")
    to_number: str = Field(..., description="Recipient phone number (business)")
    message_type: str = Field(..., description="Message type")
    content: str = Field(..., description="Message content (text or description)")
    timestamp: datetime = Field(..., description="Message timestamp")
    context: Optional[Dict[str, Any]] = Field(None, description="Message context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentResponse(BaseModel):
    """Response from agent for WhatsApp message"""
    to: str = Field(..., description="Recipient phone number")
    message: str = Field(..., description="Response message")
    message_type: str = Field(default="text", description="Response message type")
    context: Optional[Dict[str, Any]] = Field(None, description="Response context")


class WebhookLog(BaseModel):
    """Webhook processing log entry"""
    id: str = Field(..., description="Log entry ID")
    webhook_id: str = Field(..., description="Webhook identifier")
    account_id: str = Field(..., description="Account identifier")
    payload: Dict[str, Any] = Field(..., description="Original webhook payload")
    processed_messages: List[ProcessedMessage] = Field(default_factory=list, description="Processed messages")
    agent_responses: List[AgentResponse] = Field(default_factory=list, description="Agent responses")
    status: str = Field(..., description="Processing status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Log timestamp")


class SendMessageRequest(BaseModel):
    """Request to send WhatsApp message"""
    to: str = Field(..., description="Recipient phone number")
    message_type: str = Field(default="text", description="Message type")
    text: Optional[str] = Field(None, description="Text message content")
    image: Optional[Dict[str, Any]] = Field(None, description="Image message content")
    audio: Optional[Dict[str, Any]] = Field(None, description="Audio message content")
    video: Optional[Dict[str, Any]] = Field(None, description="Video message content")
    document: Optional[Dict[str, Any]] = Field(None, description="Document message content")
    template: Optional[Dict[str, Any]] = Field(None, description="Template message content")
    context: Optional[Dict[str, str]] = Field(None, description="Message context (reply)")


class SendMessageResponse(BaseModel):
    """Response from sending WhatsApp message"""
    message_id: str = Field(..., description="Sent message ID")
    status: str = Field(..., description="Send status")
    recipient: str = Field(..., description="Recipient phone number")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Send timestamp")