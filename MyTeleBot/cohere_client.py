"""
Cohere API client for generating intelligent responses
"""

import logging
import asyncio
from typing import Optional
import cohere
from config import Config

logger = logging.getLogger(__name__)

class CohereClient:
    """Client for interacting with Cohere API"""
    
    def __init__(self, config: Config):
        self.config = config
        self.client = cohere.Client(api_key=config.COHERE_API_KEY)
        
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response using Cohere API
        
        Args:
            prompt: The full prompt string to send to the API.
            
        Returns:
            Generated response string
        """
        try:
            # Generate response using Cohere
            response = await asyncio.to_thread(
                self._call_cohere_api,
                prompt
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Cohere API error: {e}")
            return "I'm having trouble accessing my AI service right now. Please try again in a moment."
    
    def _call_cohere_api(self, prompt: str) -> str:
        """
        Make synchronous call to Cohere API
        
        Args:
            prompt: The prompt to send to Cohere
            
        Returns:
            Generated response text
        """
        try:
            response = self.client.generate(
                model=self.config.COHERE_MODEL,
                prompt=prompt,
                max_tokens=self.config.COHERE_MAX_TOKENS,
                temperature=self.config.COHERE_TEMPERATURE,
                k=0,
                stop_sequences=["\n\n", "Human:", "User:", "Assistant:"],
                return_likelihoods='NONE'
            )
            
            if response.generations and len(response.generations) > 0:
                generated_text = response.generations[0].text.strip()
                if generated_text:
                    return generated_text
                else:
                    return "I'm not sure how to respond to that. Could you try rephrasing your question?"
            else:
                return "I didn't generate a proper response. Please try again."
                
        except Exception as e:
            logger.error(f"Error calling Cohere API: {e}")
            raise
