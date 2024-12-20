import pytest
from datetime import datetime
import os
from unittest.mock import Mock, patch
import pandas as pd
import mysql.connector
from mysql.connector import Error
from backend.article.article import Article
from backend.database.db_manager import DatabaseManager

@pytest.fixture(scope="session")
def mysql_test_config():
    """Provide test database configuration."""
    return {
        'host': os.getenv('MYSQL_HOST', 'mysql_test'),
        'port': int(os.getenv('MYSQL_PORT', 3306)),
        'user': os.getenv('MYSQL_USER', 'test_user'),
        'password': os.getenv('MYSQL_PASSWORD', 'test_password'),
        'database': os.getenv('MYSQL_DATABASE', 'xuexinwen_test'),
        'charset': os.getenv('MYSQL_CHARSET', 'utf8mb4'),
        'collation': os.getenv('MYSQL_COLLATION', 'utf8mb4_unicode_ci')
    }

@pytest.fixture(scope="session")
def mysql_test_db(mysql_test_config):
    """Create and manage test database."""
    config = {k: v for k, v in mysql_test_config.items() if k not in ['collation', 'database']}
    conn = mysql.connector.connect(**config)
    cursor = conn.cursor()
    
    try:
        # Create test database
        cursor.execute(f"DROP DATABASE IF EXISTS {mysql_test_config['database']}")
        cursor.execute(
            f"CREATE DATABASE {mysql_test_config['database']} "
            f"CHARACTER SET {mysql_test_config['charset']} "
            f"COLLATE {mysql_test_config['collation']}"
        )
        
        # Switch to test database
        cursor.execute(f"USE {mysql_test_config['database']}")
        
        # Read and execute schema file
        with open('backend/database/setup.sql', 'r') as f:
            # Split the file into individual statements
            statements = f.read().split(';')
            for statement in statements:
                if statement.strip():
                    cursor.execute(statement)
        
        conn.commit()
        yield mysql_test_config
        
    finally:
        # Cleanup
        cursor.execute(f"DROP DATABASE IF EXISTS {mysql_test_config['database']}")
        conn.commit()
        cursor.close()
        conn.close()

@pytest.fixture
def db_manager(mysql_test_config):
    """Create a DatabaseManager instance for testing."""
    # Override the host to use test configuration
    original_init = DatabaseManager.__init__
    def mock_init(self, max_retries=5, retry_delay=1):
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.dbconfig = {
            "host": mysql_test_config['host'],
            "port": mysql_test_config['port'],
            "database": mysql_test_config['database'],
            "user": mysql_test_config['user'],
            "password": mysql_test_config['password'],
            "charset": mysql_test_config['charset'],
            "use_unicode": True,
            "collation": mysql_test_config['collation'],
            "raise_on_warnings": True
        }
        self._test_connection()
    
    with patch.object(DatabaseManager, '__init__', mock_init):
        manager = DatabaseManager()
        yield manager

@pytest.fixture(autouse=True)
def cleanup_database(db_manager):
    """Clean up database tables after each test."""
    yield  # Run the test
    
    # Clean up after test
    conn, cursor = db_manager._get_connection()
    try:
        # Delete in reverse order of dependencies
        cursor.execute("DELETE FROM graded_content")
        cursor.execute("DELETE FROM word_levels")
        cursor.execute("DELETE FROM entities")
        cursor.execute("DELETE FROM articles")
        conn.commit()
    finally:
        cursor.close()
        conn.close()

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    with patch('backend.utils.llm_client.LLMClient') as mock:
        client = mock.return_value
        
        # Mock entity extraction
        client.extract_entities.return_value = [
            {
                "word": "苹果公司",
                "type": "organization",
                "english": "Apple Inc."
            },
            {
                "word": "库克",
                "type": "person",
                "english": "Tim Cook, CEO of Apple"
            }
        ]
        
        # Mock word classification
        client.classify_words.return_value = {
            "发表": "B1",
            "新产品": "A2"
        }
        
        # Mock simplification
        client.simplify_to_multiple_levels.return_value = {
            "original": "苹果公司今天发表新产品。库克介绍了最新科技。",
            "A2": "苹果公司今天介绍新东西。库克说明了新科技。",
            "B1": "苹果公司今天发表新产品。库克介绍了新技术。"
        }
        
        return client

@pytest.fixture
def mock_tocfl_data():
    """Create mock TOCFL dictionary data."""
    with patch('pandas.read_csv') as mock_read_csv:
        df = pd.DataFrame([
            {'traditional': '公司', 'simplified': '公司', 'cefr_level': 'A2'},
            {'traditional': '今天', 'simplified': '今天', 'cefr_level': 'A1'},
            {'traditional': '介紹', 'simplified': '介绍', 'cefr_level': 'A2'},
            {'traditional': '科技', 'simplified': '科技', 'cefr_level': 'B1'}
        ])
        mock_read_csv.return_value = df
        return df

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="苹果公司发表新产品",
        english_title="Apple Announces New Product",
        mandarin_content="苹果公司今天发表新产品。库克介绍了最新科技。",
        english_content="Apple announced new products today. Tim Cook introduced the latest technology.",
        section_indices=[(0, 11), (11, 20)],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.fixture
def empty_article():
    """Create an empty article for testing error cases."""
    return Article(
        article_id="empty123",
        url="https://example.com/empty",
        date=datetime.now(),
        source="test_source",
        authors=[],
        mandarin_title="",
        english_title="",
        mandarin_content="",
        english_content="",
        section_indices=[],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.fixture
def mock_components():
    """Create mock components for testing."""
    return {
        'entity_extractor': Mock(),
        'tocfl_tagger': Mock(),
        'segmenter': Mock(),
        'html_wrapper': Mock(),
        'article_simplifier': Mock()
    }
