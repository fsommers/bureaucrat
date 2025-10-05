# Test Suite for Synthetic Document Generator

## Overview
Comprehensive test suite using pytest for testing all functionality of the synthetic document generator.

## Installation
```bash
# Install test dependencies
pip install -r requirements-test.txt
```

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage report
```bash
pytest --cov=. --cov-report=html
# Open htmlcov/index.html to view coverage report
```

### Run specific test file
```bash
pytest tests/test_entity_generation.py
```

### Run tests by marker
```bash
# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration

# Run provider-specific tests
pytest -m providers

# Skip slow tests
pytest -m "not slow"
```

### Run tests in parallel
```bash
pytest -n auto
```

### Run with verbose output
```bash
pytest -v
```

## Test Structure

```
tests/
├── conftest.py                     # Shared fixtures and configuration
├── test_providers.py               # Test AI provider abstraction
├── test_entity_generation.py       # Test entity data generation
├── test_document_generation.py     # Test HTML document creation
├── test_document_analysis.py       # Test document image analysis
└── fixtures/                        # Test data files
    ├── sample_entities.json        # Sample entity data
    └── sample_analysis.json        # Sample analysis results
```

## Test Categories

### Unit Tests
- Test individual functions and methods
- Mock external dependencies
- Fast execution
- Marked with `@pytest.mark.unit`

### Integration Tests
- Test component interactions
- May use real file I/O
- Marked with `@pytest.mark.integration`

### Test Markers
- `unit`: Unit tests
- `integration`: Integration tests
- `providers`: AI provider tests
- `generation`: Document/entity generation tests
- `analysis`: Document analysis tests
- `slow`: Slow-running tests
- `pdf`: PDF conversion tests

## Key Fixtures (from conftest.py)

### Mock Fixtures
- `mock_ai_client`: Mocked AI client
- `mock_ai_provider_factory`: Mocked provider factory
- `mock_config`: Mock configuration values

### Data Fixtures
- `sample_document_type`: Sample document type string
- `sample_entity_fields`: Sample entity field list
- `sample_entity_data`: Single entity data dict
- `sample_entity_data_list`: List of entity data
- `sample_html_document`: Sample HTML document
- `sample_document_analysis`: Sample analysis result

### File System Fixtures
- `temp_output_dir`: Temporary directory for test outputs
- `mock_backgrounds_dir`: Mock backgrounds directory with PNG files
- `sample_json_file`: Sample JSON file for testing

### Utility Fixtures
- `cli_runner`: Click CLI test runner
- `capture_output`: Capture stdout/stderr
- `assert_json_equal`: Helper for JSON comparison

## Writing New Tests

### Example Unit Test
```python
@pytest.mark.unit
@pytest.mark.generation
def test_entity_generation(mock_ai_client):
    result = mock_ai_client.generate_bulk_entity_data(
        "invoice", ["field1", "field2"], 5, "en"
    )
    assert len(result) == 2  # Based on mock
```

### Example CLI Test
```python
def test_cli_command(runner, mock_ai_provider_factory):
    from generate_entities import generate_entities

    result = runner.invoke(generate_entities, [
        '-t', 'invoice',
        '-e', 'field1,field2',
        '-c', '5'
    ])

    assert result.exit_code == 0
    assert "Successfully" in result.output
```

## Coverage Goals
- Aim for >80% code coverage
- Focus on critical paths
- Test error handling
- Test edge cases

## Debugging Tests

### Run specific test with output
```bash
pytest tests/test_entity_generation.py::TestEntityGenerationCLI::test_generate_entities_manual_mode -v -s
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Show local variables on failure
```bash
pytest -l
```