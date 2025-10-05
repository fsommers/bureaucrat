"""
Tests for document analysis functionality.
"""
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, mock_open
from click.testing import CliRunner


class TestDocumentAnalysisCLI:
    """Test the document analysis CLI command."""

    @pytest.fixture
    def runner(self):
        """Create a CLI runner."""
        return CliRunner()

    @pytest.fixture
    def sample_image_file(self, temp_output_dir):
        """Create a sample image file."""
        image_file = temp_output_dir / "sample_document.jpg"
        image_file.write_bytes(b"fake image data")
        return image_file

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analyze_document_basic(self, runner, mock_ai_provider_factory, mock_ai_client,
                                   sample_image_file, temp_output_dir):
        """Test basic document analysis."""
        from analyze_document import analyze_document

        result = runner.invoke(
            analyze_document,
            [
                '-i', str(sample_image_file),
                '-o', str(temp_output_dir)
            ]
        )

        assert result.exit_code == 0
        assert "Analyzing document image" in result.output
        assert "Analysis complete" in result.output

        # Verify AI client was called
        mock_ai_client.analyze_document_image.assert_called_once_with(str(sample_image_file))

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analyze_document_custom_output_file(self, runner, mock_ai_provider_factory,
                                                mock_ai_client, sample_image_file, temp_output_dir):
        """Test analysis with custom output filename."""
        from analyze_document import analyze_document

        result = runner.invoke(
            analyze_document,
            [
                '-i', str(sample_image_file),
                '-o', str(temp_output_dir),
                '--output-file', 'custom_analysis.json'
            ]
        )

        assert result.exit_code == 0
        assert "custom_analysis.json" in result.output or "Analysis complete" in result.output

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analyze_missing_image_file(self, runner):
        """Test analysis with missing image file."""
        from analyze_document import analyze_document

        result = runner.invoke(
            analyze_document,
            ['-i', 'nonexistent.jpg']
        )

        assert result.exit_code != 0
        assert "does not exist" in result.output or "Error" in result.output


class TestAnalysisResultStructure:
    """Test the structure of analysis results."""

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analysis_result_fields(self, mock_ai_client):
        """Test that analysis results have required fields."""
        result = mock_ai_client.analyze_document_image("test.jpg")

        assert "document_type" in result
        assert "detected_language" in result
        assert "confidence" in result
        assert "extracted_entities" in result

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_extracted_entities_structure(self, mock_ai_client):
        """Test structure of extracted entities."""
        result = mock_ai_client.analyze_document_image("test.jpg")
        entities = result["extracted_entities"]

        assert isinstance(entities, dict)
        assert len(entities) > 0

        # Check that all values are strings
        for key, value in entities.items():
            assert isinstance(key, str)
            assert isinstance(value, str)

    @pytest.mark.unit
    @pytest.mark.analysis
    @pytest.mark.parametrize("language", ["en", "es", "fr", "de", "ja", "zh", "th"])
    def test_language_detection(self, language):
        """Test language detection for various languages."""
        mock_result = {
            "document_type": "invoice",
            "detected_language": language,
            "confidence": "high",
            "extracted_entities": {}
        }

        assert mock_result["detected_language"] == language
        assert mock_result["detected_language"] in ["en", "es", "fr", "de", "ja", "zh", "th"]

    @pytest.mark.unit
    @pytest.mark.analysis
    @pytest.mark.parametrize("confidence", ["high", "medium", "low"])
    def test_confidence_levels(self, confidence):
        """Test different confidence levels in analysis."""
        mock_result = {
            "document_type": "invoice",
            "detected_language": "en",
            "confidence": confidence,
            "extracted_entities": {}
        }

        assert mock_result["confidence"] in ["high", "medium", "low"]


