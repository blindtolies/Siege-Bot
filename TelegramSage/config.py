"""
Configuration management for the Telegram chatbot.
"""

import os
from typing import Optional

class Config:
    """Configuration class for bot settings and API keys."""
    
    def __init__(self):
        """Initialize configuration from environment variables."""
        # Load environment variables from .env file if available
        self._load_env_file()
        
        # Telegram Bot Configuration
        self.TELEGRAM_BOT_TOKEN: str = self._get_required_env("TELEGRAM_BOT_TOKEN")
        
        # Cohere API Configuration
        self.COHERE_API_KEY: str = self._get_required_env("COHERE_API_KEY")
        
        # Cohere Model Settings
        self.COHERE_MODEL: str = os.getenv("COHERE_MODEL", "command-xlarge-nightly")
        self.MAX_TOKENS: int = int(os.getenv("MAX_TOKENS", "300"))
        self.TEMPERATURE: float = float(os.getenv("TEMPERATURE", "0.7"))
        
        # Bot Settings
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        
        # Validate configuration
        self._validate_config()
    
    def _load_env_file(self):
        """Load environment variables from .env file if it exists."""
        try:
            from dotenv import load_dotenv
            if os.path.exists(".env"):
                load_dotenv()
        except ImportError:
            # dotenv not available, skip loading .env file
            pass
    
    def _get_required_env(self, key: str) -> str:
        """Get required environment variable or raise error."""
        value = os.getenv(key)
        if not value:
            raise ValueError(f"Required environment variable {key} is not set")
        return value
    
    def _validate_config(self):
        """Validate configuration values."""
        # Validate Telegram token format (basic check)
        if not self.TELEGRAM_BOT_TOKEN.count(":") == 1:
            raise ValueError("Invalid Telegram bot token format")
        
        # Validate numeric settings
        if self.MAX_TOKENS < 1 or self.MAX_TOKENS > 2048:
            raise ValueError("MAX_TOKENS must be between 1 and 2048")
        
        if self.TEMPERATURE < 0 or self.TEMPERATURE > 2:
            raise ValueError("TEMPERATURE must be between 0 and 2")
        
        # Validate Cohere API key (basic length check)
        if len(self.COHERE_API_KEY) < 10:
            raise ValueError("Cohere API key appears to be invalid")
    
    def get_summary(self) -> dict:
        """Get configuration summary (without sensitive data)."""
        return {
            "cohere_model": self.COHERE_MODEL,
            "max_tokens": self.MAX_TOKENS,
            "temperature": self.TEMPERATURE,
            "log_level": self.LOG_LEVEL,
            "telegram_token_set": bool(self.TELEGRAM_BOT_TOKEN),
            "cohere_key_set": bool(self.COHERE_API_KEY),
        }
