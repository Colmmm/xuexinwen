import pytest
from datetime import datetime
import json
from ..database.db_manager import DatabaseManager
from ..article.article import Article

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
        metadata={"category": "technology"}
    )

@pytest.fixture
def sample_processing_results():
    """Create sample processing results for testing."""
    return {
        'entities': {
            'organization': {
                '音乐应用程序': 'music app'
            },
            'misc': {
                '免费试用': 'free trial'
            }
        },
        'word_levels': {
            'A1': ['今天', '用户'],
            'A2': ['新的', '免费'],
            'B1': ['应用程序', '试用']
        },
        'graded_content': {
            'A2': '这个新的音乐软件今天出来了。大家可以免费用三十天。',
            'B1': '这个新的音乐应用今天发布。用户可以免费使用一个月。'
        }
    }

@pytest.mark.db
@pytest.mark.db_write
def test_add_article(db_manager, sample_article):
    """Test adding a new article."""
    db_manager.add_article(sample_article)
    
    # Verify article was added
    saved_article = db_manager.get_article(sample_article.article_id)
    assert saved_article is not None
    assert saved_article.article_id == sample_article.article_id
    assert saved_article.mandarin_title == sample_article.mandarin_title
    assert saved_article.english_title == sample_article.english_title
    assert saved_article.mandarin_content == sample_article.mandarin_content
    assert saved_article.english_content == sample_article.english_content
    assert saved_article.section_indices == sample_article.section_indices
    assert saved_article.metadata == sample_article.metadata

@pytest.mark.db
@pytest.mark.db_write
def test_update_article(db_manager, sample_article):
    """Test updating an existing article."""
    # First add the article
    db_manager.add_article(sample_article)
    
    # Modify and update
    sample_article.english_title = "Updated Title"
    db_manager.add_article(sample_article)
    
    # Verify update
    saved_article = db_manager.get_article(sample_article.article_id)
    assert saved_article.english_title == "Updated Title"

@pytest.mark.db
def test_check_article_status(db_manager, sample_article):
    """Test checking article status."""
    # Initially article shouldn't exist
    exists, processed = db_manager.check_article_status(sample_article.article_id)
    assert not exists
    assert not processed
    
    # Add article
    db_manager.add_article(sample_article)
    exists, processed = db_manager.check_article_status(sample_article.article_id)
    assert exists
    assert not processed
    
    # Mark as processed
    db_manager.mark_article_processed(sample_article.article_id)
    exists, processed = db_manager.check_article_status(sample_article.article_id)
    assert exists
    assert processed

@pytest.mark.db
@pytest.mark.db_write
def test_save_processing_results(db_manager, sample_article, sample_processing_results):
    """Test saving article processing results."""
    # Add article first
    db_manager.add_article(sample_article)
    
    # Save processing results
    db_manager.save_processing_results(
        article_id=sample_article.article_id,
        entities=sample_processing_results['entities'],
        word_levels=sample_processing_results['word_levels'],
        graded_content=sample_processing_results['graded_content']
    )
    
    # Verify results were saved
    results = db_manager.get_processing_results(sample_article.article_id)
    assert results is not None
    
    # Check entities
    assert '音乐应用程序' in results['entities']['organization']
    assert '免费试用' in results['entities']['misc']
    
    # Check word levels
    assert '今天' in results['word_levels']['A1']
    assert '新的' in results['word_levels']['A2']
    assert '应用程序' in results['word_levels']['B1']
    
    # Check graded content
    assert 'A2' in results['graded_content']
    assert 'B1' in results['graded_content']
    
    # Verify article was marked as processed
    exists, processed = db_manager.check_article_status(sample_article.article_id)
    assert exists
    assert processed

@pytest.mark.db
@pytest.mark.db_read
def test_get_articles(db_manager, sample_article):
    """Test retrieving multiple articles."""
    # Add sample article
    db_manager.add_article(sample_article)
    
    # Add another article
    another_article = Article(
        article_id="test456",
        url="https://example.com/article2",
        date=datetime.now(),
        source="test_source",
        authors=["Another Author"],
        mandarin_title="另一篇文章",
        english_title="Another Article",
        mandarin_content="这是另一篇测试文章。",
        english_content="This is another test article.",
        section_indices=[(0, 8)],
        image_url=None,
        graded_content=None,
        metadata=None
    )
    db_manager.add_article(another_article)
    
    # Test retrieving all articles
    articles = db_manager.get_articles()
    assert len(articles) == 2
    
    # Test filtering by source
    articles = db_manager.get_articles(source="test_source")
    assert len(articles) == 2
    
    # Test limit and offset
    articles = db_manager.get_articles(limit=1)
    assert len(articles) == 1
    
    articles = db_manager.get_articles(offset=1, limit=1)
    assert len(articles) == 1
    assert articles[0].article_id != articles[0].article_id

@pytest.mark.db
def test_error_handling(db_manager):
    """Test error handling for invalid operations."""
    # Test getting non-existent article
    article = db_manager.get_article("nonexistent")
    assert article is None
    
    # Test getting processing results for non-existent article
    with pytest.raises(Exception):
        db_manager.get_processing_results("nonexistent")
    
    # Test saving processing results for non-existent article
    with pytest.raises(Exception):
        db_manager.save_processing_results(
            article_id="nonexistent",
            entities={},
            word_levels={},
            graded_content={}
        )
