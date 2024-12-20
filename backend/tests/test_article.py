import pytest
from datetime import datetime
from backend.article.article import Article

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="测试标题",
        english_title="Test Title",
        mandarin_content="这是一个测试文章。这是第二句话。",
        english_content="This is a test article. This is the second sentence.",
        section_indices=[(0, 8), (8, 15)],
        image_url="https://example.com/image.jpg",
        graded_content=None,
        metadata={"category": "test"}
    )

def test_article_creation(sample_article):
    """Test basic article creation and attributes."""
    assert sample_article.article_id == "test123"
    assert sample_article.mandarin_title == "测试标题"
    assert len(sample_article.section_indices) == 2
    assert sample_article.graded_content is None

def test_get_section_content(sample_article):
    """Test retrieving section content."""
    mandarin, english = sample_article.get_section_content(0)
    assert mandarin == "这是一个测试文章"
    assert english == "This is a test article"
    
    mandarin, english = sample_article.get_section_content(1)
    assert mandarin == "这是第二句话"
    assert english == "This is the second sentence"

def test_get_section_content_invalid_index(sample_article):
    """Test error handling for invalid section index."""
    with pytest.raises(IndexError):
        sample_article.get_section_content(2)

def test_get_graded_content(sample_article):
    """Test retrieving graded content."""
    # Test native content
    assert sample_article.get_graded_content("native") == sample_article.mandarin_content
    
    # Test non-existent graded content
    assert sample_article.get_graded_content("BEGINNER") is None
    
    # Add graded content and test
    sample_article.add_graded_version("BEGINNER", "简单版本")
    assert sample_article.get_graded_content("BEGINNER") == "简单版本"

def test_add_graded_version(sample_article):
    """Test adding graded versions."""
    sample_article.add_graded_version("BEGINNER", "简单版本")
    sample_article.add_graded_version("INTERMEDIATE", "中级版本")
    
    assert sample_article.graded_content == {
        "BEGINNER": "简单版本",
        "INTERMEDIATE": "中级版本"
    }

def test_to_dict(sample_article):
    """Test converting article to dictionary."""
    article_dict = sample_article.to_dict()
    
    assert article_dict["article_id"] == sample_article.article_id
    assert article_dict["mandarin_title"] == sample_article.mandarin_title
    assert article_dict["section_indices"] == sample_article.section_indices
    assert article_dict["metadata"] == sample_article.metadata

def test_from_dict():
    """Test creating article from dictionary."""
    article_data = {
        "article_id": "test123",
        "url": "https://example.com/article",
        "date": datetime.now().isoformat(),
        "source": "test_source",
        "authors": ["Test Author"],
        "mandarin_title": "测试标题",
        "english_title": "Test Title",
        "mandarin_content": "测试内容",
        "english_content": "Test content",
        "section_indices": [(0, 4)],
        "image_url": "https://example.com/image.jpg",
        "graded_content": {"BEGINNER": "简单版本"},
        "metadata": {"category": "test"}
    }
    
    article = Article.from_dict(article_data)
    
    assert article.article_id == article_data["article_id"]
    assert article.mandarin_title == article_data["mandarin_title"]
    assert article.graded_content == article_data["graded_content"]
    assert len(article.section_indices) == 1

def test_article_immutability(sample_article):
    """Test that critical article attributes are not mutable."""
    with pytest.raises(AttributeError):
        sample_article.article_id = "new_id"
    
    with pytest.raises(AttributeError):
        sample_article.mandarin_content = "新内容"
