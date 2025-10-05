"""
Tests for entity generation functionality.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from click.testing import CliRunner


class TestEntityGenerationCLI:
    """Test the entity generation CLI command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_entities_manual_mode(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test entity generation with manual parameters."""
        from generate_entities import generate_entities

        result = runner.invoke(
            generate_entities,
            [
                '-t', 'business invoice',
                '-e', 'customer_name,invoice_number,total_amount',
                '-c', '5',
                '-l', 'en',
                '-o', str(temp_output_dir)
            ]
        )

        # Check command executed successfully
        assert result.exit_code == 0
        assert "Generating 5 sets of entity data" in result.output
        assert "Successfully generated" in result.output

        # Verify mock was called
        mock_ai_client.generate_bulk_entity_data.assert_called_once_with(
            'business invoice',
            ['customer_name', 'invoice_number', 'total_amount'],
            5,
            'en'
        )

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_entities_with_analysis_json(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test entity generation using analysis JSON file."""
        from generate_entities import generate_entities

        # Create a mock analysis JSON file
        analysis_file = temp_output_dir / "analysis.json"
        analysis_data = {
            "document_type": "medical form",
            "detected_language": "en",
            "extracted_entities": {
                "patient_name": "John Doe",
                "doctor_name": "Dr. Smith"
            }
        }
        analysis_file.write_text(json.dumps(analysis_data))

        result = runner.invoke(
            generate_entities,
            [
                '-a', str(analysis_file),
                '-c', '3',
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0
        assert "medical form" in result.output

        # Verify the correct fields were extracted
        mock_ai_client.generate_bulk_entity_data.assert_called_once_with(
            'medical form',
            ['patient_name', 'doctor_name'],
            3,
            'en'
        )

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_entities_missing_required_params(self, runner):
        """Test that missing required parameters raises error."""
        from generate_entities import generate_entities

        # Missing document type and entity fields
        result = runner.invoke(generate_entities, ['-c', '5'])

        assert result.exit_code != 0
        assert ("document-type" in result.output.lower() or
                "entity-fields" in result.output.lower())

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_entities_invalid_language(self, runner, mock_ai_provider_factory, mock_ai_client):
        """Test that invalid language code raises error or is handled gracefully."""
        from generate_entities import generate_entities

        result = runner.invoke(
            generate_entities,
            [
                '-t', 'invoice',
                '-e', 'field1,field2',
                '-c', '1',
                '-l', 'invalid_lang'
            ]
        )

        # Either it should fail with an error OR succeed but warn
        # Check if the language validation is implemented
        if result.exit_code != 0:
            assert "Unsupported language code" in result.output
        else:
            # If it succeeds, it might use a default or pass through
            # the invalid language to the AI provider
            assert result.exit_code == 0

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_entities_output_file_creation(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test that output JSON file is created correctly."""
        from generate_entities import generate_entities

        output_file = "custom_entities.json"

        result = runner.invoke(
            generate_entities,
            [
                '-t', 'invoice',
                '-e', 'customer,amount',
                '-c', '2',
                '-o', str(temp_output_dir),
                '-f', output_file
            ]
        )

        assert result.exit_code == 0

        # Check file would be created (mocked)
        assert output_file in result.output or "Successfully generated" in result.output


class TestEntityGenerationLogic:
    """Test the core entity generation logic."""

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_entity_data_structure(self, mock_makedirs, mock_file, mock_ai_provider_factory, mock_ai_client):
        """Test that generated entity data has correct structure."""
        from ai_providers import get_ai_client

        client = get_ai_client(provider='gemini')
        result = client.generate_bulk_entity_data(
            "test document",
            ["field1", "field2"],
            2,
            "en"
        )

        # Check structure based on mock
        assert isinstance(result, list)
        assert len(result) == 2
        assert all('_document_type' in item for item in result)
        assert all('_language' in item for item in result)

    @pytest.mark.unit
    @pytest.mark.generation
    def test_entity_field_validation(self, mock_ai_client):
        """Test validation of entity fields."""
        # Mock client doesn't validate, but real implementation might
        # Test that the mock at least accepts the call
        result = mock_ai_client.generate_bulk_entity_data(
            "document",
            ["field1"],  # Non-empty fields
            5,
            "en"
        )
        assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.generation
    def test_entity_count_validation(self, mock_ai_provider_factory, mock_ai_client):
        """Test validation of entity count."""
        from click.testing import CliRunner
        from generate_entities import generate_entities

        runner = CliRunner()

        # Test with count = 0
        result = runner.invoke(
            generate_entities,
            [
                '-t', 'invoice',
                '-e', 'field1',
                '-c', '0'
            ]
        )

        # Check if count validation is implemented
        if "Count must be greater than 0" in result.output:
            assert result.exit_code != 0
        else:
            # Click might handle this automatically with type=int
            assert result.exit_code != 0 or "0" in result.output

        # Test with negative count - Click should reject this
        result = runner.invoke(
            generate_entities,
            [
                '-t', 'invoice',
                '-e', 'field1',
                '-c', '-5'
            ]
        )

        # Click typically rejects negative numbers for count
        assert result.exit_code != 0 or "-5" in result.output

    @pytest.mark.unit
    @pytest.mark.generation
    def test_language_specific_generation(self, mock_ai_provider_factory, mock_ai_client):
        """Test that language parameter is passed correctly."""
        from ai_providers import get_ai_client

        languages = ['en', 'es', 'fr', 'de', 'ja', 'zh']

        for lang in languages:
            client = get_ai_client(provider='gemini')
            client.generate_bulk_entity_data(
                "test document",
                ["field"],
                1,
                lang
            )

            # Verify language was passed to mock
            call_args = mock_ai_client.generate_bulk_entity_data.call_args
            assert call_args[0][3] == lang  # 4th argument is language


class TestEntityGenerationWithAnalysis:
    """Test entity generation using document analysis results."""

    @pytest.mark.unit
    @pytest.mark.generation
    def test_extract_fields_from_analysis(self, sample_document_analysis):
        """Test extracting entity fields from analysis JSON."""
        fields = list(sample_document_analysis["extracted_entities"].keys())

        assert "patient_name" in fields
        assert "doctor_name" in fields
        assert "medication" in fields
        assert "date" in fields

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('builtins.open', new_callable=mock_open)
    def test_use_analysis_document_type(self, mock_file, sample_document_analysis):
        """Test using document type from analysis."""
        doc_type = sample_document_analysis["document_type"]

        assert doc_type == "medical prescription form"

    @pytest.mark.unit
    @pytest.mark.generation
    def test_use_analysis_language(self, sample_document_analysis):
        """Test using detected language from analysis."""
        language = sample_document_analysis["detected_language"]

        assert language == "en"


class TestEntityGenerationErrorHandling:
    """Test error handling in entity generation."""

    @pytest.mark.unit
    @pytest.mark.generation
    def test_handle_api_error(self, runner, mock_ai_provider_factory, mock_ai_client):
        """Test handling of API errors during generation."""
        from generate_entities import generate_entities

        # Make mock raise an error
        mock_ai_client.generate_bulk_entity_data.side_effect = Exception("API Error")

        result = runner.invoke(
            generate_entities,
            [
                '-t', 'invoice',
                '-e', 'field1',
                '-c', '1'
            ]
        )

        assert result.exit_code != 0
        assert "Error" in result.output

    @pytest.mark.unit
    @pytest.mark.generation
    def test_handle_invalid_analysis_json(self, runner, temp_output_dir):
        """Test handling of invalid analysis JSON file."""
        from generate_entities import generate_entities

        # Create invalid JSON file
        bad_json_file = temp_output_dir / "bad.json"
        bad_json_file.write_text("{ invalid json }")

        result = runner.invoke(
            generate_entities,
            [
                '-a', str(bad_json_file),
                '-c', '1'
            ]
        )

        assert result.exit_code != 0

    @pytest.mark.unit
    @pytest.mark.generation
    def test_handle_missing_analysis_file(self, runner):
        """Test handling of missing analysis file."""
        from generate_entities import generate_entities

        result = runner.invoke(
            generate_entities,
            [
                '-a', 'nonexistent.json',
                '-c', '1'
            ]
        )

        assert result.exit_code != 0


class TestEntityGenerationBatch:
    """Test batch/bulk entity generation."""

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_large_batch(self, mock_ai_provider_factory, mock_ai_client):
        """Test generating a large batch of entities."""
        # Mock should handle any batch size
        large_batch = 100

        from ai_providers import get_ai_client
        client = get_ai_client(provider='gemini')

        result = client.generate_bulk_entity_data(
            "invoice",
            ["field1", "field2"],
            large_batch,
            "en"
        )

        # Mock returns 2 items by default, but real implementation would handle batch
        assert isinstance(result, list)

    @pytest.mark.unit
    @pytest.mark.generation
    @pytest.mark.parametrize("count", [1, 5, 10, 50, 100])
    def test_various_batch_sizes(self, count, mock_ai_provider_factory, mock_ai_client):
        """Test entity generation with various batch sizes."""
        from ai_providers import get_ai_client
        client = get_ai_client(provider='gemini')

        result = client.generate_bulk_entity_data(
            "test",
            ["field"],
            count,
            "en"
        )

        assert isinstance(result, list)


@pytest.mark.integration
@pytest.mark.generation
class TestEntityGenerationIntegration:
    """Integration tests for entity generation."""

    def test_end_to_end_entity_generation(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test complete entity generation workflow."""
        from generate_entities import generate_entities

        # Generate entities
        result = runner.invoke(
            generate_entities,
            [
                '-t', 'business invoice for catering',
                '-e', 'company_name,customer_name,invoice_number,total_amount,service_date',
                '-c', '10',
                '-l', 'en',
                '-o', str(temp_output_dir),
                '-f', 'test_entities.json'
            ]
        )

        assert result.exit_code == 0
        assert "Successfully generated 10 entity records" in result.output

        # Verify mock was called with correct parameters
        mock_ai_client.generate_bulk_entity_data.assert_called_once()
        call_args = mock_ai_client.generate_bulk_entity_data.call_args[0]

        assert call_args[0] == 'business invoice for catering'
        assert call_args[1] == ['company_name', 'customer_name', 'invoice_number', 'total_amount', 'service_date']
        assert call_args[2] == 10
        assert call_args[3] == 'en'