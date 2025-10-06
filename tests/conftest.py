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
Shared pytest fixtures and configuration for all tests.
"""
import os
import sys
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import pytest

# Add parent directory to path to import the modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ==================== Mock AI Client Fixtures ====================

@pytest.fixture
def mock_ai_client():
    """Mock AI client for testing without making actual API calls."""
    client = Mock()

    # Mock generate_bulk_entity_data
    client.generate_bulk_entity_data.return_value = [
        {
            "customer_name": "John Doe",
            "invoice_number": "INV-001",
            "total_amount": "$1,234.56",
            "_document_type": "business invoice",
            "_language": "en"
        },
        {
            "customer_name": "Jane Smith",
            "invoice_number": "INV-002",
            "total_amount": "$2,345.67",
            "_document_type": "business invoice",
            "_language": "en"
        }
    ]

    # Mock generate_document_with_data
    client.generate_document_with_data.return_value = """
    <!DOCTYPE html>
    <html>
    <head><title>Test Document</title></head>
    <body><h1>Invoice</h1><p>Customer: John Doe</p></body>
    </html>
    """

    # Mock analyze_document_image
    client.analyze_document_image.return_value = {
        "document_type": "business invoice",
        "detected_language": "en",
        "confidence": "high",
        "extracted_entities": {
            "customer_name": "John Doe",
            "invoice_number": "INV-001",
            "total_amount": "$1,234.56"
        }
    }

    return client


@pytest.fixture
def mock_ai_provider_factory(mock_ai_client):
    """Mock the get_ai_client function to return our mock client."""
    with patch('ai_providers.get_ai_client') as mock_factory:
        mock_factory.return_value = mock_ai_client
        yield mock_factory


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_document_type():
    """Sample document type for testing."""
    return "business invoice for catering service"


@pytest.fixture
def sample_entity_fields():
    """Sample entity fields for testing."""
    return ["customer_name", "invoice_number", "total_amount", "service_date"]


@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing."""
    return {
        "customer_name": "Acme Corporation",
        "invoice_number": "INV-2024-001",
        "total_amount": "$5,678.90",
        "service_date": "2024-01-15",
        "_document_type": "business invoice",
        "_language": "en"
    }


@pytest.fixture
def sample_entity_data_list():
    """Sample list of entity data for bulk testing."""
    return [
        {
            "customer_name": "Acme Corporation",
            "invoice_number": "INV-2024-001",
            "total_amount": "$5,678.90",
            "service_date": "2024-01-15",
            "_document_type": "business invoice",
            "_language": "en"
        },
        {
            "customer_name": "Global Industries",
            "invoice_number": "INV-2024-002",
            "total_amount": "$3,456.78",
            "service_date": "2024-01-16",
            "_document_type": "business invoice",
            "_language": "en"
        },
        {
            "customer_name": "Tech Solutions Ltd",
            "invoice_number": "INV-2024-003",
            "total_amount": "$8,901.23",
            "service_date": "2024-01-17",
            "_document_type": "business invoice",
            "_language": "en"
        }
    ]


@pytest.fixture
def sample_html_document():
    """Sample HTML document for testing."""
    return """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <title>Business Invoice</title>
        <style>
            body { font-family: Arial, sans-serif; }
            .invoice-header { font-size: 24px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="invoice-header">Invoice #INV-2024-001</div>
        <p>Customer: Acme Corporation</p>
        <p>Total Amount: $5,678.90</p>
        <p>Service Date: January 15, 2024</p>
    </body>
    </html>
    """


@pytest.fixture
def sample_document_analysis():
    """Sample document analysis result."""
    return {
        "document_type": "medical prescription form",
        "detected_language": "en",
        "confidence": "high",
        "extracted_entities": {
            "patient_name": "John Smith",
            "doctor_name": "Dr. Jane Wilson",
            "medication": "Amoxicillin 500mg",
            "date": "2024-01-15"
        }
    }


# ==================== File System Fixtures ====================

@pytest.fixture
def temp_output_dir():
    """Create a temporary output directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_backgrounds_dir(temp_output_dir):
    """Create a mock backgrounds directory with sample PNG files."""
    backgrounds_dir = temp_output_dir / "backgrounds"
    backgrounds_dir.mkdir(exist_ok=True)

    # Create dummy PNG files
    for i in range(1, 4):
        png_file = backgrounds_dir / f"paper_bg_{i}.png"
        png_file.write_bytes(b"PNG mock data")

    return backgrounds_dir


@pytest.fixture
def sample_json_file(temp_output_dir):
    """Create a sample JSON file for testing."""
    json_path = temp_output_dir / "test_data.json"
    data = {
        "document_type": "test invoice",
        "entities": ["field1", "field2"],
        "count": 5,
        "language": "en"
    }
    json_path.write_text(json.dumps(data, indent=2))
    return json_path


# ==================== Configuration Fixtures ====================

@pytest.fixture
def mock_config():
    """Mock configuration values."""
    return {
        "AI_PROVIDER": "gemini",
        "DEFAULT_OUTPUT_DIR": "output",
        "DEFAULT_DOCUMENT_COUNT": 10,
        "GEMINI_API_KEY": "test-api-key",
        "LANGUAGE_CODES": {
            "en": "English",
            "es": "Spanish",
            "fr": "French",
            "de": "German",
            "ja": "Japanese",
            "zh": "Chinese"
        }
    }


@pytest.fixture(autouse=True)
def mock_environment(mock_config, monkeypatch):
    """Automatically mock environment variables for all tests."""
    for key, value in mock_config.items():
        if isinstance(value, str):
            monkeypatch.setenv(key, value)


# ==================== CLI Testing Fixtures ====================

@pytest.fixture
def cli_runner():
    """Create a Click CLI test runner."""
    from click.testing import CliRunner
    return CliRunner()


# ==================== Utility Fixtures ====================

@pytest.fixture
def capture_output():
    """Fixture to capture stdout/stderr."""
    import io
    from contextlib import redirect_stdout, redirect_stderr

    class OutputCapture:
        def __init__(self):
            self.stdout = io.StringIO()
            self.stderr = io.StringIO()

        def __enter__(self):
            self._stdout_context = redirect_stdout(self.stdout)
            self._stderr_context = redirect_stderr(self.stderr)
            self._stdout_context.__enter__()
            self._stderr_context.__enter__()
            return self

        def __exit__(self, *args):
            self._stdout_context.__exit__(*args)
            self._stderr_context.__exit__(*args)

        def get_stdout(self):
            return self.stdout.getvalue()

        def get_stderr(self):
            return self.stderr.getvalue()

    return OutputCapture()


@pytest.fixture
def assert_json_equal():
    """Helper fixture for comparing JSON data."""
    def _assert_json_equal(actual, expected, ignore_keys=None):
        """Assert two JSON objects are equal, optionally ignoring certain keys."""
        ignore_keys = ignore_keys or []

        if isinstance(actual, dict) and isinstance(expected, dict):
            # Remove ignored keys
            actual_filtered = {k: v for k, v in actual.items() if k not in ignore_keys}
            expected_filtered = {k: v for k, v in expected.items() if k not in ignore_keys}
            assert actual_filtered == expected_filtered
        elif isinstance(actual, list) and isinstance(expected, list):
            assert len(actual) == len(expected)
            for a, e in zip(actual, expected):
                _assert_json_equal(a, e, ignore_keys)
        else:
            assert actual == expected

    return _assert_json_equal


# ==================== Marker Configuration ====================

def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "providers: mark test as testing AI providers"
    )
    config.addinivalue_line(
        "markers", "generation: mark test as testing generation functionality"
    )