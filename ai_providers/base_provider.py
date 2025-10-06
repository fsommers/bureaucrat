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
Base abstract class for AI providers.

This module defines the interface that all AI providers must implement
to ensure compatibility with the document generation system.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Configuration for an AI provider."""
    api_key: str
    model_name: Optional[str] = None
    endpoint_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 8192
    safety_settings: Optional[Dict[str, Any]] = None
    additional_params: Optional[Dict[str, Any]] = None


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All AI providers (Gemini, Hugging Face, etc.) must inherit from this
    class and implement the required methods.
    """

    def __init__(self, config: ProviderConfig):
        """
        Initialize the AI provider with configuration.

        Args:
            config: Provider-specific configuration
        """
        self.config = config
        self._validate_config()
        self._initialize_client()

    @abstractmethod
    def _validate_config(self) -> None:
        """
        Validate the provider configuration.

        Raises:
            ValueError: If configuration is invalid
        """
        pass

    @abstractmethod
    def _initialize_client(self) -> None:
        """
        Initialize the provider-specific client/model.

        This method should set up the connection to the AI service
        and prepare any necessary resources.
        """
        pass

    @abstractmethod
    def generate_bulk_entity_data(
        self,
        document_type: str,
        entity_fields: List[str],
        count: int,
        language: str = 'en'
    ) -> List[Dict[str, Any]]:
        """
        Generate bulk entity data for document creation.

        Args:
            document_type: Type of document (e.g., "invoice", "contract")
            entity_fields: List of fields to generate (e.g., ["customer_name", "amount"])
            count: Number of entity records to generate
            language: Language code for generation (e.g., "en", "th", "de")

        Returns:
            List of dictionaries containing entity data

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def generate_document_with_data(
        self,
        document_type: str,
        entity_data: Dict[str, str],
        language: str = 'en',
        template_image_path: Optional[str] = None,
        instructions: Optional[str] = None
    ) -> str:
        """
        Generate an HTML document using provided entity data.

        Args:
            document_type: Type of document to generate
            entity_data: Dictionary of entity field values
            language: Language code for the document
            template_image_path: Optional path to template image for layout matching
            instructions: Optional additional instructions for document generation

        Returns:
            HTML content as string

        Raises:
            Exception: If generation fails
        """
        pass

    @abstractmethod
    def analyze_document_image(self, image_path: str) -> Dict[str, Any]:
        """
        Analyze a document image to extract type and entities.

        Args:
            image_path: Path to the document image file

        Returns:
            Dictionary containing:
                - document_type: Detected document type
                - detected_language: Language code
                - confidence: Confidence level (high/medium/low)
                - extracted_entities: Dictionary of extracted entities

        Raises:
            Exception: If analysis fails or provider doesn't support vision
        """
        pass

    @abstractmethod
    def supports_vision(self) -> bool:
        """
        Check if the provider supports vision/image analysis capabilities.

        Returns:
            True if provider supports vision, False otherwise
        """
        pass

    def get_provider_name(self) -> str:
        """
        Get the name of the provider.

        Returns:
            Provider name as string
        """
        return self.__class__.__name__.replace('Provider', '')

    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current model configuration.

        Returns:
            Dictionary with model information
        """
        return {
            'provider': self.get_provider_name(),
            'model': self.config.model_name,
            'temperature': self.config.temperature,
            'max_tokens': self.config.max_tokens,
            'supports_vision': self.supports_vision()
        }

    def handle_safety_filter(self, response: Any, retry_with_simplified: bool = True) -> Any:
        """
        Handle safety filter blocks from the provider.

        This is a helper method that providers can override to handle
        their specific safety filter responses.

        Args:
            response: The response from the AI provider
            retry_with_simplified: Whether to retry with a simplified prompt

        Returns:
            Processed response or raises exception
        """
        # Default implementation - providers can override
        return response

    def validate_language_code(self, language: str) -> bool:
        """
        Validate if a language code is supported.

        Args:
            language: Language code to validate

        Returns:
            True if language is supported, False otherwise
        """
        # Import here to avoid circular dependency
        from config import LANGUAGE_CODES
        return language in LANGUAGE_CODES