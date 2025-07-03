"""
Pydantic models for billing service
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, validator


class TransactionType(str, Enum):
    """Transaction types"""
    PURCHASE = "purchase"
    USAGE = "usage"
    REFUND = "refund"
    BONUS = "bonus"
    CREDIT_ADDITION = "credit_addition"


class OrderStatus(str, Enum):
    """Order status types"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class PaymentStatus(str, Enum):
    """Payment status types"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


# ========== REQUEST MODELS ==========

class CreditPurchaseRequest(BaseModel):
    """Request model for credit purchase"""
    package_id: str = Field(..., description="Credit package ID")
    quantity: int = Field(default=1, ge=1, description="Quantity of packages")
    custom_amount: Optional[float] = Field(None, ge=1000, le=50000, description="Custom amount for custom packages")

    @validator('custom_amount')
    def validate_custom_amount(cls, v, values):
        if values.get('package_id') == 'custom_amount' and v is None:
            raise ValueError('Custom amount is required for custom packages')
        return v


class PaymentVerificationRequest(BaseModel):
    """Request model for payment verification"""
    order_id: str = Field(..., description="Credit order ID")
    payment_id: str = Field(..., description="Razorpay payment ID")
    signature: str = Field(..., description="Razorpay signature")


class UsageTrackingRequest(BaseModel):
    """Request model for usage tracking"""
    amount: float = Field(..., gt=0, description="Credit amount to deduct")
    usage_type: str = Field(default="api_call", description="Type of usage")
    service: str = Field(..., description="Service name")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    characters: Optional[int] = Field(None, ge=0, description="Number of characters")
    api_calls: Optional[int] = Field(default=1, ge=1, description="Number of API calls")
    session_id: Optional[str] = Field(None, description="Session ID")
    request_id: Optional[str] = Field(None, description="Request ID")


class CreditAdditionRequest(BaseModel):
    """Request model for adding credits (admin)"""
    target_user_id: str = Field(..., description="Target user ID")
    base_amount: float = Field(..., gt=0, description="Base credit amount")
    bonus_amount: float = Field(default=0.0, ge=0, description="Bonus credit amount")
    reason: Optional[str] = Field(None, description="Reason for credit addition")


class SettingsUpdateRequest(BaseModel):
    """Request model for updating credit settings"""
    low_balance_threshold: Optional[float] = Field(None, ge=0, description="Low balance threshold")
    email_alerts: Optional[bool] = Field(None, description="Enable email alerts")
    usage_alerts: Optional[bool] = Field(None, description="Enable usage alerts")


# ========== RESPONSE MODELS ==========

class CreditBalance(BaseModel):
    """Credit balance model"""
    total_credits: float = Field(..., description="Total available credits")
    base_credits: float = Field(..., description="Base credits")
    bonus_credits: float = Field(..., description="Bonus credits")


class CreditAccount(BaseModel):
    """Credit account model"""
    user_id: str = Field(..., description="User ID")
    balance: CreditBalance = Field(..., description="Credit balance")
    settings: Dict[str, Any] = Field(..., description="Account settings")
    status: str = Field(..., description="Account status")
    created_at: str = Field(..., description="Account creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class CreditPackage(BaseModel):
    """Credit package model"""
    id: str = Field(..., description="Package ID")
    name: str = Field(..., description="Package name")
    description: str = Field(..., description="Package description")
    price: float = Field(..., description="Package price")
    base_credits: float = Field(..., description="Base credits")
    bonus_credits: float = Field(..., description="Bonus credits")
    total_credits: float = Field(..., description="Total credits")
    category: str = Field(..., description="Package category")
    popular: bool = Field(..., description="Is popular package")
    features: List[str] = Field(..., description="Package features")
    savings_percentage: Optional[int] = Field(None, description="Savings percentage")
    effective_rate: Optional[float] = Field(None, description="Price per credit")
    character_equivalent: Optional[int] = Field(None, description="Character equivalent")
    display_price: Optional[str] = Field(None, description="Formatted price")
    display_credits: Optional[str] = Field(None, description="Formatted credits")


class PaymentInfo(BaseModel):
    """Payment information model"""
    gateway: str = Field(..., description="Payment gateway")
    status: PaymentStatus = Field(..., description="Payment status")
    gateway_order_id: Optional[str] = Field(None, description="Gateway order ID")
    payment_id: Optional[str] = Field(None, description="Payment ID")
    payment_link: Optional[str] = Field(None, description="Payment link")
    completed_at: Optional[str] = Field(None, description="Payment completion timestamp")
    verified: bool = Field(default=False, description="Payment verified")


class CreditOrder(BaseModel):
    """Credit order model"""
    id: str = Field(..., description="Order ID")
    user_id: str = Field(..., description="User ID")
    package_id: str = Field(..., description="Package ID")
    package_name: str = Field(..., description="Package name")
    quantity: int = Field(..., description="Quantity")
    unit_price: float = Field(..., description="Unit price")
    subtotal: float = Field(..., description="Subtotal")
    tax_amount: float = Field(..., description="Tax amount")
    total_amount: float = Field(..., description="Total amount")
    base_credits: float = Field(..., description="Base credits")
    bonus_credits: float = Field(..., description="Bonus credits")
    total_credits: float = Field(..., description="Total credits")
    status: OrderStatus = Field(..., description="Order status")
    payment: PaymentInfo = Field(..., description="Payment information")
    metadata: Dict[str, Any] = Field(..., description="Order metadata")
    created_at: str = Field(..., description="Order creation timestamp")
    updated_at: str = Field(..., description="Last update timestamp")


class Transaction(BaseModel):
    """Transaction model"""
    id: str = Field(..., description="Transaction ID")
    user_id: str = Field(..., description="User ID")
    amount: float = Field(..., description="Transaction amount")
    type: TransactionType = Field(..., description="Transaction type")
    balance_before: float = Field(..., description="Balance before transaction")
    balance_after: float = Field(..., description="Balance after transaction")
    timestamp: str = Field(..., description="Transaction timestamp")
    transaction_data: Dict[str, Any] = Field(..., description="Transaction data")
    display_amount: Optional[str] = Field(None, description="Formatted amount")
    amount_sign: Optional[str] = Field(None, description="Amount sign")
    type_display: Optional[str] = Field(None, description="Display type")
    formatted_timestamp: Optional[str] = Field(None, description="Formatted timestamp")


class UsageSummary(BaseModel):
    """Usage summary model"""
    period: str = Field(..., description="Summary period")
    total_credits_used: float = Field(..., description="Total credits used")
    total_characters: int = Field(..., description="Total characters processed")
    total_api_calls: int = Field(..., description="Total API calls")
    average_cost_per_character: float = Field(..., description="Average cost per character")
    agent_usage: Dict[str, Dict[str, Union[float, int]]] = Field(..., description="Per-agent usage")
    period_start: str = Field(..., description="Period start timestamp")
    period_end: str = Field(..., description="Period end timestamp")


class LowBalanceAlert(BaseModel):
    """Low balance alert model"""
    is_low_balance: bool = Field(..., description="Is balance low")
    current_balance: float = Field(..., description="Current balance")
    threshold: float = Field(..., description="Low balance threshold")
    should_alert: bool = Field(..., description="Should send alert")


class CreditStatus(BaseModel):
    """Credit status model"""
    balance: CreditBalance = Field(..., description="Credit balance")
    settings: Dict[str, Any] = Field(..., description="Account settings")
    status: str = Field(..., description="Account status")
    alerts: LowBalanceAlert = Field(..., description="Alert information")
    can_use_services: bool = Field(..., description="Can use services")


# ========== WEBHOOK MODELS ==========

class WebhookEvent(BaseModel):
    """Webhook event model"""
    event: str = Field(..., description="Event type")
    payload: Dict[str, Any] = Field(..., description="Event payload")
    created_at: int = Field(..., description="Event creation timestamp")


class PaymentWebhookPayload(BaseModel):
    """Payment webhook payload model"""
    payment_id: str = Field(..., description="Payment ID")
    order_id: str = Field(..., description="Order ID")
    amount: float = Field(..., description="Payment amount")
    status: str = Field(..., description="Payment status")
    purpose: Optional[str] = Field(None, description="Payment purpose")
    user_id: Optional[str] = Field(None, description="User ID")
    credit_order_id: Optional[str] = Field(None, description="Credit order ID")
    invoice_id: Optional[str] = Field(None, description="Invoice ID")
    error_description: Optional[str] = Field(None, description="Error description")


# ========== API RESPONSE MODELS ==========

class APIResponse(BaseModel):
    """Generic API response model"""
    success: bool = Field(..., description="Request success status")
    data: Optional[Any] = Field(None, description="Response data")
    error: Optional[str] = Field(None, description="Error message")
    error_code: Optional[str] = Field(None, description="Error code")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional details")


class PaginatedResponse(BaseModel):
    """Paginated response model"""
    success: bool = Field(..., description="Request success status")
    data: List[Any] = Field(..., description="Response data")
    pagination: Dict[str, Any] = Field(..., description="Pagination info")
    total: int = Field(..., description="Total items")


class HealthCheckResponse(BaseModel):
    """Health check response model"""
    status: str = Field(..., description="Health status")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    timestamp: str = Field(..., description="Check timestamp")
    environment: str = Field(..., description="Environment")
    dependencies: Dict[str, str] = Field(..., description="Dependency status")