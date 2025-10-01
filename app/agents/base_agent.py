"""
Base agent with fallback system for multiple AI providers.
"""

import logging
import os
from typing import Any, Dict, Optional, Union
from pydantic_ai import Agent
from pydantic_ai.models.openai import OpenAIChatModel
from pydantic_ai.providers.grok import GrokProvider
from app.config import settings

logger = logging.getLogger(__name__)


class FallbackAgent:
    """
    Agent that tries multiple AI providers with fallback support.
    Tries OpenAI first, then X.AI (Grok), then Anthropic.
    """

    def __init__(self, system_prompt: str):
        """Initialize the fallback agent with system prompt."""
        self.system_prompt = system_prompt
        self.agents = self._setup_agents()

    def _setup_agents(self) -> Dict[str, Optional[Agent]]:
        """Setup all available AI agents based on API keys."""
        agents = {}

        # Set environment variables for API keys
        if settings.OPENAI_API_KEY:
            os.environ['OPENAI_API_KEY'] = settings.OPENAI_API_KEY
        if settings.XAI_API_KEY:
            os.environ['XAI_API_KEY'] = settings.XAI_API_KEY
        if settings.ANTHROPIC_API_KEY:
            os.environ['ANTHROPIC_API_KEY'] = settings.ANTHROPIC_API_KEY

        # X.AI Agent (Primary) - Use proper PydanticAI GrokProvider
        if settings.XAI_API_KEY:
            try:
                xai_model = OpenAIChatModel(
                    'grok-2-1212',  # Latest Grok model
                    provider=GrokProvider(api_key=settings.XAI_API_KEY)
                )
                agents['xai'] = Agent(
                    xai_model,
                    system_prompt=self.system_prompt
                )
                logger.info(
                    "✅ X.AI (Grok) agent configured with proper PydanticAI provider")
            except Exception as e:
                logger.warning(f"⚠️ X.AI agent setup failed: {e}")
                agents['xai'] = None
        else:
            agents['xai'] = None
            logger.info("⚠️ No X.AI API key found")

        # OpenAI Agent (Secondary)
        if settings.OPENAI_API_KEY:
            try:
                agents['openai'] = Agent(
                    'openai:gpt-4o-mini',  # Use mini for cost efficiency
                    system_prompt=self.system_prompt
                )
                logger.info("✅ OpenAI agent configured")
            except Exception as e:
                logger.warning(f"⚠️ OpenAI agent setup failed: {e}")
                agents['openai'] = None
        else:
            agents['openai'] = None
            logger.info("⚠️ No OpenAI API key found")

        # Anthropic Agent (Fallback #2)
        if settings.ANTHROPIC_API_KEY:
            try:
                agents['anthropic'] = Agent(
                    'anthropic:claude-3-haiku-20240307',  # Use cheaper Haiku model
                    system_prompt=self.system_prompt
                )
                logger.info("✅ Anthropic agent configured")
            except Exception as e:
                logger.warning(f"⚠️ Anthropic agent setup failed: {e}")
                agents['anthropic'] = None
        else:
            agents['anthropic'] = None
            logger.info("⚠️ No Anthropic API key found")

        return agents

    async def run_async(self, user_input: str, message_history: Optional[list] = None) -> str:
        """
        Run the query through available agents with fallback.
        Tries X.AI (Grok-3) -> OpenAI -> Anthropic in order.
        """
        providers = ['xai', 'openai', 'anthropic']

        for provider in providers:
            agent = self.agents.get(provider)
            if agent is None:
                logger.debug(f"Skipping {provider} - agent not available")
                continue

            try:
                logger.info(f"🤖 Trying {provider.upper()} agent...")

                # Use PydanticAI agent for all providers
                result = await agent.run(user_input)
                logger.info(f"✅ {provider.upper()} agent succeeded")

                # Handle different PydanticAI result formats
                # In newer versions, result might be a RunResult object
                if hasattr(result, 'data'):
                    return str(result.data)
                elif hasattr(result, 'output'):
                    return str(result.output)
                elif hasattr(result, 'content'):
                    return str(result.content)
                elif hasattr(result, 'message'):
                    return str(result.message)
                elif hasattr(result, 'text'):
                    return str(result.text)
                else:
                    # The result object itself might be the content
                    logger.info(
                        f"Result type: {type(result)}, attributes: {[attr for attr in dir(result) if not attr.startswith('_')]}")
                    return str(result)

            except Exception as e:
                logger.warning(f"❌ {provider.upper()} agent failed: {e}")
                continue

        # If all agents fail
        error_msg = "All AI providers failed. Please check your API keys and try again."
        logger.error(error_msg)
        raise Exception(error_msg)

    def run_sync(self, user_input: str, message_history: Optional[list] = None) -> str:
        """
        Synchronous version - use async version with asyncio for simplicity.
        """
        import asyncio
        return asyncio.run(self.run_async(user_input, message_history))

    def get_available_providers(self) -> list:
        """Get list of available providers."""
        available = []
        for provider, agent in self.agents.items():
            if agent is not None:
                available.append(provider)
        return available

    def get_status(self) -> Dict[str, bool]:
        """Get status of all providers."""
        return {provider: agent is not None for provider, agent in self.agents.items()}
