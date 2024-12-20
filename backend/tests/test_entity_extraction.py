import pytest
from unittest.mock import Mock, patch
from datetime import datetime
from typing import Dict
from backend.preprocessing.entity_extraction import EntityExtractor
from backend.article.article import Article

@pytest.fixture
def mock_llm_response():
    """Mock response from LLM for entity extraction."""
    return [
        {
            "word": "马斯克",
            "type": "person",
            "english": "Elon Musk, CEO of Tesla and SpaceX"
        },
        {
            "word": "硅谷",
            "type": "place",
            "english": "Silicon Valley"
        },
        {
            "word": "特斯拉",
            "type": "organization",
            "english": "Tesla"
        },
        {
            "word": "人工智能",
            "type": "other",
            "english": "Artificial Intelligence (AI)"
        }
    ]

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="特斯拉发布新人工智能系统",
        english_title="Tesla Announces New AI System",
        mandarin_content="马斯克在硅谷宣布特斯拉的最新人工智能系统。这项技术将改变自动驾驶的未来。",
        english_content="Elon Musk announces Tesla's latest AI system in Silicon Valley. This technology will transform the future of autonomous driving.",
        section_indices=[(0, 19), (19, 33)],
        image_url=None,
        graded_content=None,
        metadata=None
    )

@pytest.fixture
def entity_extractor():
    """Create an EntityExtractor instance with mocked LLM client."""
    return EntityExtractor()

@pytest.mark.llm
@pytest.mark.slow
def test_entity_extraction(entity_extractor, sample_article, mock_llm_response):
    """Test the extraction of entities from article content."""
    # Mock the LLM client's extract_entities method
    with patch('backend.utils.llm_client.LLMClient.extract_entities') as mock_extract:
        mock_extract.return_value = mock_llm_response
        
        # Extract entities
        entities = entity_extractor.extract_entities(sample_article)
        
        # Verify entity categories
        assert "names" in entities
        assert "places" in entities
        assert "organizations" in entities
        assert "misc" in entities
        
        # Verify specific entities
        assert entities["names"]["马斯克"] == "Elon Musk, CEO of Tesla and SpaceX"
        assert entities["places"]["硅谷"] == "Silicon Valley"
        assert entities["organizations"]["特斯拉"] == "Tesla"
        assert entities["misc"]["人工智能"] == "Artificial Intelligence (AI)"

@pytest.mark.llm
def test_entity_extraction_empty_response(entity_extractor, sample_article):
    """Test handling of empty response from LLM."""
    with patch('backend.utils.llm_client.LLMClient.extract_entities') as mock_extract:
        mock_extract.return_value = []
        
        entities = entity_extractor.extract_entities(sample_article)
        
        # Verify empty categories are present
        assert all(len(entities[cat]) == 0 for cat in ["names", "places", "organizations", "misc"])

@pytest.mark.llm
def test_entity_extraction_invalid_response(entity_extractor, sample_article):
    """Test handling of invalid response from LLM."""
    with patch('backend.utils.llm_client.LLMClient.extract_entities') as mock_extract:
        # Missing required fields
        mock_extract.return_value = [
            {"word": "马斯克"},  # Missing type and english
            {"type": "place", "english": "Silicon Valley"},  # Missing word
            {"word": "特斯拉", "type": "invalid_type", "english": "Tesla"}  # Invalid type
        ]
        
        entities = entity_extractor.extract_entities(sample_article)
        
        # Verify only valid entities are included
        assert all(cat in entities for cat in ["names", "places", "organizations", "misc"])
        assert all(len(entities[cat]) == 0 for cat in ["names", "places"])  # Invalid entries should be skipped
        assert len(entities["organizations"]) == 0  # Invalid type should be skipped

def test_get_all_entities(entity_extractor):
    """Test getting a flat list of all entity words."""
    # Create a sample entities dictionary
    entities = {
        "names": {"马斯克": "Elon Musk"},
        "places": {"硅谷": "Silicon Valley", "西雅图": "Seattle"},
        "organizations": {"特斯拉": "Tesla"},
        "misc": {"人工智能": "AI"}
    }
    
    all_entities = entity_extractor.get_all_entities(entities)
    
    # Verify all entities are included
    assert len(all_entities) == 5
    assert "马斯克" in all_entities
    assert "硅谷" in all_entities
    assert "西雅图" in all_entities
    assert "特斯拉" in all_entities
    assert "人工智能" in all_entities

def test_type_mapping(entity_extractor):
    """Test the entity type mapping."""
    assert entity_extractor.type_mapping["person"] == "names"
    assert entity_extractor.type_mapping["place"] == "places"
    assert entity_extractor.type_mapping["organization"] == "organizations"
    assert entity_extractor.type_mapping["other"] == "misc"
