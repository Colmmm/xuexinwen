import pytest
from unittest.mock import Mock, patch
from datetime import datetime
import pandas as pd
from typing import Dict
from backend.article.article import Article
from backend.article.article_processor import ArticleProcessor

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    with patch('backend.utils.llm_client.LLMClient') as mock:
        client = mock.return_value
        
        # Mock entity extraction
        client.extract_entities.return_value = [
            {
                "word": "蘋果公司",
                "type": "organization",
                "english": "Apple Inc."
            },
            {
                "word": "庫克",
                "type": "person",
                "english": "Tim Cook, CEO of Apple"
            }
        ]
        
        # Mock word classification
        client.classify_words.return_value = {
            "發表": "B1",
            "新產品": "A2"
        }
        
        # Mock simplification
        client.simplify_to_multiple_levels.return_value = {
            "original": "蘋果公司今天發表新產品。庫克介紹了最新科技。",
            "A2": "蘋果公司今天介紹新東西。庫克說明了新科技。",
            "B1": "蘋果公司今天發表新產品。庫克介紹了新技術。"
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
        mandarin_title="蘋果公司發表新產品",
        english_title="Apple Announces New Product",
        mandarin_content="蘋果公司今天發表新產品。庫克介紹了最新科技。",
        english_content="Apple announced new products today. Tim Cook introduced the latest technology.",
        section_indices=[(0, 11), (11, 20)],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.mark.db
@pytest.mark.llm
@pytest.mark.slow
def test_complete_article_processing(mock_llm_client, mock_tocfl_data, sample_article):
    """Test complete article processing pipeline."""
    # Initialize processor
    processor = ArticleProcessor(tocfl_csv_path="dummy/path.csv")
    
    # Process article
    result = processor.process_article(sample_article, simplify=True)
    
    # Verify structure of result
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    
    # Verify entity extraction
    assert "蘋果公司" in result["entities"]["organizations"]
    assert "庫克" in result["entities"]["names"]
    
    # Verify HTML versions exist
    assert "native" in result["html_versions"]
    assert "BEGINNER" in result["html_versions"]
    assert "INTERMEDIATE" in result["html_versions"]
    
    # Verify HTML content includes proper wrapping
    native_html = result["html_versions"]["native"]
    assert 'class="word-' in native_html
    assert 'data-definition=' in native_html
    assert 'data-entity="true"' in native_html
    
    # Verify word levels were properly categorized
    assert any(word in result["word_levels"]["A1"] for word in ["今天"])
    assert any(word in result["word_levels"]["A2"] for word in ["公司"])
    assert any(word in result["word_levels"]["B1"] for word in ["科技"])

@pytest.mark.db
@pytest.mark.llm
def test_error_recovery(mock_llm_client, mock_tocfl_data, sample_article):
    """Test pipeline recovery from component failures."""
    # Make entity extraction fail
    mock_llm_client.extract_entities.side_effect = Exception("Entity extraction failed")
    
    # Initialize processor
    processor = ArticleProcessor(tocfl_csv_path="dummy/path.csv")
    
    # Process should continue with empty entities
    result = processor.process_article(sample_article)
    
    # Verify basic processing still worked
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    
    # Verify empty entities didn't break the pipeline
    assert all(len(entities) == 0 for entities in result["entities"].values())
    assert "native" in result["html_versions"]

@pytest.mark.db
@pytest.mark.llm
def test_empty_article_processing(mock_llm_client, mock_tocfl_data):
    """Test processing of empty article."""
    empty_article = Article(
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
    
    # Initialize processor
    processor = ArticleProcessor(tocfl_csv_path="dummy/path.csv")
    
    # Process empty article
    result = processor.process_article(empty_article)
    
    # Verify result structure is maintained
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    
    # Verify empty content produces empty results
    assert all(len(entities) == 0 for entities in result["entities"].values())
    assert result["html_versions"]["native"] == ""
    assert all(len(words) == 0 for words in result["word_levels"].values())
