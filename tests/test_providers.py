"""
Tests for AI provider system functionality.
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from ai_providers import AIProvider, ProviderFactory, get_ai_client
from ai_providers.gemini_provider import GeminiProvider
from ai_providers.base_provider import ProviderConfig


class TestProviderFactory:
    """Test the ProviderFactory class."""

    @pytest.mark.unit
    @pytest.mark.providers
    def test_register_provider(self):
        """Test registering a new provider."""
        # Create a mock provider class
        class MockProvider(AIProvider):
            def __init__(self, config):
                super().__init__(config)

            def generate_bulk_entity_data(self, document_type, entity_fields, count, language='en'):
                return []

            def generate_document_with_data(self, document_type, entity_data, language='en', template_image_path=None):
                return "<html></html>"

            def analyze_document_image(self, image_path):
                return {}

        # Register the mock provider
        ProviderFactory.register_provider('mock', MockProvider)

        # Verify it was registered
        assert 'mock' in ProviderFactory._providers

    @pytest.mark.unit
    @pytest.mark.providers
    def test_create_provider_with_valid_type(self):
        """Test creating a provider with a valid type."""
        config = ProviderConfig(api_key="test-key")

        # Gemini should already be registered
        provider = ProviderFactory.get_provider('gemini', config)

        assert provider is not None
        assert isinstance(provider, GeminiProvider)

    @pytest.mark.unit
    @pytest.mark.providers
    def test_create_provider_with_invalid_type(self):
        """Test creating a provider with an invalid type raises error."""
        config = ProviderConfig(api_key="test-key")

        with pytest.raises(ValueError) as exc_info:
            ProviderFactory.get_provider('nonexistent', config)

        assert "Unknown provider" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.providers
    def test_list_available_providers(self):
        """Test listing available providers."""
        providers = ProviderFactory.list_providers()

        # At minimum, gemini should be available
        assert 'gemini' in providers
        assert isinstance(providers, list)


class TestGetAIClient:
    """Test the get_ai_client convenience function."""

    @pytest.mark.unit
    @pytest.mark.providers
    @patch.dict('os.environ', {'GEMINI_API_KEY': 'test-api-key'})
    def test_get_ai_client_gemini(self):
        """Test getting a Gemini client."""
        client = get_ai_client(provider='gemini')

        assert client is not None
        assert isinstance(client, GeminiProvider)

    @pytest.mark.unit
    @pytest.mark.providers
    @patch.dict('os.environ', {}, clear=True)
    def test_get_ai_client_missing_api_key(self):
        """Test that missing API key raises appropriate error."""
        # Mock the environment to have no GEMINI_API_KEY
        import os
        if 'GEMINI_API_KEY' in os.environ:
            del os.environ['GEMINI_API_KEY']

        with pytest.raises(ValueError) as exc_info:
            get_ai_client(provider='gemini')

        assert "api_key" in str(exc_info.value).lower() or "GEMINI_API_KEY" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.providers
    @patch.dict('os.environ', {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-key'})
    def test_get_ai_client_from_env(self):
        """Test getting client from environment variable."""
        with patch('config.AI_PROVIDER', 'gemini'):
            client = get_ai_client()

        assert client is not None
        assert isinstance(client, GeminiProvider)


class TestAIProviderInterface:
    """Test the AIProvider abstract base class interface."""

    @pytest.mark.unit
    @pytest.mark.providers
    def test_provider_must_implement_interface(self):
        """Test that providers must implement all abstract methods."""

        # Try to create a provider without implementing required methods
        class IncompleteProvider(AIProvider):
            def __init__(self, config):
                super().__init__(config)
            # Missing required method implementations

        config = ProviderConfig(api_key="test-key")

        # Should not be able to instantiate incomplete provider
        with pytest.raises(TypeError) as exc_info:
            IncompleteProvider(config)

        assert "Can't instantiate abstract class" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.providers
    def test_provider_config_validation(self):
        """Test ProviderConfig validation."""
        # Valid config
        config = ProviderConfig(
            api_key="test-key",
            model_name="test-model",
            temperature=0.7,
            max_tokens=1000
        )

        assert config.api_key == "test-key"
        assert config.model_name == "test-model"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000

        # Config with defaults
        config_defaults = ProviderConfig(api_key="test-key")
        assert config_defaults.model_name is None
        assert config_defaults.temperature == 0.7  # Default value
        assert config_defaults.max_tokens == 8192  # Default value


class TestGeminiProvider:
    """Test the Gemini provider implementation."""

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    def test_gemini_provider_initialization(self, mock_genai):
        """Test Gemini provider initialization."""
        config = ProviderConfig(
            api_key="test-key",
            model="gemini-pro",
            temperature=0.5
        )

        provider = GeminiProvider(config)

        # Verify genai was configured
        mock_genai.configure.assert_called_once_with(api_key="test-key")

        # Verify model was created
        mock_genai.GenerativeModel.assert_called()

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    def test_gemini_generate_bulk_entity_data(self, mock_genai, sample_document_type, sample_entity_fields):
        """Test Gemini provider's bulk entity generation."""
        # Setup mock
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = '[{"customer_name": "Test Corp", "invoice_number": "INV-001"}]'
        mock_model.generate_content.return_value = mock_response

        config = ProviderConfig(api_key="test-key")
        provider = GeminiProvider(config)

        # Test generation
        result = provider.generate_bulk_entity_data(
            sample_document_type,
            sample_entity_fields,
            count=2,
            language='en'
        )

        assert isinstance(result, list)
        assert len(result) > 0
        mock_model.generate_content.assert_called()

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    def test_gemini_generate_document_with_data(self, mock_genai, sample_entity_data):
        """Test Gemini provider's document generation."""
        # Setup mock
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = '<html><body>Test Document</body></html>'
        mock_model.generate_content.return_value = mock_response

        config = ProviderConfig(api_key="test-key")
        provider = GeminiProvider(config)

        # Test generation
        result = provider.generate_document_with_data(
            "business invoice",
            sample_entity_data,
            language='en'
        )

        assert isinstance(result, str)
        assert '<html>' in result
        mock_model.generate_content.assert_called()

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    @patch('ai_providers.gemini_provider.Image.open')
    def test_gemini_analyze_document_image(self, mock_image_open, mock_genai):
        """Test Gemini provider's document analysis."""
        # Setup mocks
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = '{"document_type": "invoice", "extracted_entities": {}}'
        mock_model.generate_content.return_value = mock_response

        mock_img = MagicMock()
        mock_image_open.return_value = mock_img

        config = ProviderConfig(api_key="test-key")
        provider = GeminiProvider(config)

        # Test analysis
        result = provider.analyze_document_image("test_image.jpg")

        assert isinstance(result, dict)
        assert "document_type" in result
        mock_model.generate_content.assert_called()


