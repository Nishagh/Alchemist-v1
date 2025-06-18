#!/usr/bin/env python3
"""
WhatsApp Service Module for Universal Agent Template

This module provides WhatsApp integration functionality that dynamically loads
configuration from Firestore and handles WhatsApp webhook messages.
"""

import os
import logging
import hashlib
import hmac
import json
from typing import Dict, Any, Optional, List
from datetime import datetime

import httpx
from fastapi import Request, HTTPException

logger = logging.getLogger(__name__)


class WhatsAppService:
    """
    WhatsApp service for handling webhook messages and sending responses.
    Dynamically loads configuration from Firestore agent config.
    """
    
    def __init__(self, agent_config: Dict[str, Any]):
        """Initialize WhatsApp service with agent configuration"""
        self.agent_config = agent_config
        self.whatsapp_config = agent_config.get('whatsapp', {})
        self.enabled = self.whatsapp_config.get('enabled', False)
        
        if self.enabled:
            self.phone_id = self.whatsapp_config.get('phone_id')
            self.access_token = self.whatsapp_config.get('access_token')
            self.verify_token = self.whatsapp_config.get('verify_token')
            self.app_secret = self.whatsapp_config.get('app_secret')
            
            # Validate required configuration
            if not all([self.phone_id, self.access_token, self.verify_token]):
                logger.warning("WhatsApp configuration incomplete - service disabled")
                self.enabled = False
            else:
                logger.info(f"WhatsApp service initialized for phone ID: {self.phone_id}")
        else:
            logger.info("WhatsApp integration disabled - no configuration found")
    
    def is_enabled(self) -> bool:
        """Check if WhatsApp integration is enabled and properly configured"""
        return self.enabled
    
    async def verify_webhook(self, hub_mode: str, hub_challenge: str, hub_verify_token: str) -> str:
        """
        Verify WhatsApp webhook subscription.
        
        Args:
            hub_mode: The mode of the request (should be 'subscribe')
            hub_challenge: The challenge string to echo back
            hub_verify_token: The verify token to validate
            
        Returns:
            The challenge string if verification succeeds
            
        Raises:
            HTTPException: If verification fails
        """
        if not self.enabled:
            raise HTTPException(status_code=404, detail="WhatsApp integration not configured")
        
        if hub_mode == "subscribe" and hub_verify_token == self.verify_token:
            logger.info("WhatsApp webhook verification successful")
            return hub_challenge
        else:
            logger.warning(f"WhatsApp webhook verification failed: mode={hub_mode}, token_match={hub_verify_token == self.verify_token}")
            raise HTTPException(status_code=403, detail="Verification failed")
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """
        Verify the webhook signature to ensure the request is from WhatsApp.
        
        Args:
            payload: The raw request body
            signature: The X-Hub-Signature-256 header value
            
        Returns:
            True if signature is valid, False otherwise
        """
        if not self.app_secret:
            logger.warning("No app_secret configured - skipping signature verification")
            return True
        
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                self.app_secret.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def parse_webhook_message(self, webhook_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Parse incoming WhatsApp webhook message.
        
        Args:
            webhook_data: The webhook JSON data
            
        Returns:
            Parsed message data or None if not a message
        """
        try:
            entry = webhook_data.get('entry', [])
            if not entry:
                return None
            
            changes = entry[0].get('changes', [])
            if not changes:
                return None
            
            value = changes[0].get('value', {})
            messages = value.get('messages', [])
            
            if not messages:
                # Check for status updates
                statuses = value.get('statuses', [])
                if statuses:
                    logger.info(f"Received message status update: {statuses[0].get('status')}")
                return None
            
            message = messages[0]
            contact = value.get('contacts', [{}])[0]
            
            parsed_message = {
                'message_id': message.get('id'),
                'from_phone': message.get('from'),
                'timestamp': message.get('timestamp'),
                'type': message.get('type'),
                'contact_name': contact.get('profile', {}).get('name', 'Unknown'),
                'text': None,
                'media': None
            }
            
            # Extract message content based on type
            if message.get('type') == 'text':
                parsed_message['text'] = message.get('text', {}).get('body', '')
            elif message.get('type') == 'image':
                parsed_message['media'] = {
                    'type': 'image',
                    'id': message.get('image', {}).get('id'),
                    'caption': message.get('image', {}).get('caption', '')
                }
            elif message.get('type') == 'document':
                parsed_message['media'] = {
                    'type': 'document',
                    'id': message.get('document', {}).get('id'),
                    'filename': message.get('document', {}).get('filename', 'document')
                }
            elif message.get('type') == 'audio':
                parsed_message['media'] = {
                    'type': 'audio',
                    'id': message.get('audio', {}).get('id')
                }
            
            logger.info(f"Parsed WhatsApp message from {parsed_message['from_phone']}: {parsed_message['type']}")
            return parsed_message
            
        except Exception as e:
            logger.error(f"Error parsing WhatsApp webhook message: {str(e)}")
            return None
    
    async def send_text_message(self, to_phone: str, message: str) -> bool:
        """
        Send a text message via WhatsApp API.
        
        Args:
            to_phone: Recipient phone number
            message: Message text to send
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            logger.error("WhatsApp service not enabled")
            return False
        
        try:
            # Split long messages
            max_length = 4096  # WhatsApp text message limit
            if len(message) > max_length:
                # Send in chunks
                for i in range(0, len(message), max_length):
                    chunk = message[i:i + max_length]
                    await self._send_single_message(to_phone, chunk)
                return True
            else:
                return await self._send_single_message(to_phone, message)
                
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {str(e)}")
            return False
    
    async def _send_single_message(self, to_phone: str, message: str) -> bool:
        """Send a single text message via WhatsApp API"""
        url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
        
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "messaging_product": "whatsapp",
            "to": to_phone,
            "type": "text",
            "text": {"body": message}
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                logger.info(f"WhatsApp message sent successfully to {to_phone}")
                return True
            else:
                logger.error(f"Failed to send WhatsApp message: {response.status_code} - {response.text}")
                return False
    
    async def send_quick_reply(self, to_phone: str, message: str, buttons: List[str]) -> bool:
        """
        Send a message with quick reply buttons.
        
        Args:
            to_phone: Recipient phone number
            message: Message text
            buttons: List of button labels (max 3)
            
        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            # Limit to 3 buttons as per WhatsApp API
            button_objects = []
            for i, button_text in enumerate(buttons[:3]):
                button_objects.append({
                    "type": "reply",
                    "reply": {
                        "id": f"btn_{i}",
                        "title": button_text[:20]  # Button title limit
                    }
                })
            
            payload = {
                "messaging_product": "whatsapp",
                "to": to_phone,
                "type": "interactive",
                "interactive": {
                    "type": "button",
                    "body": {"text": message},
                    "action": {"buttons": button_objects}
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    logger.info(f"WhatsApp quick reply sent successfully to {to_phone}")
                    return True
                else:
                    logger.error(f"Failed to send WhatsApp quick reply: {response.status_code} - {response.text}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending WhatsApp quick reply: {str(e)}")
            return False
    
    async def mark_as_read(self, message_id: str) -> bool:
        """
        Mark a message as read.
        
        Args:
            message_id: The WhatsApp message ID to mark as read
            
        Returns:
            True if marked successfully, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            url = f"https://graph.facebook.com/v18.0/{self.phone_id}/messages"
            
            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, json=payload)
                
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Error marking WhatsApp message as read: {str(e)}")
            return False
    
    def format_agent_response(self, response: str) -> str:
        """
        Format agent response for WhatsApp delivery.
        
        Args:
            response: The agent's response text
            
        Returns:
            Formatted response suitable for WhatsApp
        """
        # Remove markdown formatting that WhatsApp doesn't support well
        formatted = response.replace('**', '*')  # Convert bold markdown to WhatsApp format
        formatted = formatted.replace('__', '_')  # Convert underline markdown to WhatsApp format
        
        # Remove code blocks for better readability
        formatted = formatted.replace('```', '```\n')
        
        return formatted.strip()
    
    def get_conversation_user_id(self, phone_number: str) -> str:
        """
        Generate a consistent user ID for conversations based on phone number.
        
        Args:
            phone_number: WhatsApp phone number
            
        Returns:
            Consistent user ID for conversation tracking
        """
        return f"whatsapp_{phone_number}"