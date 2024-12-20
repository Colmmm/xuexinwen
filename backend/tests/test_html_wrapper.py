import pytest
from datetime import datetime
from ..postprocessing.html_wrapper import HTMLWrapper
from ..article.article import Article

@pytest.fixture
def html_wrapper():
    """Create an HTMLWrapper instance for testing."""
    return HTMLWrapper()

@pytest.fixture
def sample_article():
    """Create a sample article for testing."""
    return Article(
        article_id="test123",
        url="https://example.com/article",
        date=datetime.now(),
        source="test_source",
        authors=["Test Author"],
        mandarin_title="美食评论家推荐餐厅",
        english_title="Food Critic Recommends Restaurants",
        mandarin_content="著名美食评论家推荐了三家新餐厅。这些餐厅的特色是创新料理。",
        english_content="Famous food critic recommended three new restaurants. These restaurants specialize in innovative cuisine.",
        section_indices=[(0, 14), (14, 26)],
        image_url=None,
        graded_content={
            "BEGINNER": "有名的美食家介绍三家新餐厅。这些餐厅做新的菜。"
        },
        metadata=None
    )

def test_wrap_word_basic(html_wrapper):
    """Test basic word wrapping with minimal attributes."""
    wrapped = html_wrapper.wrap_word("餐厅", "B1")
    assert wrapped == '<span class="word-b1">餐厅</span>'

def test_wrap_word_with_definition(html_wrapper):
    """Test word wrapping with definition."""
    wrapped = html_wrapper.wrap_word(
        word="餐厅",
        level="B1",
        definition="restaurant"
    )
    assert 'class="word-b1"' in wrapped
    assert 'data-definition="restaurant"' in wrapped
    assert '>餐厅</span>' in wrapped

def test_wrap_word_with_all_attributes(html_wrapper):
    """Test word wrapping with all possible attributes."""
    wrapped = html_wrapper.wrap_word(
        word="餐厅",
        level="B1",
        definition="restaurant",
        pinyin="cān tīng",
        is_entity=True
    )
    assert 'class="word-b1"' in wrapped
    assert 'data-definition="restaurant"' in wrapped
    assert 'data-pinyin="cān tīng"' in wrapped
    assert 'data-entity="true"' in wrapped
    assert '>餐厅</span>' in wrapped

def test_wrap_word_escaping(html_wrapper):
    """Test proper HTML escaping in word wrapping."""
    wrapped = html_wrapper.wrap_word(
        word='餐厅"&<>',
        level="B1",
        definition='restaurant"&<>'
    )
    assert '"&<>' not in wrapped  # Raw special characters should not appear
    assert '&quot;' in wrapped or '&#34;' in wrapped  # Quotes should be escaped
    assert '&amp;' in wrapped  # Ampersands should be escaped
    assert '&lt;' in wrapped  # Less than should be escaped
    assert '&gt;' in wrapped  # Greater than should be escaped

def test_process_text(html_wrapper):
    """Test processing a list of words into HTML."""
    words = ["美食", "评论家", "推荐", "餐厅"]
    word_levels = {
        "美食": "B1",
        "评论家": "B2",
        "推荐": "A2",
        "餐厅": "A2"
    }
    entity_definitions = {
        "names": {},
        "places": {},
        "organizations": {
            "餐厅": "restaurant"
        },
        "misc": {
            "美食": "gourmet food"
        }
    }
    pinyin_dict = {
        "美食": "měi shí",
        "餐厅": "cān tīng"
    }
    
    html = html_wrapper.process_text(
        words=words,
        word_levels=word_levels,
        entity_definitions=entity_definitions,
        pinyin_dict=pinyin_dict
    )
    
    # Verify each word is properly wrapped
    assert 'class="word-b1"' in html  # 美食
    assert 'class="word-b2"' in html  # 评论家
    assert 'class="word-a2"' in html  # 推荐, 餐厅
    assert 'data-definition="gourmet food"' in html  # 美食 definition
    assert 'data-definition="restaurant"' in html  # 餐厅 definition
    assert 'data-pinyin="měi shí"' in html  # 美食 pinyin
    assert 'data-pinyin="cān tīng"' in html  # 餐厅 pinyin

def test_process_article(html_wrapper, sample_article):
    """Test processing an entire article with multiple versions."""
    words = ["美食", "评论家", "推荐", "餐厅"]
    word_levels = {
        "美食": "B1",
        "评论家": "B2",
        "推荐": "A2",
        "餐厅": "A2"
    }
    entity_definitions = {
        "names": {},
        "places": {},
        "organizations": {
            "餐厅": "restaurant"
        },
        "misc": {
            "美食": "gourmet food"
        }
    }
    
    html_versions = html_wrapper.process_article(
        article=sample_article,
        words=words,
        word_levels=word_levels,
        entity_definitions=entity_definitions
    )
    
    # Verify all versions are processed
    assert "native" in html_versions
    assert "BEGINNER" in html_versions
    
    # Verify content of each version
    native_html = html_versions["native"]
    assert "美食评论家" in native_html
    assert "餐厅" in native_html
    assert 'class="word-b1"' in native_html
    assert 'class="word-b2"' in native_html
    
    beginner_html = html_versions["BEGINNER"]
    assert "美食家" in beginner_html  # Simplified version
    assert "餐厅" in beginner_html
    assert 'class="word-b1"' in beginner_html

def test_empty_content(html_wrapper):
    """Test handling of empty content."""
    # Empty word list
    assert html_wrapper.process_text([], {}, {}) == ""
    
    # Empty word with attributes
    wrapped = html_wrapper.wrap_word("", "A1")
    assert wrapped == '<span class="word-a1"></span>'

def test_missing_attributes(html_wrapper):
    """Test handling of missing optional attributes."""
    words = ["餐厅"]
    word_levels = {"餐厅": "A2"}
    
    # No entity definitions
    html = html_wrapper.process_text(words, word_levels, {})
    assert 'class="word-a2"' in html
    assert 'data-definition' not in html
    
    # No pinyin
    html = html_wrapper.process_text(words, word_levels, {}, None)
    assert 'data-pinyin' not in html
