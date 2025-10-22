"""
Cohere API client for generating intelligent responses
"""

import logging
import asyncio
from typing import Optional, Dict, Any
from typing import Optional
import cohere
from config import Config

@@ -16,37 +16,28 @@
    def __init__(self, config: Config):
        self.config = config
        self.client = cohere.Client(api_key=config.COHERE_API_KEY)
        self.conversation_history: Dict[int, list] = {}

    async def generate_response(self, user_id: int, message: str, context: Optional[str] = None) -> str:
    async def generate_response(self, prompt: str) -> str:
        """
        Generate a response using Cohere API
        
        Args:
            user_id: Telegram user ID for conversation tracking
            message: User's message
            context: Additional context for the conversation
            prompt: The full prompt string to send to the API.
            
        Returns:
            Generated response string
        """
        try:
            # Build conversation context
            conversation_context = self._build_conversation_context(user_id, message, context)
            
            # Generate response using Cohere
            response = await asyncio.to_thread(
                self._call_cohere_api,
                conversation_context
                prompt
            )

            # Update conversation history
            self._update_conversation_history(user_id, message, response)
            
            return response

        except Exception as e:
            logger.error(f"Cohere API error for user {user_id}: {e}")
            logger.error(f"Cohere API error: {e}")
            return "I'm having trouble accessing my AI service right now. Please try again in a moment."

    def _call_cohere_api(self, prompt: str) -> str:
@@ -66,7 +57,7 @@
                max_tokens=self.config.COHERE_MAX_TOKENS,
                temperature=self.config.COHERE_TEMPERATURE,
                k=0,
                stop_sequences=[],
                stop_sequences=["\n\n", "Human:", "User:", "Assistant:"],
                return_likelihoods='NONE'
            )

@@ -82,89 +73,3 @@
        except Exception as e:
            logger.error(f"Error calling Cohere API: {e}")
            raise
    
    def _build_conversation_context(self, user_id: int, message: str, context: Optional[str] = None) -> str:
        """
        Build conversation context including history
        
        Args:
            user_id: User ID for conversation tracking
            message: Current user message
            context: Additional context
            
        Returns:
            Formatted prompt for Cohere
        """
        # Get conversation history for this user
        history = self.conversation_history.get(user_id, [])
        
        # Build the prompt with context
        prompt_parts = []
        
        # Add system context
        prompt_parts.append(
            "You are a helpful, friendly, and knowledgeable AI assistant. "
            "Provide clear, accurate, and helpful responses to user questions. "
            "Keep your responses conversational and engaging."
        )
        
        # Add additional context if provided
        if context:
            prompt_parts.append(f"Additional context: {context}")
        
        # Add conversation history (last 5 exchanges to keep context manageable)
        if history:
            prompt_parts.append("\nConversation history:")
            for exchange in history[-5:]:  # Keep last 5 exchanges
                prompt_parts.append(f"Human: {exchange['user']}")
                prompt_parts.append(f"Assistant: {exchange['bot']}")
        
        # Add current message
        prompt_parts.append(f"\nHuman: {message}")
        prompt_parts.append("Assistant:")
        
        return "\n".join(prompt_parts)
    
    def _update_conversation_history(self, user_id: int, user_message: str, bot_response: str):
        """
        Update conversation history for a user
        
        Args:
            user_id: User ID
            user_message: User's message
            bot_response: Bot's response
        """
        if user_id not in self.conversation_history:
            self.conversation_history[user_id] = []
        
        self.conversation_history[user_id].append({
            'user': user_message,
            'bot': bot_response
        })
        
        # Keep only last 10 exchanges to prevent memory issues
        if len(self.conversation_history[user_id]) > 10:
            self.conversation_history[user_id] = self.conversation_history[user_id][-10:]
    
    def clear_conversation_history(self, user_id: int):
        """
        Clear conversation history for a user
        
        Args:
            user_id: User ID to clear history for
        """
        if user_id in self.conversation_history:
            del self.conversation_history[user_id]
            logger.info(f"Cleared conversation history for user {user_id}")
    
    def get_conversation_length(self, user_id: int) -> int:
        """
        Get the length of conversation history for a user
        
        Args:
            user_id: User ID
            
        Returns:
            Number of exchanges in conversation history
        """
        return len(self.conversation_history.get(user_id, []))
