"""
Configuration settings for WhatsApp BSP Integration Service
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application Settings
    app_name: str = "WhatsApp BSP Integration Service"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    port: int = Field(default=8082, env="PORT")
    host: str = Field(default="0.0.0.0", env="HOST")
    
    # WhatsApp Business API Configuration
    whatsapp_access_token: Optional[str] = Field(default=None, env="WHATSAPP_ACCESS_TOKEN")
    whatsapp_app_id: Optional[str] = Field(default=None, env="WHATSAPP_APP_ID")
    whatsapp_app_secret: Optional[str] = Field(default=None, env="WHATSAPP_APP_SECRET")
    whatsapp_api_version: str = Field(default="v18.0", env="WHATSAPP_API_VERSION")
    
    # Firebase Configuration
    firebase_credentials_path: str = Field(
        default="config/firebase_config.json", 
        env="FIREBASE_CREDENTIALS_PATH"
    )
    firebase_project_id: Optional[str] = Field(default=None, env="FIREBASE_PROJECT_ID")
    
    # Database Collections
    managed_accounts_collection: str = Field(
        default="whatsapp_managed_accounts", 
        env="MANAGED_ACCOUNTS_COLLECTION"
    )
    webhook_logs_collection: str = Field(
        default="whatsapp_webhook_logs", 
        env="WEBHOOK_LOGS_COLLECTION"
    )
    
    # Webhook Configuration
    webhook_base_url: Optional[str] = Field(default=None, env="WEBHOOK_BASE_URL")
    webhook_verify_token: str = Field(
        default="alchemist_whatsapp_verify_token_2024", 
        env="WEBHOOK_VERIFY_TOKEN"
    )
    
    # API Configuration
    api_timeout: int = Field(default=30, env="API_TIMEOUT")
    max_retry_attempts: int = Field(default=3, env="MAX_RETRY_ATTEMPTS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Security
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    allowed_origins: list[str] = Field(
        default=["http://localhost:3000", "https://alchemist.app"], 
        env="ALLOWED_ORIGINS"
    )
    
    # Verification Settings
    verification_code_expiry_minutes: int = Field(default=5, env="VERIFICATION_CODE_EXPIRY_MINUTES")
    max_verification_attempts: int = Field(default=3, env="MAX_VERIFICATION_ATTEMPTS")
    
    # Message Settings
    test_message_template: str = Field(
        default="Hello! This is a test message from your AI agent's WhatsApp integration. Everything is working correctly! 🤖",
        env="TEST_MESSAGE_TEMPLATE"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")  # json, text
    
    # Health Check Configuration
    health_check_interval: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")  # seconds
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    def get_whatsapp_config(self) -> dict:
        """Get WhatsApp Business API configuration"""
        return {
            "access_token": self.whatsapp_access_token,
            "app_id": self.whatsapp_app_id,
            "app_secret": self.whatsapp_app_secret,
            "api_version": self.whatsapp_api_version
        }

    def validate_required_settings(self):
        """Validate that required settings are present"""
        errors = []
        
        # Check WhatsApp Business API configuration
        whatsapp_config = self.get_whatsapp_config()
        required_keys = ['access_token', 'app_id', 'app_secret']
        for key in required_keys:
            if not whatsapp_config.get(key):
                errors.append(f"Missing WhatsApp Business API configuration: {key}")
        
        # Check Firebase configuration
        if not os.path.exists(self.firebase_credentials_path):
            errors.append(f"Firebase credentials file not found: {self.firebase_credentials_path}")
        
        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings"""
    return settings