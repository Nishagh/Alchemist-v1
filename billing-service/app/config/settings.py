"""
Application settings and configuration
"""

import os
from typing import List, Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Basic app settings
    APP_NAME: str = "Alchemist Billing Service"
    DEBUG: bool = Field(default=False, env="DEBUG")
    HOST: str = Field(default="0.0.0.0", env="HOST")
    PORT: int = Field(default=8080, env="PORT")
    
    # CORS settings
    ALLOWED_ORIGINS: List[str] = Field(
        default=[
            "http://localhost:3000",
            "https://alchemist-e69bb.web.app",
            "https://alchemist-e69bb.firebaseapp.com",
            "https://alchemist.olbrain.com"
        ],
        env="ALLOWED_ORIGINS"
    )
    
    # Firebase settings
    FIREBASE_PROJECT_ID: str = Field(env="FIREBASE_PROJECT_ID", default="alchemist-e69bb")
    FIREBASE_CREDENTIALS_PATH: Optional[str] = Field(env="FIREBASE_CREDENTIALS_PATH", default=None)
    
    # Firestore collections (schema-compliant names)
    USER_CREDITS_COLLECTION: str = "user_accounts"
    CREDIT_TRANSACTIONS_COLLECTION: str = "credit_transactions"
    CREDIT_PACKAGES_COLLECTION: str = "credit_packages"
    CREDIT_ORDERS_COLLECTION: str = "credit_orders"
    
    # Payment settings
    RAZORPAY_KEY_ID: str = Field(env="RAZORPAY_KEY_ID", default="")
    RAZORPAY_KEY_SECRET: str = Field(env="RAZORPAY_KEY_SECRET", default="")
    RAZORPAY_WEBHOOK_SECRET: str = Field(env="RAZORPAY_WEBHOOK_SECRET", default="")
    
    # Credit system settings
    MIN_PURCHASE_AMOUNT: float = 1000.0  # Minimum ₹1000
    MAX_PURCHASE_AMOUNT: float = 50000.0  # Maximum ₹50,000
    DEFAULT_LOW_BALANCE_THRESHOLD: float = 50.0  # Alert when balance < ₹50
    GST_RATE: float = 18.0  # 18% GST
    
    # Bonus credit tiers
    BONUS_TIERS: dict = {
        1000: 0,    # No bonus for minimum ₹1000
        5000: 25,   # 25% bonus for ₹5000+
        10000: 30,  # 30% bonus for ₹10000+
        25000: 35,  # 35% bonus for ₹25000+
        50000: 40,  # 40% bonus for ₹50000+
    }
    
    # API settings
    API_TIMEOUT: int = 30  # seconds
    MAX_RETRIES: int = 3
    
    # Security settings
    JWT_SECRET_KEY: str = Field(env="JWT_SECRET_KEY", default="your-secret-key-change-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Logging settings
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Usage tracking settings
    TRACK_USAGE: bool = True
    USAGE_BATCH_SIZE: int = 100
    USAGE_FLUSH_INTERVAL: int = 60  # seconds
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True,
        "extra": "ignore"
    }


# Global settings instance
try:
    settings = Settings()
