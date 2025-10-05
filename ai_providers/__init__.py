"""
AI Provider abstraction layer for document generation.

This package provides a unified interface for different AI providers
(Gemini, Hugging Face, etc.) to generate documents and analyze images.
"""

from .base_provider import AIProvider, ProviderConfig
from .provider_factory import ProviderFactory, get_ai_client
from .gemini_provider import GeminiProvider

# Register available providers
ProviderFactory.register_provider('gemini', GeminiProvider)

__all__ = [
    'AIProvider',
    'ProviderConfig',
    'ProviderFactory',
    'get_ai_client',
    'GeminiProvider'
]