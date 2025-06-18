import os
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv
import openai
from tenacity import retry, wait_exponential, stop_after_attempt

# Load environment variables
load_dotenv()

class OpenAIService:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(OpenAIService, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize OpenAI service with API key"""
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key is required. Set OPENAI_API_KEY environment variable.")
        
        self.client = openai.OpenAI(api_key=self.api_key)
        self.embeddings_model = "text-embedding-3-small"
        
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