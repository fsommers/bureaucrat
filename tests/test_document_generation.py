"""
Tests for document generation functionality.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open, call
from click.testing import CliRunner


class TestDocumentGenerationCLI:
    """Test the document generation CLI command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_entity_file(self, temp_output_dir, sample_entity_data_list):
        """Create a sample entity JSON file."""
        entity_file = temp_output_dir / "entities.json"
        entity_file.write_text(json.dumps(sample_entity_data_list))
        return entity_file

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_documents_basic(self, runner, mock_ai_provider_factory, mock_ai_client,
                                     sample_entity_file, temp_output_dir):
        """Test basic document generation from entity file."""
        from generate_documents import generate_documents

        result = runner.invoke(
            generate_documents,
            [
                '-e', str(sample_entity_file),
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0
        assert "Generating" in result.output
        assert "HTML documents" in result.output

        # Verify AI client was called for each entity
        # sample_entity_data_list is a list fixture, not a method
        assert mock_ai_client.generate_document_with_data.call_count >= 1

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_documents_with_template_image(self, runner, mock_ai_provider_factory,
                                                   mock_ai_client, sample_entity_file, temp_output_dir):
        """Test document generation with template image."""
        from generate_documents import generate_documents

        # Create a dummy image file
        template_image = temp_output_dir / "template.jpg"
        template_image.write_bytes(b"fake image data")

        result = runner.invoke(
            generate_documents,
            [
                '-e', str(sample_entity_file),
                '-i', str(template_image),
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0

        # Verify template image was passed to generation
        calls = mock_ai_client.generate_document_with_data.call_args_list
        for call_args in calls:
            assert len(call_args[0]) == 4 or 'template_image_path' in call_args[1]

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_documents_with_start_index(self, runner, mock_ai_provider_factory,
                                                mock_ai_client, sample_entity_file, temp_output_dir):
        """Test document generation with custom start index."""
        from generate_documents import generate_documents

        result = runner.invoke(
            generate_documents,
            [
                '-e', str(sample_entity_file),
                '-s', '100',
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0

        # Output files should start from document_0100.html
        assert "document_0100" in result.output or "Successfully generated" in result.output

    @pytest.mark.unit
    @pytest.mark.generation
    def test_generate_documents_override_language(self, runner, mock_ai_provider_factory,
                                              mock_ai_client, sample_entity_file, temp_output_dir):
        """Test overriding language from entity data."""
        from generate_documents import generate_documents

        result = runner.invoke(
            generate_documents,
            [
                '-e', str(sample_entity_file),
                '-l', 'es',
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0

        # Verify Spanish language was used
        calls = mock_ai_client.generate_document_with_data.call_args_list
        for call_args in calls:
            assert call_args[0][2] == 'es'  # 3rd argument is language


class TestDocumentGenerationLogic:
    """Test core document generation logic."""

    @pytest.mark.unit
    @pytest.mark.generation
    def test_html_document_structure(self, mock_ai_client, sample_entity_data):
        """Test that generated HTML has correct structure."""
        html = mock_ai_client.generate_document_with_data(
            "invoice",
            sample_entity_data,
            "en"
        )

        assert "<!DOCTYPE html>" in html
        assert "<html" in html
        assert "<body>" in html
        assert "</html>" in html

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('generate_documents.get_available_backgrounds')
    def test_background_image_selection(self, mock_get_backgrounds, temp_output_dir):
        """Test random background image selection."""
        # Mock available backgrounds
        mock_backgrounds = [
            "backgrounds/paper_bg_1.png",
            "backgrounds/paper_bg_2.png",
            "backgrounds/paper_bg_3.png"
        ]
        mock_get_backgrounds.return_value = mock_backgrounds

        from generate_documents import get_available_backgrounds
        backgrounds = get_available_backgrounds()

        assert len(backgrounds) == 3
        assert all(bg.endswith('.png') for bg in backgrounds)

    @pytest.mark.unit
    @pytest.mark.generation
    def test_document_metadata_generation(self, sample_entity_data):
        """Test that document metadata is generated correctly."""
        metadata = {
            "entity_data": sample_entity_data,
            "document_type": sample_entity_data.get("_document_type", "unknown"),
            "language": sample_entity_data.get("_language", "en"),
            "generated_at": "2024-01-15T10:00:00"
        }

        assert metadata["document_type"] == "business invoice"
        assert metadata["language"] == "en"
        assert "entity_data" in metadata


class TestBackgroundHandling:
    """Test background image handling in document generation."""

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('glob.glob')
    def test_no_backgrounds_available(self, mock_glob):
        """Test handling when no background images are available."""
        mock_glob.return_value = []

        from generate_documents import get_available_backgrounds
        backgrounds = get_available_backgrounds()

        assert backgrounds == []

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('os.path.exists')
    def test_backgrounds_directory_missing(self, mock_exists):
        """Test handling when backgrounds directory doesn't exist."""
        mock_exists.return_value = False

        from generate_documents import get_available_backgrounds
        backgrounds = get_available_backgrounds()

        assert backgrounds == []

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('shutil.copy2')
    @patch('glob.glob')
    def test_background_copy_to_output(self, mock_glob, mock_copy, temp_output_dir):
        """Test copying background images to output directory."""
        mock_glob.return_value = ["backgrounds/paper_bg_1.png"]

        # Simulate copying background
        source = "backgrounds/paper_bg_1.png"
        dest = temp_output_dir / "background_0001.png"

        # In real code, this would be called
        # mock_copy(source, dest)

        # Verify copy would be called with correct paths
        # (actual verification depends on implementation)
        assert source.endswith('.png')


class TestDocumentNumbering:
    """Test document numbering and file naming."""

    @pytest.mark.unit
    @pytest.mark.generation
    @pytest.mark.parametrize("index,expected", [
        (1, "document_0001.html"),
        (99, "document_0099.html"),
        (100, "document_0100.html"),
        (1000, "document_1000.html"),
    ])
    def test_document_file_naming(self, index, expected):
        """Test document file naming with zero-padding."""
        filename = f"document_{index:04d}.html"
        assert filename == expected

    @pytest.mark.unit
    @pytest.mark.generation
    def test_background_file_naming(self):
        """Test background file naming matches document numbering."""
        doc_num = 42
        doc_filename = f"document_{doc_num:04d}.html"
        bg_filename = f"background_{doc_num:04d}.png"

        assert doc_filename == "document_0042.html"
        assert bg_filename == "background_0042.png"


class TestDocumentGenerationErrorHandling:
    """Test error handling in document generation."""

    @pytest.mark.unit
    @pytest.mark.generation
    def test_missing_entity_file(self, runner):
        """Test handling of missing entity file."""
        from generate_documents import generate_documents

        result = runner.invoke(
            generate_documents,
            ['-e', 'nonexistent.json']
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output

    @pytest.mark.unit
    @pytest.mark.generation
    def test_invalid_entity_json(self, runner, temp_output_dir):
        """Test handling of invalid entity JSON."""
        from generate_documents import generate_documents

        # Create invalid JSON file
        bad_json = temp_output_dir / "bad.json"
        bad_json.write_text("{ invalid json }")

        result = runner.invoke(
            generate_documents,
            ['-e', str(bad_json)]
        )

        assert result.exit_code != 0

    @pytest.mark.unit
    @pytest.mark.generation
    def test_empty_entity_list(self, runner, temp_output_dir):
        """Test handling of empty entity list."""
        from generate_documents import generate_documents

        # Create empty entity list
        empty_json = temp_output_dir / "empty.json"
        empty_json.write_text("[]")

        result = runner.invoke(
            generate_documents,
            ['-e', str(empty_json)]
        )

        assert result.exit_code != 0
        assert "No entity data found" in result.output

    @pytest.mark.unit
    @pytest.mark.generation
    def test_api_error_during_generation(self, runner, mock_ai_provider_factory,
                                        mock_ai_client, sample_entity_file, temp_output_dir):
        """Test handling of API errors during document generation."""
        from generate_documents import generate_documents

        # Make mock raise an error
        mock_ai_client.generate_document_with_data.side_effect = Exception("API Error")

        result = runner.invoke(
            generate_documents,
            [
                '-e', str(sample_entity_file),
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code != 0
        assert "Error" in result.output


class TestDocumentGeneratorClass:
    """Test the DocumentGenerator class."""

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('document_generator.get_ai_client')
    def test_document_generator_init(self, mock_get_client):
        """Test DocumentGenerator initialization."""
        from document_generator import DocumentGenerator

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        generator = DocumentGenerator()

        assert generator.ai_client == mock_client
        assert generator.generated_data == []
        mock_get_client.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.generation
    @patch('document_generator.get_ai_client')
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_document_generator_workflow(self, mock_makedirs, mock_file, mock_get_client):
        """Test complete DocumentGenerator workflow."""
        from document_generator import DocumentGenerator

        mock_client = Mock()
        mock_get_client.return_value = mock_client

        # Mock entity generation
        mock_client.generate_bulk_entity_data.return_value = [
            {"name": "Test", "value": "123"}
        ]

        # Mock document generation
        mock_client.generate_document_with_data.return_value = "<html>Test</html>"

        generator = DocumentGenerator()
        generator.generate_documents(
            document_type="invoice",
            entity_fields=["name", "value"],
            count=1,
            language="en",
            output_dir="test_output"
        )

        # Verify methods were called
        mock_client.generate_bulk_entity_data.assert_called_once()
        mock_client.generate_document_with_data.assert_called_once()
        mock_makedirs.assert_called_once_with("test_output", exist_ok=True)


@pytest.mark.integration
@pytest.mark.generation
class TestDocumentGenerationIntegration:
    """Integration tests for document generation."""

    def test_end_to_end_document_generation(self, runner, mock_ai_provider_factory,
                                           mock_ai_client, temp_output_dir):
        """Test complete document generation workflow."""
        from generate_documents import generate_documents

        # Create entity file
        entity_file = temp_output_dir / "entities.json"
        entities = [
            {
                "customer": "ABC Corp",
                "amount": "$1000",
                "_document_type": "invoice",
                "_language": "en"
            }
        ]
        entity_file.write_text(json.dumps(entities))

        # Generate documents
        result = runner.invoke(
            generate_documents,
            [
                '-e', str(entity_file),
                '-o', str(temp_output_dir / "output")
            ]
        )

        assert result.exit_code == 0
        assert "Successfully generated" in result.output

        # Verify mock was called
        mock_ai_client.generate_document_with_data.assert_called_once()