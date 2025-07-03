import logging
from typing import Optional, List, Dict, Any
import openai
from tenacity import retry, wait_exponential, stop_after_attempt

# Import centralized configuration from alchemist_shared
from alchemist_shared.config.base_settings import BaseSettings
from alchemist_shared.database.firebase_client import FirebaseClient

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    OpenAI service for Knowledge Vault that uses centralized alchemist-shared configuration.
    
    This service handles:
    - API key management through centralized settings
    - Embedding generation for document chunks
    - Integration with alchemist_shared configuration
    """
    
    _instance = None
    _api_key: Optional[str] = None
    _settings: Optional[BaseSettings] = None
    _firebase_client: Optional[FirebaseClient] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize OpenAI service using centralized configuration"""
        # Load centralized settings
        self._settings = BaseSettings()
        
        # Initialize Firebase client for potential future use
        self._firebase_client = FirebaseClient()
        
        # Get OpenAI configuration from centralized settings
        openai_config = self._settings.get_openai_config()
        self._api_key = openai_config.get("api_key")
        
        if not self._api_key:
            raise ValueError("OpenAI API key is required. Please set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self._api_key)
        self.embeddings_model = "text-embedding-3-small"
        
        logger.info(f"OpenAI service initialized with centralized config")
        if self._api_key:
            logger.info(f"OpenAI API key loaded: {self._api_key[:10]}...")
        else:
            logger.warning("No OpenAI API key found in centralized configuration")
        
    @property
    def api_key(self) -> Optional[str]:
        """Get the OpenAI API key"""
        if not self._api_key and self._settings:
            openai_config = self._settings.get_openai_config()
            self._api_key = openai_config.get("api_key")
        return self._api_key
    
    def get_api_key(self) -> Optional[str]:
        """Get the current OpenAI API key"""
        return self.api_key
    
    def is_api_key_valid(self) -> bool:
        """Check if the OpenAI API key is valid"""
        return bool(self.api_key)
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(5))
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts"""
        if not self.is_api_key_valid():
            raise ValueError("OpenAI API key is not set")
        
        try:
            response = self.client.embeddings.create(
                model=self.embeddings_model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            raise Exception(f"Error generating embeddings: {str(e)}")
    
    @retry(wait=wait_exponential(multiplier=1, min=4, max=60), stop=stop_after_attempt(5))
    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        if not self.is_api_key_valid():
            raise ValueError("OpenAI API key is not set")
        
        try:
            response = self.client.embeddings.create(
                model=self.embeddings_model,
                input=[text]
            )
            return response.data[0].embedding
        except Exception as e:
            raise Exception(f"Error generating embedding: {str(e)}")