class TestProviderErrorHandling:
    """Test error handling in provider system."""

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    def test_handle_api_error(self, mock_genai):
        """Test handling of API errors."""
        # Setup mock to raise error
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_model.generate_content.side_effect = Exception("API Error")

        config = ProviderConfig(api_key="test-key")
        provider = GeminiProvider(config)

        # Should handle error gracefully
        with pytest.raises(Exception) as exc_info:
            provider.generate_bulk_entity_data("test", ["field"], 1)

        assert "API Error" in str(exc_info.value)

    @pytest.mark.unit
    @pytest.mark.providers
    @patch('ai_providers.gemini_provider.genai')
    def test_handle_invalid_json_response(self, mock_genai):
        """Test handling of invalid JSON in API response."""
        # Setup mock with invalid JSON
        mock_model = MagicMock()
        mock_genai.GenerativeModel.return_value = mock_model
        mock_response = MagicMock()
        mock_response.text = 'Invalid JSON {not valid}'
        mock_model.generate_content.return_value = mock_response

        config = ProviderConfig(api_key="test-key")
        provider = GeminiProvider(config)

        # Should handle invalid JSON gracefully
        with pytest.raises(Exception):
            provider.generate_bulk_entity_data("test", ["field"], 1)


@pytest.mark.integration
@pytest.mark.providers
class TestProviderIntegration:
    """Integration tests for provider system."""

    def test_provider_switching(self, mock_ai_provider_factory, mock_ai_client):
        """Test switching between different providers."""
        # This would test switching providers in a real scenario
        # For now, we verify the mock is working

        from ai_providers import get_ai_client
        client = get_ai_client(provider='gemini')

        # The mock should return our mock client
        assert client == mock_ai_client

    @patch.dict('os.environ', {'AI_PROVIDER': 'gemini', 'GEMINI_API_KEY': 'test-key'})
    def test_provider_with_config_loading(self):
        """Test provider with configuration loading from environment."""
        # Import config to trigger load from environment
        from config import AI_PROVIDER

        assert AI_PROVIDER == 'gemini'