"""
Utility helper functions
"""

import re
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal


def format_currency(amount: float, currency: str = "INR") -> str:
    """Format amount as currency"""
    if currency == "INR":
        return f"₹{amount:,.2f}"
    else:
        return f"{amount:,.2f} {currency}"


def format_number(number: float) -> str:
    """Format number with proper separators"""
    return f"{number:,.0f}"


def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_phone(phone: str) -> bool:
    """Validate Indian phone number format"""
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', phone)
    
    # Check if it's a valid Indian mobile number
    if len(digits) == 10 and digits.startswith(('6', '7', '8', '9')):
        return True
    elif len(digits) == 12 and digits.startswith('91') and digits[2:3] in ['6', '7', '8', '9']:
        return True
    elif len(digits) == 13 and digits.startswith('+91') and digits[3:4] in ['6', '7', '8', '9']:
        return True
    
    return False


def generate_order_id(prefix: str = "ORD") -> str:
    """Generate unique order ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}_{timestamp}"


def generate_transaction_id(prefix: str = "TXN") -> str:
    """Generate unique transaction ID"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    return f"{prefix}_{timestamp}"


def calculate_gst(amount: float, rate: float = 18.0) -> Dict[str, float]:
    """Calculate GST breakdown"""
    gst_amount = (amount * rate) / 100
    total_amount = amount + gst_amount
    
    return {
        "base_amount": round(amount, 2),
        "gst_rate": rate,
        "gst_amount": round(gst_amount, 2),
        "total_amount": round(total_amount, 2)
    }


def calculate_percentage_discount(original: float, discounted: float) -> float:
    """Calculate percentage discount"""
    if original <= 0:
        return 0.0
    
    discount = ((original - discounted) / original) * 100
    return round(discount, 2)


def sanitize_string(text: str, max_length: int = 255) -> str:
    """Sanitize string for database storage"""
    if not text:
        return ""
    
    # Remove control characters and limit length
    sanitized = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)
    return sanitized[:max_length].strip()


def mask_sensitive_data(data: str, mask_char: str = "*", visible_chars: int = 4) -> str:
    """Mask sensitive data like card numbers, emails, etc."""
    if not data or len(data) <= visible_chars:
        return data
    
    visible_part = data[-visible_chars:]
    masked_part = mask_char * (len(data) - visible_chars)
    
    return masked_part + visible_part


def create_hash(data: str, algorithm: str = "sha256") -> str:
    """Create hash of data"""
    if algorithm == "md5":
        return hashlib.md5(data.encode()).hexdigest()
    elif algorithm == "sha1":
        return hashlib.sha1(data.encode()).hexdigest()
    elif algorithm == "sha256":
        return hashlib.sha256(data.encode()).hexdigest()
    else:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")


def parse_amount(amount_str: str) -> Optional[float]:
    """Parse amount string to float"""
    try:
        # Remove currency symbols and spaces
        cleaned = re.sub(r'[₹$,\s]', '', amount_str)
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def format_timestamp(timestamp: datetime, format_type: str = "iso") -> str:
    """Format timestamp in various formats"""
    if format_type == "iso":
        return timestamp.isoformat()
    elif format_type == "human":
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")
    elif format_type == "date":
        return timestamp.strftime("%Y-%m-%d")
    elif format_type == "time":
        return timestamp.strftime("%H:%M:%S")
    else:
        return str(timestamp)


def calculate_bonus_credits(amount: float, bonus_tiers: Dict[float, float]) -> float:
    """Calculate bonus credits based on amount and tiers"""
    bonus_percentage = 0.0
    
    # Find the highest applicable tier
    for tier_amount, percentage in sorted(bonus_tiers.items(), reverse=True):
        if amount >= tier_amount:
            bonus_percentage = percentage
            break
    
    return (amount * bonus_percentage) / 100


def validate_credit_amount(amount: float, min_amount: float = 1.0, 
                          max_amount: float = 100000.0) -> bool:
    """Validate credit amount"""
    return min_amount <= amount <= max_amount


def get_display_name(user_data: Dict[str, Any]) -> str:
    """Get display name from user data"""
    # Try different fields in order of preference
    for field in ['display_name', 'name', 'displayName', 'email']:
        if field in user_data and user_data[field]:
            return user_data[field]
    
    return "Unknown User"


def calculate_days_between(start_date: datetime, end_date: datetime) -> int:
    """Calculate days between two dates"""
    return abs((end_date - start_date).days)


def is_business_hours(timestamp: datetime, timezone_name: str = "Asia/Kolkata") -> bool:
    """Check if timestamp is during business hours (9 AM - 6 PM IST)"""
    try:
        # For simplicity, using UTC offset. In production, use pytz
        # Assuming IST is UTC+5:30
        hour = timestamp.hour
        
        # Adjust for IST if timestamp is in UTC
        if timestamp.tzinfo == timezone.utc:
            hour = (hour + 5) % 24  # Rough IST conversion
        
        return 9 <= hour < 18  # 9 AM to 6 PM
    except:
        return True  # Default to business hours if calculation fails


def chunk_list(lst: list, chunk_size: int):
    """Split list into chunks"""
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_dict_get(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Safely get nested dictionary value using dot notation"""
    try:
        keys = path.split('.')
        value = data
        
        for key in keys:
            value = value[key]
        
        return value
    except (KeyError, TypeError):
        return default


def merge_dicts(*dicts: Dict[str, Any]) -> Dict[str, Any]:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        if isinstance(d, dict):
            result.update(d)
    return result


def convert_to_decimal(value: Any, precision: int = 2) -> Optional[Decimal]:
    """Convert value to Decimal with specified precision"""
    try:
        decimal_value = Decimal(str(value))
        return decimal_value.quantize(Decimal('0.01'))
    except (ValueError, TypeError):
        return None