"""
Payment service for handling payment processing with Razorpay
Converted from Node.js paymentService.js
"""

import hmac
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone

import razorpay
from razorpay.errors import BadRequestError, SignatureVerificationError

from app.config.settings import settings

logger = logging.getLogger(__name__)


class PaymentService:
    """Service for handling payment operations with Razorpay"""
    
    def __init__(self):
        self.razorpay_client = None
        self._initialize_razorpay()
    
    def _initialize_razorpay(self):
        """Initialize Razorpay client"""
        try:
            if not settings.RAZORPAY_KEY_ID or not settings.RAZORPAY_KEY_SECRET:
                logger.warning("Razorpay credentials not configured. Payment processing will be disabled.")
                return
            
            self.razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            logger.info("Razorpay client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Razorpay client: {e}")
            raise
    
    def _ensure_initialized(self):
        """Ensure Razorpay client is initialized"""
        if not self.razorpay_client:
            raise RuntimeError("Razorpay client not initialized. Check API credentials.")
    
    # ========== ORDER CREATION ==========
    
    async def create_invoice_payment(self, user_id: str, invoice_id: str, amount: float) -> Dict[str, Any]:
        """Create payment order for invoice"""
        self._ensure_initialized()
        
        try:
            # Convert amount to paisa (smallest currency unit)
            amount_in_paisa = int(amount * 100)
            
            order_data = {
                "amount": amount_in_paisa,
                "currency": "INR",
                "receipt": f"invoice_{invoice_id}",
                "notes": {
                    "user_id": user_id,
                    "invoice_id": invoice_id,
                    "purpose": "invoice_payment",
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            order = self.razorpay_client.order.create(data=order_data)
            
            logger.info(f"Created Razorpay order {order['id']} for invoice {invoice_id}")
            return order
            
        except BadRequestError as e:
            logger.error(f"Razorpay bad request error: {e}")
            raise ValueError(f"Invalid payment request: {e}")
        except Exception as e:
            logger.error(f"Error creating invoice payment: {e}")
            raise
    
    async def create_credit_purchase_order(self, user_id: str, order_id: str, amount: float, 
                                          order_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create payment order for credit purchase"""
        self._ensure_initialized()
        
        try:
            # Convert amount to paisa
            amount_in_paisa = int(amount * 100)
            
            order_data = {
                "amount": amount_in_paisa,
                "currency": "INR",
                "receipt": f"credit_order_{order_id}",
                "notes": {
                    "user_id": user_id,
                    "credit_order_id": order_id,
                    "purpose": "credit_purchase",
                    "package_id": order_details.get("package_id"),
                    "total_credits": str(order_details.get("total_credits", 0)),
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            order = self.razorpay_client.order.create(data=order_data)
            
            logger.info(f"Created Razorpay order {order['id']} for credit purchase {order_id}")
            return order
            
        except BadRequestError as e:
            logger.error(f"Razorpay bad request error: {e}")
            raise ValueError(f"Invalid payment request: {e}")
        except Exception as e:
            logger.error(f"Error creating credit purchase order: {e}")
            raise
    
    # ========== PAYMENT VERIFICATION ==========
    
    def verify_payment_signature(self, order_id: str, payment_id: str, signature: str) -> bool:
        """Verify Razorpay payment signature"""
        try:
            if not settings.RAZORPAY_KEY_SECRET:
                logger.error("Razorpay key secret not configured")
                return False
            
            # Create signature verification string
            verification_string = f"{order_id}|{payment_id}"
            
            # Generate expected signature
            expected_signature = hmac.new(
                settings.RAZORPAY_KEY_SECRET.encode('utf-8'),
                verification_string.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                logger.info(f"Payment signature verified for order {order_id}")
            else:
                logger.warning(f"Invalid payment signature for order {order_id}")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying payment signature: {e}")
            return False
    
    async def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Get payment details from Razorpay"""
        self._ensure_initialized()
        
        try:
            payment = self.razorpay_client.payment.fetch(payment_id)
            
            return {
                "id": payment["id"],
                "amount": payment["amount"] / 100,  # Convert from paisa to rupees
                "currency": payment["currency"],
                "status": payment["status"],
                "order_id": payment.get("order_id"),
                "method": payment.get("method"),
                "email": payment.get("email"),
                "contact": payment.get("contact"),
                "created_at": payment.get("created_at"),
                "captured": payment.get("captured", False),
                "notes": payment.get("notes", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting payment details: {e}")
            return None
    
    async def get_order_details(self, order_id: str) -> Optional[Dict[str, Any]]:
        """Get order details from Razorpay"""
        self._ensure_initialized()
        
        try:
            order = self.razorpay_client.order.fetch(order_id)
            
            return {
                "id": order["id"],
                "amount": order["amount"] / 100,  # Convert from paisa to rupees
                "currency": order["currency"],
                "status": order["status"],
                "receipt": order.get("receipt"),
                "created_at": order.get("created_at"),
                "notes": order.get("notes", {})
            }
            
        except Exception as e:
            logger.error(f"Error getting order details: {e}")
            return None
    
    # ========== WEBHOOK PROCESSING ==========
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Razorpay webhook signature"""
        try:
            if not settings.RAZORPAY_WEBHOOK_SECRET:
                logger.error("Razorpay webhook secret not configured")
                return False
            
            # Generate expected signature
            expected_signature = hmac.new(
                settings.RAZORPAY_WEBHOOK_SECRET.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Compare signatures
            is_valid = hmac.compare_digest(expected_signature, signature)
            
            if is_valid:
                logger.info("Webhook signature verified")
            else:
                logger.warning("Invalid webhook signature")
            
            return is_valid
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {e}")
            return False
    
    async def process_webhook_event(self, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process Razorpay webhook event"""
        try:
            event_type = event_data.get("event")
            payload = event_data.get("payload", {})
            
            logger.info(f"Processing webhook event: {event_type}")
            
            if event_type == "payment.captured":
                return await self._handle_payment_captured(payload)
            elif event_type == "payment.failed":
                return await self._handle_payment_failed(payload)
            elif event_type == "order.paid":
                return await self._handle_order_paid(payload)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "ignored", "event_type": event_type}
            
        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            raise
    
    async def _handle_payment_captured(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment captured webhook"""
        try:
            payment_entity = payload.get("payment", {}).get("entity", {})
            
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id")
            amount = payment_entity.get("amount", 0) / 100  # Convert to rupees
            notes = payment_entity.get("notes", {})
            
            purpose = notes.get("purpose")
            
            logger.info(f"Payment captured: {payment_id} for order: {order_id}")
            
            result = {
                "status": "processed",
                "event_type": "payment.captured",
                "payment_id": payment_id,
                "order_id": order_id,
                "amount": amount,
                "purpose": purpose
            }
            
            # Add purpose-specific data
            if purpose == "credit_purchase":
                result["credit_order_id"] = notes.get("credit_order_id")
                result["user_id"] = notes.get("user_id")
            elif purpose == "invoice_payment":
                result["invoice_id"] = notes.get("invoice_id")
                result["user_id"] = notes.get("user_id")
            
            return result
            
        except Exception as e:
            logger.error(f"Error handling payment captured webhook: {e}")
            raise
    
    async def _handle_payment_failed(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failed webhook"""
        try:
            payment_entity = payload.get("payment", {}).get("entity", {})
            
            payment_id = payment_entity.get("id")
            order_id = payment_entity.get("order_id")
            error_description = payment_entity.get("error_description")
            notes = payment_entity.get("notes", {})
            
            logger.warning(f"Payment failed: {payment_id} for order: {order_id}, reason: {error_description}")
            
            return {
                "status": "failed",
                "event_type": "payment.failed",
                "payment_id": payment_id,
                "order_id": order_id,
                "error_description": error_description,
                "purpose": notes.get("purpose"),
                "user_id": notes.get("user_id")
            }
            
        except Exception as e:
            logger.error(f"Error handling payment failed webhook: {e}")
            raise
    
    async def _handle_order_paid(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order paid webhook"""
        try:
            order_entity = payload.get("order", {}).get("entity", {})
            
            order_id = order_entity.get("id")
            amount = order_entity.get("amount", 0) / 100  # Convert to rupees
            notes = order_entity.get("notes", {})
            
            logger.info(f"Order paid: {order_id}")
            
            return {
                "status": "paid",
                "event_type": "order.paid",
                "order_id": order_id,
                "amount": amount,
                "purpose": notes.get("purpose"),
                "user_id": notes.get("user_id")
            }
            
        except Exception as e:
            logger.error(f"Error handling order paid webhook: {e}")
            raise
    
    # ========== REFUNDS ==========
    
    async def create_refund(self, payment_id: str, amount: Optional[float] = None, 
                           reason: Optional[str] = None) -> Dict[str, Any]:
        """Create refund for a payment"""
        self._ensure_initialized()
        
        try:
            refund_data = {
                "payment_id": payment_id
            }
            
            if amount:
                refund_data["amount"] = int(amount * 100)  # Convert to paisa
            
            if reason:
                refund_data["notes"] = {"reason": reason}
            
            refund = self.razorpay_client.payment.refund(payment_id, refund_data)
            
            logger.info(f"Created refund {refund['id']} for payment {payment_id}")
            
            return {
                "id": refund["id"],
                "payment_id": refund["payment_id"],
                "amount": refund["amount"] / 100,  # Convert to rupees
                "status": refund["status"],
                "created_at": refund.get("created_at")
            }
            
        except Exception as e:
            logger.error(f"Error creating refund: {e}")
            raise
    
    # ========== CUSTOMER MANAGEMENT ==========
    
    async def create_customer(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create customer in Razorpay"""
        self._ensure_initialized()
        
        try:
            customer = self.razorpay_client.customer.create(data=customer_data)
            
            logger.info(f"Created customer {customer['id']}")
            return customer
            
        except Exception as e:
            logger.error(f"Error creating customer: {e}")
            raise
    
    # ========== UTILITY METHODS ==========
    
    def format_amount_for_razorpay(self, amount: float) -> int:
        """Convert amount to paisa for Razorpay"""
        return int(amount * 100)
    
    def format_amount_from_razorpay(self, amount: int) -> float:
        """Convert amount from paisa to rupees"""
        return amount / 100
    
    def is_payment_successful(self, payment_status: str) -> bool:
        """Check if payment status indicates success"""
        return payment_status in ["captured", "authorized"]
    
    def get_payment_method_display(self, method: str) -> str:
        """Get display name for payment method"""
        method_map = {
            "card": "Credit/Debit Card",
            "netbanking": "Net Banking",
            "wallet": "Digital Wallet",
            "upi": "UPI",
            "bank_transfer": "Bank Transfer"
        }
        return method_map.get(method, method.title())