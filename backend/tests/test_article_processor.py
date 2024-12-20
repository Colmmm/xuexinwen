import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict
from backend.article.article_processor import ArticleProcessor
from backend.article.article import Article

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

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="新的音乐应用程序发布",
        english_title="New Music App Released",
        mandarin_content="这个新的音乐应用程序今天发布。用户可以免费试用三十天。",
        english_content="The new music app was released today. Users can try it free for thirty days.",
        section_indices=[(0, 13), (13, 25)],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.fixture
def mock_processor(mock_components):
    """Create an ArticleProcessor with mocked components."""
    with patch('backend.preprocessing.entity_extraction.EntityExtractor') as mock_ee, \
         patch('backend.preprocessing.tocfl_tagger.TOCFLTagger') as mock_tt, \
         patch('backend.preprocessing.segmentation.Segmenter') as mock_seg, \
         patch('backend.postprocessing.html_wrapper.HTMLWrapper') as mock_hw, \
         patch('backend.main_processing.simplify_articles.ArticleSimplifier') as mock_as:
        
        # Set up mock returns
        mock_ee.return_value = mock_components['entity_extractor']
        mock_tt.return_value = mock_components['tocfl_tagger']
        mock_seg.return_value = mock_components['segmenter']
        mock_hw.return_value = mock_components['html_wrapper']
        mock_as.return_value = mock_components['article_simplifier']
        
        processor = ArticleProcessor(tocfl_csv_path="dummy/path.csv")
        return processor

@pytest.mark.llm
@pytest.mark.slow
def test_process_article_basic(mock_processor, mock_components, sample_article):
    """Test basic article processing without simplification."""
    # Set up mock returns
    mock_components['entity_extractor'].extract_entities.return_value = {
        "names": {},
        "places": {},
        "organizations": {"音乐应用程序": "music app"},
        "misc": {}
    }
    mock_components['entity_extractor'].get_all_entities.return_value = ["音乐应用程序"]
    
    mock_components['segmenter'].segment_article.return_value = {
        "native": ["这个", "新的", "音乐应用程序", "今天", "发布"]
    }
    
    mock_components['tocfl_tagger'].get_word_level_map.return_value = {
        "这个": "A1",
        "新的": "A2",
        "音乐应用程序": "B1",
        "今天": "A1",
        "发布": "B1"
    }
    
    mock_components['tocfl_tagger'].categorize_words.return_value = {
        "A1": ["这个", "今天"],
        "A2": ["新的"],
        "B1": ["音乐应用程序", "发布"]
    }
    
    mock_components['html_wrapper'].process_article.return_value = {
        "native": "<span>wrapped content</span>"
    }
    
    # Process article
    result = mock_processor.process_article(sample_article, simplify=False)
    
    # Verify all components were called correctly
    mock_components['entity_extractor'].extract_entities.assert_called_once_with(sample_article)
    mock_components['segmenter'].segment_article.assert_called_once()
    mock_components['tocfl_tagger'].get_word_level_map.assert_called_once()
    mock_components['html_wrapper'].process_article.assert_called_once()
    mock_components['article_simplifier'].simplify_article.assert_not_called()
    
    # Verify result structure
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    assert result["html_versions"]["native"] == "<span>wrapped content</span>"

@pytest.mark.llm
@pytest.mark.slow
def test_process_article_with_simplification(mock_processor, mock_components, sample_article):
    """Test article processing with simplification enabled."""
    # Set up basic mock returns as before
    mock_components['entity_extractor'].extract_entities.return_value = {
        "names": {},
        "places": {},
        "organizations": {"音乐应用程序": "music app"},
        "misc": {}
    }
    mock_components['entity_extractor'].get_all_entities.return_value = ["音乐应用程序"]
    
    # Add simplified version
    mock_components['segmenter'].segment_article.return_value = {
        "native": ["这个", "新的", "音乐应用程序", "今天", "发布"],
        "BEGINNER": ["这个", "新的", "音乐软件", "今天", "出来了"]
    }
    
    mock_components['html_wrapper'].process_article.return_value = {
        "native": "<span>original content</span>",
        "BEGINNER": "<span>simplified content</span>"
    }
    
    # Process article with simplification
    result = mock_processor.process_article(sample_article, simplify=True)
    
    # Verify simplifier was called
    mock_components['article_simplifier'].simplify_article.assert_called_once_with(sample_article)
    
    # Verify result includes both versions
    assert "native" in result["html_versions"]
    assert "BEGINNER" in result["html_versions"]

@pytest.mark.llm
def test_error_recovery(mock_processor, mock_components, sample_article):
    """Test pipeline recovery from component failures."""
    # Make entity extraction fail
    mock_components['entity_extractor'].extract_entities.side_effect = Exception("Entity extraction failed")
    
    # Process should continue with empty entities
    result = mock_processor.process_article(sample_article)
    
    # Verify basic processing still worked
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    
    # Verify empty entities didn't break the pipeline
    assert all(len(entities) == 0 for entities in result["entities"].values())
    assert "native" in result["html_versions"]

def test_empty_article_processing(mock_processor, mock_components):
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
    
    # Process empty article
    result = mock_processor.process_article(empty_article)
    
    # Verify result structure is maintained
    assert "html_versions" in result
    assert "entities" in result
    assert "word_levels" in result
    
    # Verify empty content produces empty results
    assert all(len(entities) == 0 for entities in result["entities"].values())
    assert result["html_versions"]["native"] == ""
    assert all(len(words) == 0 for words in result["word_levels"].values())
