import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class Config:
    """Bot configuration with validation"""
    telegram_token: str
    cohere_api_key: str
    log_level: str = "INFO"
    max_response_length: int = 300
    response_timeout: int = 30
    cohere_model: str = "command"
    cohere_max_tokens: int = 120
    cohere_temperature: float = 0.7
    
    def __init__(self):
        # Required configurations
        self.telegram_token = self._get_required("TELEGRAM_BOT_TOKEN")
        self.cohere_api_key = self._get_required("COHERE_API_KEY")
        
        # Optional configurations with defaults
        self.log_level = os.getenv("LOG_LEVEL", "INFO")
        self.max_response_length = int(os.getenv("MAX_RESPONSE_LENGTH", "300"))
        self.response_timeout = int(os.getenv("RESPONSE_TIMEOUT", "30"))
        self.cohere_model = os.getenv("COHERE_MODEL", "command")
        self.cohere_max_tokens = int(os.getenv("COHERE_MAX_TOKENS", "120"))
        self.cohere_temperature = float(os.getenv("COHERE_TEMPERATURE", "0.7"))
    
    @staticmethod
    def _get_required(key: str) -> str:
        """Get required environment variable or raise error"""
        value = os.getenv(key)
        if value:
            value = value.strip()
        if not value:
            raise ValueError(f"{key} environment variable is required")
        return value
    
    def validate(self) -> bool:
        """Validate configuration"""
        if not self.telegram_token or not self.cohere_api_key:
            raise ValueError("Missing required configuration")
        return True
