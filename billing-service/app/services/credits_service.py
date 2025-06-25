"""
Credits service for handling credit operations
Converted from Node.js creditsService.js
"""

import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timezone
from decimal import Decimal
from firebase_admin.firestore import SERVER_TIMESTAMP

from app.config.settings import settings, DEFAULT_CREDIT_PACKAGES
from app.services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)


class CreditsService:
    """Service for managing user credits and credit operations"""
    
    def __init__(self, firebase_service: FirebaseService):
        self.firebase = firebase_service
        self.min_purchase = settings.MIN_PURCHASE_AMOUNT
        self.max_purchase = settings.MAX_PURCHASE_AMOUNT
        self.gst_rate = settings.GST_RATE
        self.bonus_tiers = settings.BONUS_TIERS
    
    # ========== CREDITS BALANCE ==========
    
    async def get_user_balance(self, user_id: str) -> Dict[str, Any]:
        """Get user credit balance"""
        try:
            account = await self.firebase.get_user_credits_account(user_id)
            
            if not account:
                # Create new account with zero balance
                account = await self.firebase.create_user_credits_account(user_id, 0.0)
            
            return {
                "balance": account.get("balance", {}),
                "status": account.get("status", "active"),
                "last_updated": account.get("updated_at")
            }
            
        except Exception as e:
            logger.error(f"Error getting user balance: {e}")
            raise
    
    async def get_user_credits_account(self, user_id: str) -> Dict[str, Any]:
        """Get complete user credits account"""
        try:
            account = await self.firebase.get_user_credits_account(user_id)
            
            if not account:
                # Create new account
                account = await self.firebase.create_user_credits_account(user_id, 0.0)
            
            # Check for low balance alert
            low_balance_check = await self.check_low_balance_alert(user_id)
            
            return {
                **account,
                "low_balance_alert": low_balance_check
            }
            
        except Exception as e:
            logger.error(f"Error getting user credits account: {e}")
            raise
    
    async def check_low_balance_alert(self, user_id: str) -> Dict[str, Any]:
        """Check if user balance is below threshold"""
        try:
            account = await self.firebase.get_user_credits_account(user_id)
            
            if not account:
                return {
                    "is_low_balance": True,
                    "threshold": settings.DEFAULT_LOW_BALANCE_THRESHOLD,
                    "should_alert": True
                }
            
            balance = account.get("balance", {})
            total_credits = balance.get("total_credits", 0.0)
            
            threshold = account.get("settings", {}).get("low_balance_threshold", settings.DEFAULT_LOW_BALANCE_THRESHOLD)
            is_low_balance = total_credits <= threshold
            
            return {
                "is_low_balance": is_low_balance,
                "current_balance": total_credits,
                "threshold": threshold,
                "should_alert": is_low_balance and account.get("settings", {}).get("email_alerts", True)
            }
            
        except Exception as e:
            logger.error(f"Error checking low balance alert: {e}")
            raise
    
    # ========== CREDIT PACKAGES ==========
    
    async def get_credit_packages(self) -> List[Dict[str, Any]]:
        """Get available credit packages"""
        try:
            packages = await self.firebase.get_credit_packages()
            
            # Add calculated fields to each package
            enhanced_packages = []
            for pkg in packages:
                enhanced_pkg = self._enhance_package_info(pkg)
                enhanced_packages.append(enhanced_pkg)
            
            return enhanced_packages
            
        except Exception as e:
            logger.error(f"Error getting credit packages: {e}")
            raise
    
    def _enhance_package_info(self, package: Dict[str, Any]) -> Dict[str, Any]:
        """Add calculated fields to package"""
        base_credits = package.get("base_credits") or 0.0
        bonus_credits = package.get("bonus_credits") or 0.0
        total_credits = base_credits + bonus_credits
        price = package.get("price") or 0.0
        
        # Calculate savings percentage
        savings_percentage = 0
        if bonus_credits > 0 and base_credits > 0:
            savings_percentage = round((bonus_credits / base_credits) * 100)
        
        # Calculate effective rate (price per credit)
        effective_rate = price / total_credits if total_credits > 0 else 0
        
        return {
            **package,
            "total_credits": total_credits,
            "savings_percentage": savings_percentage,
            "effective_rate": round(effective_rate, 4),
            "character_equivalent": int(total_credits * 1000),  # 1 credit = 1000 characters
            "display_price": self.format_currency(price),
            "display_credits": self.format_number(total_credits)
        }
    
    # ========== CREDIT PURCHASE ==========
    
    async def create_credit_order(self, user_id: str, package_id: str, 
                                 quantity: int = 1, custom_amount: Optional[float] = None) -> Dict[str, Any]:
        """Create credit purchase order"""
        try:
            # Get package data
            if package_id == "custom_amount" and custom_amount:
                if custom_amount < self.min_purchase:
                    raise ValueError(f"Minimum purchase amount is ₹{self.min_purchase}")
                if custom_amount > self.max_purchase:
                    raise ValueError(f"Maximum purchase amount is ₹{self.max_purchase}")
                
                package_data = {
                    "id": "custom_amount",
                    "name": "Custom Amount",
                    "price": custom_amount,
                    "base_credits": custom_amount,
                    "bonus_credits": self._calculate_bonus_credits(custom_amount),
                    "category": "custom"
                }
            else:
                packages = await self.get_credit_packages()
                package_data = next((p for p in packages if p["id"] == package_id), None)
                
                if not package_data:
                    raise ValueError(f"Package not found: {package_id}")
            
            # Calculate order totals
            unit_price = package_data["price"]
            base_credits = package_data["base_credits"] * quantity
            bonus_credits = package_data["bonus_credits"] * quantity
            total_credits = base_credits + bonus_credits
            
            subtotal = unit_price * quantity
            tax_amount = (subtotal * self.gst_rate) / 100
            total_amount = subtotal + tax_amount
            
            # Create order data
            order_data = {
                "user_id": user_id,
                "package_id": package_id,
                "package_name": package_data["name"],
                "quantity": quantity,
                "unit_price": unit_price,
                "subtotal": round(subtotal, 2),
                "tax_amount": round(tax_amount, 2),
                "total_amount": round(total_amount, 2),
                "base_credits": base_credits,
                "bonus_credits": bonus_credits,
                "total_credits": total_credits,
                "status": "pending",
                "payment": {
                    "gateway": "razorpay",
                    "status": "pending",
                    "gateway_order_id": None,
                    "payment_id": None,
                    "payment_link": None
                },
                "metadata": {
                    "package_category": package_data.get("category", "standard"),
                    "custom_amount": custom_amount if package_id == "custom_amount" else None
                }
            }
            
            # Save order to database
            order = await self.firebase.create_credit_order(order_data)
            
            logger.info(f"Created credit order {order['id']} for user {user_id}")
            return order
            
        except Exception as e:
            logger.error(f"Error creating credit order: {e}")
            raise
    
    async def complete_credit_order(self, order_id: str, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Complete credit order after successful payment"""
        try:
            # Get order details
            order = await self.firebase.get_credit_order(order_id)
            if not order:
                raise ValueError(f"Order not found: {order_id}")
            
            if order["status"] != "pending":
                raise ValueError(f"Order is not pending: {order['status']}")
            
            # Update order status
            update_data = {
                "status": "completed",
                "payment": {
                    **order.get("payment", {}),
                    "status": "completed",
                    "payment_id": payment_data.get("payment_id"),
                    "verified": payment_data.get("verified", True),
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            }
            
            await self.firebase.update_credit_order(order_id, update_data)
            
            # Add credits to user account
            credit_amount = order["total_credits"]
            transaction_data = {
                "order_id": order_id,
                "package_name": order["package_name"],
                "base_credits": order["base_credits"],
                "bonus_credits": order["bonus_credits"],
                "payment_id": payment_data.get("payment_id"),
                "gateway": "razorpay"
            }
            
            result = await self.firebase.update_user_balance(
                order["user_id"],
                credit_amount,
                "purchase",
                transaction_data
            )
            
            logger.info(f"Completed credit order {order_id} for user {order['user_id']}")
            return {
                "order": {**order, **update_data},
                "balance_update": result
            }
            
        except Exception as e:
            logger.error(f"Error completing credit order: {e}")
            raise
    
    # ========== CREDIT USAGE ==========
    
    async def deduct_credits(self, user_id: str, amount: float, usage_details: Dict[str, Any]) -> Dict[str, Any]:
        """Deduct credits for usage"""
        try:
            if amount <= 0:
                raise ValueError("Credit amount must be positive")
            
            # Check if user has sufficient credits
            balance = await self.get_user_balance(user_id)
            current_credits = balance["balance"].get("total_credits", 0.0)
            
            if current_credits < amount:
                raise ValueError(f"Insufficient credits. Required: {amount}, Available: {current_credits}")
            
            # Deduct credits
            transaction_data = {
                "usage_type": usage_details.get("usage_type", "api_call"),
                "service": usage_details.get("service", "unknown"),
                "agent_id": usage_details.get("agent_id"),
                "characters": usage_details.get("characters", 0),
                "api_calls": usage_details.get("api_calls", 1),
                "session_id": usage_details.get("session_id"),
                "request_id": usage_details.get("request_id")
            }
            
            result = await self.firebase.update_user_balance(
                user_id,
                -amount,  # Negative amount for deduction
                "usage",
                transaction_data
            )
            
            logger.info(f"Deducted {amount} credits from user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error deducting credits: {e}")
            raise
    
    async def add_credits(self, user_id: str, base_amount: float, bonus_amount: float = 0.0, 
                         metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add credits to user account (admin/promotional)"""
        try:
            total_amount = base_amount + bonus_amount
            
            transaction_data = {
                "base_credits": base_amount,
                "bonus_credits": bonus_amount,
                "reason": metadata.get("reason", "Manual addition"),
                "admin_action": metadata.get("admin_action", False),
                "admin_user_id": metadata.get("admin_user_id"),
                "package_name": metadata.get("package_name", "Manual Credit Addition")
            }
            
            result = await self.firebase.update_user_balance(
                user_id,
                total_amount,
                "credit_addition",
                transaction_data
            )
            
            logger.info(f"Added {total_amount} credits to user {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Error adding credits: {e}")
            raise
    
    # ========== TRANSACTION HISTORY ==========
    
    async def get_user_transactions(self, user_id: str, limit: int = 20, 
                                   transaction_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get user transaction history"""
        try:
            transactions = await self.firebase.get_user_transactions(user_id, limit, transaction_type)
            
            # Enhance transaction data with display formatting
            enhanced_transactions = []
            for tx in transactions:
                enhanced_tx = self._enhance_transaction_info(tx)
                enhanced_transactions.append(enhanced_tx)
            
            return enhanced_transactions
            
        except Exception as e:
            logger.error(f"Error getting user transactions: {e}")
            raise
    
    def _enhance_transaction_info(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """Add display formatting to transaction"""
        amount = transaction.get("amount", 0.0)
        tx_type = transaction.get("type", "unknown")
        
        return {
            **transaction,
            "display_amount": self.format_currency(abs(amount)),
            "amount_sign": "+" if amount >= 0 else "-",
            "type_display": self._get_transaction_type_display(tx_type),
            "formatted_timestamp": self._format_timestamp(transaction.get("timestamp"))
        }
    
    def _get_transaction_type_display(self, tx_type: str) -> str:
        """Get display name for transaction type"""
        type_map = {
            "purchase": "Credit Purchase",
            "usage": "Credit Usage",
            "refund": "Refund",
            "bonus": "Bonus Credits",
            "credit_addition": "Credit Addition"
        }
        return type_map.get(tx_type, tx_type.title())
    
    # ========== UTILITY METHODS ==========
    
    def _calculate_bonus_credits(self, amount: float) -> float:
        """Calculate bonus credits based on amount and tiers"""
        bonus_percentage = 0
        
        # Find the highest applicable tier
        for tier_amount, percentage in sorted(self.bonus_tiers.items(), reverse=True):
            if amount >= tier_amount:
                bonus_percentage = percentage
                break
        
        return (amount * bonus_percentage) / 100
    
    def format_currency(self, amount: float) -> str:
        """Format amount as Indian Rupees"""
        return f"₹{amount:,.2f}"
    
    def format_number(self, number: float) -> str:
        """Format number with Indian number system"""
        return f"{number:,.0f}"
    
    def _format_timestamp(self, timestamp: str) -> str:
        """Format timestamp for display"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            return dt.strftime("%Y-%m-%d %H:%M:%S UTC")
        except:
            return timestamp
    
    def credits_to_characters(self, credits: float) -> int:
        """Convert credits to character equivalent"""
        return int(credits * 1000)  # 1 credit = 1000 characters
    
    def characters_to_credits(self, characters: int) -> float:
        """Convert characters to credits"""
        return characters / 1000  # 1000 characters = 1 credit
    
    def get_balance_status_color(self, balance: float, threshold: float = 50.0) -> str:
        """Get color indicator for balance status"""
        if balance <= 0:
            return "error"
        elif balance <= threshold:
            return "warning"
        else:
            return "success"
    
    def needs_credit_purchase(self, balance: float, threshold: float = 10.0) -> bool:
        """Check if user needs to purchase credits"""
        return balance <= threshold
    
    def calculate_days_remaining(self, current_balance: float, daily_usage: float) -> int:
        """Calculate days until credits run out"""
        if daily_usage <= 0:
            return float('inf')
        return int(current_balance / daily_usage)