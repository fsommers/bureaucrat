# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Factory for creating AI provider instances.

This module provides a factory pattern for instantiating the appropriate
AI provider based on configuration or user selection.
"""

from typing import Dict, Type, Optional, Any
from .base_provider import AIProvider, ProviderConfig


class ProviderFactory:
    """Factory class for creating AI provider instances."""

    # Registry of available providers
    _providers: Dict[str, Type[AIProvider]] = {}

    @classmethod
    def register_provider(cls, name: str, provider_class: Type[AIProvider]) -> None:
        """
        Register a new AI provider.

        Args:
            name: Name of the provider (e.g., "gemini", "novita")
            provider_class: The provider class that inherits from AIProvider
        """
        cls._providers[name.lower()] = provider_class

    @classmethod
    def get_provider(
        cls,
        provider_name: str,
        api_key: str,
        model_name: Optional[str] = None,
        **kwargs
    ) -> AIProvider:
        """
        Create and return an instance of the specified provider.

        Args:
            provider_name: Name of the provider to use
            api_key: API key for the provider
            model_name: Optional model name to use
            **kwargs: Additional provider-specific parameters

        Returns:
            Instance of the specified AI provider

        Raises:
            ValueError: If provider is not registered
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ValueError(
                f"Provider '{provider_name}' not found. "
                f"Available providers: {available}"
            )

        provider_class = cls._providers[provider_name]

        # Create provider config
        config = ProviderConfig(
            api_key=api_key,
            model_name=model_name,
            vision_model_name=kwargs.get('vision_model_name'),
            endpoint_url=kwargs.get('endpoint_url'),
            temperature=kwargs.get('temperature', 0.7),
            max_tokens=kwargs.get('max_tokens', 8192),
            safety_settings=kwargs.get('safety_settings'),
            additional_params=kwargs.get('additional_params')
        )

        return provider_class(config)

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        Get list of registered provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def get_provider_from_config(cls, config: Dict[str, Any]) -> AIProvider:
        """
        Create a provider instance from a configuration dictionary.

        Args:
            config: Configuration dictionary containing provider settings

        Returns:
            Instance of the configured AI provider

        Raises:
            ValueError: If configuration is invalid
        """
        provider_name = config.get('AI_PROVIDER', 'gemini')
        vision_model_name = None

        # Get provider-specific configuration
        if provider_name.lower() == 'gemini':
            api_key = config.get('GEMINI_API_KEY')
            model_name = config.get('GEMINI_MODEL', 'gemini-2.5-flash')
        elif provider_name.lower() == 'novita':
            api_key = config.get('NOVITA_API_KEY')
            model_name = config.get('NOVITA_MODEL')
            vision_model_name = config.get('NOVITA_VISION_MODEL')
        else:
            raise ValueError(f"Unknown provider: {provider_name}")

        if not api_key:
            raise ValueError(f"API key not found for provider: {provider_name}")

        return cls.get_provider(
            provider_name=provider_name,
            api_key=api_key,
            model_name=model_name,
            vision_model_name=vision_model_name,
            endpoint_url=config.get(f'{provider_name.upper()}_ENDPOINT'),
            temperature=config.get('TEMPERATURE', 0.7),
            max_tokens=config.get('MAX_TOKENS', 8192)
        )


# Helper function for backward compatibility
def get_ai_client(provider: Optional[str] = None) -> AIProvider:
    """
    Get an AI client instance.

    This is a convenience function for backward compatibility and quick setup.

    Args:
        provider: Optional provider name. If None, uses config defaults.

    Returns:
        AI provider instance
    """
    import os
    from dotenv import load_dotenv

    load_dotenv()

    if provider is None:
        provider = os.getenv('AI_PROVIDER', 'gemini')

    # Build config from environment
    config = {
        'AI_PROVIDER': provider,
        'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY'),
        'GEMINI_MODEL': os.getenv('GEMINI_MODEL', 'gemini-2.5-flash'),
        'NOVITA_API_KEY': os.getenv('NOVITA_API_KEY'),
        'NOVITA_MODEL': os.getenv('NOVITA_MODEL'),
        'NOVITA_VISION_MODEL': os.getenv('NOVITA_VISION_MODEL'),
        'TEMPERATURE': float(os.getenv('TEMPERATURE', '0.7')),
        'MAX_TOKENS': int(os.getenv('MAX_TOKENS', '8192'))
    }

    return ProviderFactory.get_provider_from_config(config)