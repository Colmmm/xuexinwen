import pytest
from datetime import datetime
from backend.fetching.fetch_articles import create_article_from_raw, generate_article_id

def test_create_article_from_raw():
    """Test creating an Article instance from raw article data."""
    raw_data = {
        'url': 'https://example.com/article',
        'mandarin_title': '测试标题',
        'english_title': 'Test Title',
        'authors': 'John Doe, Jane Smith',
        'date': '2024-01-01T12:00:00Z',
        'mandarin_paragraphs': [
            '第一段。',
            '第二段。'
        ],
        'english_paragraphs': [
            'First paragraph.',
            'Second paragraph.'
        ],
        'image_url': 'https://example.com/image.jpg'
    }
    
    article = create_article_from_raw(raw_data, 'test_source')
    
    # Test basic attributes
    assert article.url == raw_data['url']
    assert article.mandarin_title == raw_data['mandarin_title']
    assert article.english_title == raw_data['english_title']
    assert article.authors == ['John Doe', 'Jane Smith']
    assert article.source == 'test_source'
    assert article.image_url == raw_data['image_url']
    
    # Test content
    assert article.mandarin_content == '第一段。\n第二段。'
    assert article.english_content == 'First paragraph.\nSecond paragraph.'
    
    # Test section indices
    assert article.mandarin_section_indices == [(0, 4), (5, 9)]  # Each Chinese character is 1 unit
    assert article.english_section_indices == [(0, 16), (17, 34)]  # Including the period
    
    # Test content retrieval using indices
    mandarin_1, english_1 = article.get_section_content(0)
    assert mandarin_1 == '第一段。'
    assert english_1 == 'First paragraph.'
    
    mandarin_2, english_2 = article.get_section_content(1)
    assert mandarin_2 == '第二段。'
    assert english_2 == 'Second paragraph.'

def test_create_article_from_raw_with_single_author():
    """Test creating an Article with a single author string."""
    raw_data = {
        'url': 'https://example.com/article',
        'mandarin_title': '测试标题',
        'english_title': 'Test Title',
        'authors': 'Single Author',
        'date': datetime.now(),
        'mandarin_paragraphs': ['测试内容'],
        'english_paragraphs': ['Test content'],
        'image_url': 'https://example.com/image.jpg'
    }
    
    article = create_article_from_raw(raw_data, 'test_source')
    assert article.authors == ['Single Author']

def test_create_article_from_raw_with_no_authors():
    """Test creating an Article with no valid authors."""
    raw_data = {
        'url': 'https://example.com/article',
        'mandarin_title': '测试标题',
        'english_title': 'Test Title',
        'authors': 'No authors found',
        'date': datetime.now(),
        'mandarin_paragraphs': ['测试内容'],
        'english_paragraphs': ['Test content'],
        'image_url': 'https://example.com/image.jpg'
    }
    
    article = create_article_from_raw(raw_data, 'test_source')
    assert article.authors == []

def test_generate_article_id():
    """Test article ID generation."""
    url = 'https://example.com/article'
    article_id = generate_article_id(url)
    
    assert article_id.startswith('a')
    assert len(article_id) == 16  # 'a' + 15 chars from hash
    
    # Same URL should generate same ID
    assert generate_article_id(url) == article_id
    
    # Different URLs should generate different IDs
    different_url = 'https://example.com/different'
    assert generate_article_id(different_url) != article_id