except Exception as e:
    # Fallback settings for development/testing
    import os
    print(f"Warning: Failed to load settings from environment: {e}")
    print("Using fallback settings...")
    
    # Create minimal settings for startup
    class FallbackSettings:
        APP_NAME = "Alchemist Billing Service"
        DEBUG = os.getenv("DEBUG", "false").lower() == "true"
        HOST = os.getenv("HOST", "0.0.0.0")
        PORT = int(os.getenv("PORT", "8080"))
        
        ALLOWED_ORIGINS = [
            "http://localhost:3000",
            "https://alchemist-e69bb.web.app",
            "https://alchemist-e69bb.firebaseapp.com",
            "https://alchemist.olbrain.com"
        ]
        
        FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "alchemist-e69bb")
        FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH")
        
        USER_CREDITS_COLLECTION = "user_accounts"
        CREDIT_TRANSACTIONS_COLLECTION = "credit_transactions"
        CREDIT_PACKAGES_COLLECTION = "credit_packages"
        CREDIT_ORDERS_COLLECTION = "credit_orders"
        
        RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
        RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")
        RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET", "")
        
        MIN_PURCHASE_AMOUNT = 1000.0
        MAX_PURCHASE_AMOUNT = 50000.0
        DEFAULT_LOW_BALANCE_THRESHOLD = 50.0
        GST_RATE = 18.0
        
        BONUS_TIERS = {1000: 0, 5000: 25, 10000: 30, 25000: 35, 50000: 40}
        
        API_TIMEOUT = 30
        MAX_RETRIES = 3
        
        JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-secret-key-change-in-production")
        JWT_ALGORITHM = "HS256"
        ACCESS_TOKEN_EXPIRE_MINUTES = 30
        
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        
        TRACK_USAGE = True
        USAGE_BATCH_SIZE = 100
        USAGE_FLUSH_INTERVAL = 60
        
        DEFAULT_CREDIT_PACKAGES = [
            {
                "id": "suggested_1000",
                "name": "Starter Amount",
                "description": "Perfect for getting started with Alchemist",
                "price": 1000.0,
                "base_credits": 1000.0,
                "bonus_credits": 0.0,
                "total_credits": 1000.0,
                "category": "suggested",
                "popular": False,
                "features": [
                    "1000 credits",
                    "Basic support",
                    "Standard features"
                ]
            },
            {
                "id": "suggested_5000",
                "name": "Popular Amount",
                "description": "Great for regular users and small teams",
                "price": 5000.0,
                "base_credits": 5000.0,
                "bonus_credits": 1250.0,
                "total_credits": 6250.0,
                "category": "suggested",
                "popular": True,
                "features": [
                    "5000 base credits",
                    "1250 bonus credits (25% bonus)",
                    "Priority support",
                    "Advanced features"
                ]
            },
            {
                "id": "suggested_10000",
                "name": "Best Value Amount",
                "description": "Best value for heavy users and large teams",
                "price": 10000.0,
                "base_credits": 10000.0,
                "bonus_credits": 3000.0,
                "total_credits": 13000.0,
                "category": "suggested",
                "popular": False,
                "features": [
                    "10000 base credits",
                    "3000 bonus credits (30% bonus)",
                    "Premium support",
                    "All features included",
                    "Custom integrations"
                ]
            },
            {
                "id": "custom_amount",
                "name": "Custom Amount",
                "description": "Choose any amount starting from ₹1000",
                "price": None,
                "base_credits": None,
                "bonus_credits": None,
                "total_credits": None,
                "category": "custom",
                "popular": False,
                "features": [
                    "Minimum ₹1000",
                    "No upper limit",
                    "Bonus credits for larger amounts",
                    "Flexible payment"
                ]
            }
        ]
    
    settings = FallbackSettings()


# Credit packages configuration
DEFAULT_CREDIT_PACKAGES = [
    {
        "id": "suggested_1000",
        "name": "Starter Amount",
        "description": "Perfect for getting started with Alchemist",
        "price": 1000.0,
        "base_credits": 1000.0,
        "bonus_credits": 0.0,
        "total_credits": 1000.0,
        "category": "suggested",
        "popular": False,
        "features": [
            "1000 credits",
            "Basic support",
            "Standard features"
        ]
    },
    {
        "id": "suggested_5000",
        "name": "Popular Amount",
        "description": "Great for regular users and small teams",
        "price": 5000.0,
        "base_credits": 5000.0,
        "bonus_credits": 1250.0,
        "total_credits": 6250.0,
        "category": "suggested",
        "popular": True,
        "features": [
            "5000 base credits",
            "1250 bonus credits (25% bonus)",
            "Priority support",
            "Advanced features"
        ]
    },
    {
        "id": "suggested_10000",
        "name": "Best Value Amount",
        "description": "Best value for heavy users and large teams",
        "price": 10000.0,
        "base_credits": 10000.0,
        "bonus_credits": 3000.0,
        "total_credits": 13000.0,
        "category": "suggested",
        "popular": False,
        "features": [
            "10000 base credits",
            "3000 bonus credits (30% bonus)",
            "Premium support",
            "All features included",
            "Custom integrations"
        ]
    },
    {
        "id": "custom_amount",
        "name": "Custom Amount",
        "description": "Choose any amount starting from ₹1000",
        "price": None,
        "base_credits": None,
        "bonus_credits": None,
        "total_credits": None,
        "category": "custom",
        "popular": False,
        "features": [
            "Minimum ₹1000",
            "No upper limit",
            "Bonus credits for larger amounts",
            "Flexible payment"
        ]
    }
]