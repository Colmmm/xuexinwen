import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict
from backend.main_processing.simplify_articles import ArticleSimplifier
from backend.article.article import Article

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    with patch('backend.utils.llm_client.LLMClient') as mock:
        client = mock.return_value
        
        # Mock simplification
        client.simplify_to_multiple_levels.return_value = {
            'original': '這個新的音樂應用程序今天發布。用戶可以免費試用三十天。',
            'A2': '這個新的音樂軟件今天出來了。大家可以免費用三十天。',
            'B1': '這個新的音樂應用今天發布。用戶可以免費使用一個月。'
        }
        
        return client

@pytest.fixture
def simplifier(mock_llm_client):
    """Create an ArticleSimplifier with mocked LLM client."""
    return ArticleSimplifier()

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="新的音樂應用程序發布",
        english_title="New Music App Released",
        mandarin_content="這個新的音樂應用程序今天發布。用戶可以免費試用三十天。",
        english_content="The new music app was released today. Users can try it free for thirty days.",
        section_indices=[(0, 13), (13, 25)],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.mark.llm
@pytest.mark.slow
def test_simplify_article_basic(simplifier, mock_llm_client, sample_article):
    """Test basic article simplification."""
    # Mock LLM response for simplification
    mock_llm_client.simplify_to_multiple_levels.return_value = {
        'original': sample_article.mandarin_content,
        'A2': '這個新的音樂軟件今天出來了。大家可以免費用三十天。',
        'B1': '這個新的音樂應用今天發布。用戶可以免費使用一個月。'
    }
    
    # Simplify article
    simplifier.simplify_article(sample_article)
    
    # Verify LLM was called correctly
    mock_llm_client.simplify_to_multiple_levels.assert_called_once_with(
        zh_content=sample_article.mandarin_content,
        en_content=sample_article.english_content,
        levels=['B1', 'A2']
    )
    
    # Verify article was updated
    assert sample_article.graded_content is not None
    assert 'BEGINNER' in sample_article.graded_content
    assert 'INTERMEDIATE' in sample_article.graded_content

@pytest.mark.llm
def test_simplify_article_empty_response(simplifier, mock_llm_client, sample_article):
    """Test handling of empty response from LLM."""
    # Mock empty LLM response
    mock_llm_client.simplify_to_multiple_levels.return_value = {
        'original': sample_article.mandarin_content
    }
    
    # Simplify article
    simplifier.simplify_article(sample_article)
    
    # Verify article wasn't updated with empty content
    assert sample_article.graded_content is None or len(sample_article.graded_content) == 0

@pytest.mark.llm
def test_simplify_article_partial_response(simplifier, mock_llm_client, sample_article):
    """Test handling of partial response from LLM."""
    # Mock partial LLM response (only one level)
    mock_llm_client.simplify_to_multiple_levels.return_value = {
        'original': sample_article.mandarin_content,
        'A2': '這個新的音樂軟件今天出來了。大家可以免費用三十天。'
    }
    
    # Simplify article
    simplifier.simplify_article(sample_article)
    
    # Verify only available content was added
    assert sample_article.graded_content is not None
    assert 'BEGINNER' in sample_article.graded_content
    assert 'INTERMEDIATE' not in sample_article.graded_content

@pytest.mark.llm
def test_simplify_article_error_handling(simplifier, mock_llm_client, sample_article):
    """Test error handling during simplification."""
    # Mock LLM error
    mock_llm_client.simplify_to_multiple_levels.side_effect = Exception("LLM error")
    
    # Simplify article should not raise exception
    simplifier.simplify_article(sample_article)
    
    # Verify article wasn't modified
    assert sample_article.graded_content is None

def test_level_mapping(simplifier):
    """Test the CEFR to internal level mapping."""
    assert simplifier.level_mapping['A2'] == 'BEGINNER'
    assert simplifier.level_mapping['B1'] == 'INTERMEDIATE'

def test_simplify_empty_article(simplifier, mock_llm_client):
    """Test simplification of article with empty content."""
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
    
    # Simplify empty article
    simplifier.simplify_article(empty_article)
    
    # Verify LLM wasn't called for empty content
    mock_llm_client.simplify_to_multiple_levels.assert_not_called()
    
    # Verify article wasn't modified
    assert empty_article.graded_content is None

@pytest.mark.llm
def test_simplify_article_with_existing_content(simplifier, mock_llm_client, sample_article):
    """Test simplification of article that already has graded content."""
    # Add existing graded content
    sample_article.graded_content = {
        'BEGINNER': '舊版本',
        'INTERMEDIATE': '舊版本'
    }
    
    # Mock new LLM response
    mock_llm_client.simplify_to_multiple_levels.return_value = {
        'original': sample_article.mandarin_content,
        'A2': '新版本A2',
        'B1': '新版本B1'
    }
    
    # Simplify article
    simplifier.simplify_article(sample_article)
    
    # Verify content was updated
    assert sample_article.graded_content['BEGINNER'] == '新版本A2'
    assert sample_article.graded_content['INTERMEDIATE'] == '新版本B1'