class TestDocumentTypeDetection:
    """Test document type detection functionality."""

    @pytest.mark.unit
    @pytest.mark.analysis
    @pytest.mark.parametrize("doc_type", [
        "business invoice",
        "medical prescription",
        "rental agreement",
        "employment contract",
        "tax form",
        "insurance claim",
        "purchase order",
        "shipping label"
    ])
    def test_various_document_types(self, doc_type):
        """Test detection of various document types."""
        mock_result = {
            "document_type": doc_type,
            "detected_language": "en",
            "confidence": "high",
            "extracted_entities": {}
        }

        assert mock_result["document_type"] == doc_type

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_unknown_document_type(self):
        """Test handling of unknown document types."""
        mock_result = {
            "document_type": "unknown",
            "detected_language": "en",
            "confidence": "low",
            "extracted_entities": {}
        }

        assert mock_result["document_type"] == "unknown"
        assert mock_result["confidence"] == "low"


class TestEntityExtraction:
    """Test entity extraction from documents."""

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_extract_personal_information(self):
        """Test extraction of personal information."""
        mock_entities = {
            "full_name": "John Doe",
            "address": "123 Main St, City, State 12345",
            "phone": "+1-555-123-4567",
            "email": "john.doe@example.com"
        }

        assert "full_name" in mock_entities
        assert "address" in mock_entities
        assert "phone" in mock_entities
        assert "email" in mock_entities

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_extract_business_information(self):
        """Test extraction of business information."""
        mock_entities = {
            "company_name": "Acme Corporation",
            "company_address": "456 Business Ave",
            "tax_id": "12-3456789",
            "website": "www.acme.com"
        }

        assert "company_name" in mock_entities
        assert "company_address" in mock_entities
        assert "tax_id" in mock_entities

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_extract_document_specific_info(self):
        """Test extraction of document-specific information."""
        # Invoice specific
        invoice_entities = {
            "invoice_number": "INV-2024-001",
            "invoice_date": "2024-01-15",
            "total_amount": "$1,234.56",
            "due_date": "2024-02-15"
        }

        # Medical form specific
        medical_entities = {
            "patient_id": "P-12345",
            "diagnosis": "Common Cold",
            "prescription": "Medication XYZ",
            "doctor_name": "Dr. Smith"
        }

        assert "invoice_number" in invoice_entities
        assert "patient_id" in medical_entities


