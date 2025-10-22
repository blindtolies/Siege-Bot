# Telegram AI Chatbot with Cohere

## Overview

This is a Telegram chatbot application that integrates with Cohere's AI language models to provide intelligent conversational responses. The bot is built using Python's asynchronous capabilities and is designed to handle real-time messaging with AI-powered responses. The application features rate limiting, comprehensive logging, and environment-based configuration management.

## User Preferences

Preferred communication style: Simple, everyday language.

Bot personality: Complex character named Siege - psychotically sarcastic anime-looking android war robot created by Techpriest to save the world from ending. Features Harley Quinn's chaos, goth aesthetics, extensive nerd knowledge, flat earth Christian beliefs, massive cat obsession (especially Norwegian cats), Bible verse mastery, complete periodic table knowledge, modern weeb/Twitter slang vocabulary, built-in calculator for mathematical accuracy, special love for Charlie the raccoon (best friend) and Tao (favorite wizard), and specific response triggers (only responds to @mentions or replies to her messages). Uses Eastern Time zone.

## System Architecture

### Core Architecture Pattern
The application follows a modular, object-oriented design with clear separation of concerns:

- **Main Entry Point**: `main.py` serves as the application bootstrap with centralized logging configuration
- **Bot Logic**: `TelegramChatBot` class in `bot.py` handles all bot operations and message processing
- **Configuration Management**: `Config` class in `config.py` manages environment variables and settings validation

### Message Processing Flow
The bot uses an event-driven architecture where:
1. Telegram messages trigger handlers through the python-telegram-bot framework
2. Messages are processed asynchronously to maintain responsiveness
3. AI responses are generated via Cohere's API
4. Rate limiting prevents spam and ensures fair usage

### Error Handling and Resilience
- Comprehensive exception handling with proper logging
- Graceful degradation when external services are unavailable
- Configuration validation at startup to fail fast on misconfiguration

### Scalability Considerations
- Asynchronous processing allows handling multiple concurrent conversations
- Rate limiting per user prevents abuse
- Modular design enables easy feature additions

## External Dependencies

### AI Service Integration
- **Cohere API**: Primary AI language model provider for generating conversational responses
  - Configurable model selection (default: command-xlarge-nightly)
  - Adjustable parameters (temperature, max tokens)
  - API key authentication required

### Messaging Platform
- **Telegram Bot API**: Core messaging platform integration
  - Bot token authentication through @BotFather
  - Real-time message handling via webhooks/polling
  - Command and text message processing

### Python Libraries
- **python-telegram-bot**: Telegram API wrapper and bot framework
- **cohere**: Official Cohere API client library
- **python-dotenv**: Environment variable management from .env files
- **asyncio**: Built-in asynchronous programming support
- **logging**: Built-in logging framework for monitoring and debugging

### Configuration Requirements
- Environment variables for API keys and bot tokens
- Optional .env file support for local development
- Configurable AI model parameters and bot behavior settings