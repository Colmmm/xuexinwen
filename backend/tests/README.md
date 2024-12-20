# Test Suite Documentation

This directory contains the test suite for the XueXinWen backend. The tests are organized by component and include both unit tests and integration tests.

## Test Categories

Tests are marked with different categories to allow selective test execution:

- `unit`: Unit tests for individual components
- `integration`: Integration tests for multiple components
- `db`: Tests that interact with the database
- `llm`: Tests that involve LLM interactions
- `slow`: Tests that take longer to run

## Test Files

- `test_article.py`: Tests for the Article class and its methods
- `test_article_processor.py`: Tests for the ArticleProcessor pipeline
- `test_db_manager.py`: Tests for database operations
- `test_entity_extraction.py`: Tests for named entity recognition
- `test_html_wrapper.py`: Tests for HTML content generation
- `test_integration.py`: End-to-end integration tests
- `test_segmentation.py`: Tests for text segmentation
- `test_simplifier.py`: Tests for content simplification
- `test_tocfl_tagger.py`: Tests for TOCFL/CEFR level tagging

## Running Tests

### Using Docker (Recommended):

The test environment is containerized using Docker to ensure consistency and isolation. Use the following commands to run tests:

```bash
# Run all tests
docker-compose -f docker-compose.test.yml up --build

# Run tests with output and exit
docker-compose -f docker-compose.test.yml up --build --exit-code-from backend_test

# Run specific test categories
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m unit
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m db
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m llm
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m "not slow"
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m db_write
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/ -m db_read

# Run specific test files
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/test_article.py

# Run specific test
docker-compose -f docker-compose.test.yml run --rm backend_test pytest tests/test_article.py::test_article_creation

# Clean up test containers
docker-compose -f docker-compose.test.yml down
```

### Running Tests Locally (Alternative):

If you prefer to run tests locally without Docker, you'll need to:
1. Have MySQL 8.0 installed locally
2. Set up the test database manually
3. Configure environment variables

Then you can run tests using:
```bash
# Run all tests
pytest backend/tests/

# Run specific categories
pytest -m unit
pytest -m db
pytest -m llm
pytest -m "not slow"
pytest -m db_write
pytest -m db_read

# Run specific files/tests
pytest backend/tests/test_article.py
pytest backend/tests/test_article.py::test_article_creation
```

## Test Environment

### Docker Test Environment

The test environment is defined in `docker-compose.test.yml` and includes:

1. `backend_test` service:
   - Runs the test suite
   - Uses test-specific environment variables
   - Connects to test database

2. `mysql_test` service:
   - MySQL 8.0 database for testing
   - Uses tmpfs for improved performance
   - Runs on port 3307 to avoid conflicts
   - Automatically initializes with schema

Configuration:
- Database name: xuexinwen_test
- Host: mysql_test (Docker service name)
- Port: 3306 (internal), 3307 (external)
- Charset: utf8mb4
- Collation: utf8mb4_unicode_ci

## Test Environment

Tests use environment variables defined in `pytest.ini` for configuration. Key settings:
- `TESTING=true`
- `BACKEND_PRODUCTION=false`
- `OPENROUTER_API_KEY=dummy_key` (for LLM tests)

## Fixtures

Common test fixtures are defined in `conftest.py`:
- `sample_article`: A sample Article instance
- `empty_article`: An empty Article instance
- `mock_llm_client`: A mocked LLM client
- `mock_components`: Mocked processing components
- `db_manager`: DatabaseManager instance for test database
- `mysql_test_db`: Test database configuration and setup

## Adding New Tests

1. Create test files following the naming convention `test_*.py`
2. Use appropriate markers to categorize tests
3. Use fixtures from `conftest.py` where possible
4. Mock external dependencies (LLM, database) as needed
5. Follow existing patterns for similar components

## Best Practices

1. Use markers to categorize tests appropriately
2. Mock external dependencies to avoid real API calls
3. Clean up test data in teardown
4. Use descriptive test names and docstrings
5. Keep tests focused and independent
6. Use fixtures for common setup
7. Test both success and error cases