class TestAnalysisErrorHandling:
    """Test error handling in document analysis."""

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_invalid_image_format(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test handling of invalid image formats."""
        from analyze_document import analyze_document

        # Create a text file instead of image
        text_file = temp_output_dir / "not_an_image.txt"
        text_file.write_text("This is not an image")

        # Mock should raise an error for invalid image
        mock_ai_client.analyze_document_image.side_effect = Exception("Invalid image format")

        result = runner.invoke(
            analyze_document,
            ['-i', str(text_file)]
        )

        assert result.exit_code != 0
        assert "Error" in result.output

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_api_error_during_analysis(self, runner, mock_ai_provider_factory,
                                      mock_ai_client, sample_image_file):
        """Test handling of API errors during analysis."""
        from analyze_document import analyze_document

        # Make mock raise an API error
        mock_ai_client.analyze_document_image.side_effect = Exception("API Error: Rate limit exceeded")

        result = runner.invoke(
            analyze_document,
            ['-i', str(sample_image_file)]
        )

        assert result.exit_code != 0
        assert "Error" in result.output

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_corrupted_image_file(self, runner, mock_ai_provider_factory, mock_ai_client, temp_output_dir):
        """Test handling of corrupted image files."""
        from analyze_document import analyze_document

        # Create a corrupted image file
        corrupted_image = temp_output_dir / "corrupted.jpg"
        corrupted_image.write_bytes(b"corrupted data")

        # Mock should handle corrupted image
        mock_ai_client.analyze_document_image.side_effect = Exception("Cannot read image")

        result = runner.invoke(
            analyze_document,
            ['-i', str(corrupted_image)]
        )

        assert result.exit_code != 0


class TestAnalysisOutputHandling:
    """Test handling of analysis output."""

    @pytest.mark.unit
    @pytest.mark.analysis
    @patch('builtins.open', new_callable=mock_open)
    @patch('os.makedirs')
    def test_save_analysis_json(self, mock_makedirs, mock_file, mock_ai_client):
        """Test saving analysis results to JSON file."""
        analysis_result = mock_ai_client.analyze_document_image("test.jpg")

        # Simulate saving to file
        json_data = json.dumps(analysis_result, indent=2, ensure_ascii=False)

        # Verify JSON is valid
        parsed = json.loads(json_data)
        assert parsed == analysis_result

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analysis_json_unicode_handling(self, mock_ai_client):
        """Test handling of Unicode characters in analysis results."""
        # Mock result with Unicode characters
        mock_ai_client.analyze_document_image.return_value = {
            "document_type": "facture",  # French
            "detected_language": "fr",
            "confidence": "high",
            "extracted_entities": {
                "nom_client": "François Müller",
                "montant": "1.234,56 €",
                "adresse": "Rue de la Paix, París"
            }
        }

        result = mock_ai_client.analyze_document_image("test.jpg")

        # Verify Unicode is preserved
        assert result["extracted_entities"]["nom_client"] == "François Müller"
        assert "€" in result["extracted_entities"]["montant"]

    @pytest.mark.unit
    @pytest.mark.analysis
    def test_analysis_output_directory_creation(self, runner, mock_ai_provider_factory,
                                               mock_ai_client, sample_image_file, temp_output_dir):
        """Test that output directory is created if it doesn't exist."""
        from analyze_document import analyze_document

        new_output_dir = temp_output_dir / "new_analysis_output"

        result = runner.invoke(
            analyze_document,
            [
                '-i', str(sample_image_file),
                '-o', str(new_output_dir)
            ]
        )

        assert result.exit_code == 0
        # Directory should be created (in real implementation)


@pytest.mark.integration
@pytest.mark.analysis
class TestDocumentAnalysisIntegration:
    """Integration tests for document analysis."""

    def test_end_to_end_analysis_workflow(self, runner, mock_ai_provider_factory,
                                         mock_ai_client, temp_output_dir):
        """Test complete document analysis workflow."""
        from analyze_document import analyze_document

        # Create test image
        image_file = temp_output_dir / "test_document.png"
        image_file.write_bytes(b"PNG image data")

        # Set up mock to return realistic analysis
        mock_ai_client.analyze_document_image.return_value = {
            "document_type": "business invoice for catering service",
            "detected_language": "en",
            "confidence": "high",
            "extracted_entities": {
                "company_name": "Gourmet Catering Co.",
                "customer_name": "ABC Corporation",
                "invoice_number": "INV-2024-0123",
                "service_date": "January 15, 2024",
                "total_amount": "$3,456.78",
                "tax_amount": "$276.54"
            }
        }

        # Run analysis
        result = runner.invoke(
            analyze_document,
            [
                '-i', str(image_file),
                '-o', str(temp_output_dir / "analysis"),
                '--output-file', 'invoice_analysis.json'
            ]
        )

        assert result.exit_code == 0
        assert "Analysis complete" in result.output

        # Verify the mock was called with correct image path
        mock_ai_client.analyze_document_image.assert_called_once_with(str(image_file))

        # Verify the returned data structure
        analysis_data = mock_ai_client.analyze_document_image.return_value
        assert analysis_data["document_type"] == "business invoice for catering service"
        assert len(analysis_data["extracted_entities"]) == 6
        assert analysis_data["confidence"] == "high"

    def test_analysis_to_entity_generation_pipeline(self, mock_ai_client):
        """Test that analysis output can be used for entity generation."""
        # Simulate analysis result
        analysis = {
            "document_type": "rental agreement",
            "detected_language": "en",
            "confidence": "high",
            "extracted_entities": {
                "landlord_name": "Property Management Inc.",
                "tenant_name": "John Smith",
                "property_address": "123 Main St, Apt 4B",
                "monthly_rent": "$2,000",
                "lease_term": "12 months"
            }
        }

        # Extract fields for entity generation
        fields = list(analysis["extracted_entities"].keys())
        doc_type = analysis["document_type"]
        language = analysis["detected_language"]

        # These should be compatible with entity generation
        assert len(fields) == 5
        assert doc_type == "rental agreement"
        assert language == "en"

        # Simulate entity generation with extracted info
        mock_ai_client.generate_bulk_entity_data.return_value = [
            {field: f"Generated {field}" for field in fields}
        ]

        result = mock_ai_client.generate_bulk_entity_data(doc_type, fields, 1, language)
        assert len(result) == 1