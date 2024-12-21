import pytest
from datetime import datetime
from ..preprocessing.segmentation import Segmenter
from ..article.article import Article

@pytest.fixture
def segmenter():
    """Create a Segmenter instance for testing."""
    return Segmenter()

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
        mandarin_section_indices=[(0, 13), (13, 25)],
        english_section_indices=[(0, 35), (36, 71)],
        image_url=None,
        graded_content={
            "BEGINNER": "这个新的音乐软件今天出来了。大家可以免费用三十天。"
        },
        metadata=None
    )

def test_clean_word():
    """Test cleaning of individual words."""
    segmenter = Segmenter()
    
    # Test normal word
    assert segmenter._clean_word("音乐") == "音乐"
    
    # Test word with whitespace
    assert segmenter._clean_word("  音乐  ") == "音乐"
    
    # Test punctuation only
    assert segmenter._clean_word("。") is None
    assert segmenter._clean_word("！") is None
    
    # Test empty string
    assert segmenter._clean_word("") is None
    assert segmenter._clean_word("   ") is None

def test_add_words_to_dictionary(segmenter):
    """Test adding custom words to Jieba dictionary."""
    custom_words = ["音乐应用程序", "免费试用", "音乐软件"]
    segmenter.add_words_to_dictionary(custom_words)
    
    # Segment text containing custom words
    text = "这个音乐应用程序提供免费试用"
    words = segmenter.segment_text(text)
    
    # Verify custom words are kept together
    assert "音乐应用程序" in words
    assert "免费试用" in words

def test_segment_text(segmenter):
    """Test basic text segmentation."""
    text = "这个新的音乐应用程序今天发布"
    words = segmenter.segment_text(text)
    
    # Verify basic segmentation
    assert len(words) > 0
    assert all(w.strip() for w in words)  # No empty or whitespace-only words
    assert "。" not in words  # No punctuation
    
    # Test with custom words
    custom_words = ["音乐应用程序"]
    words = segmenter.segment_text(text, custom_words)
    assert "音乐应用程序" in words

def test_segment_article(segmenter, sample_article):
    """Test segmentation of article content."""
    # Add some custom words
    custom_words = ["音乐应用程序", "免费试用", "音乐软件"]
    
    # Segment the article
    segmented_versions = segmenter.segment_article(sample_article, custom_words)
    
    # Verify native content segmentation
    assert "native" in segmented_versions
    native_words = segmented_versions["native"]
    assert len(native_words) > 0
    assert "音乐应用程序" in native_words
    assert "免费试用" in native_words
    
    # Verify graded content segmentation
    assert "BEGINNER" in segmented_versions
    beginner_words = segmented_versions["BEGINNER"]
    assert len(beginner_words) > 0
    assert "音乐软件" in beginner_words  # Simplified version uses different words

def test_get_sentence_boundaries(segmenter):
    """Test sentence boundary detection."""
    text = "第一句话。第二句话！第三句话？最后一句"
    boundaries = segmenter.get_sentence_boundaries(text)
    
    # Verify number of sentences
    assert len(boundaries) == 4
    
    # Verify boundary positions
    assert boundaries[0] == (0, 5)   # First sentence
    assert boundaries[1] == (5, 10)  # Second sentence
    assert boundaries[2] == (10, 15) # Third sentence
    assert boundaries[3] == (15, 19) # Last sentence (no ending punctuation)
    
    # Verify sentence extraction
    first_sentence = text[boundaries[0][0]:boundaries[0][1]].strip()
    assert first_sentence == "第一句话。"  # Include the period
    assert text[boundaries[1][0]:boundaries[1][1]].strip() == "第二句话！"
    assert text[boundaries[2][0]:boundaries[2][1]].strip() == "第三句话？"
    assert text[boundaries[3][0]:boundaries[3][1]].strip() == "最后一句"

def test_empty_text_segmentation(segmenter):
    """Test handling of empty or whitespace-only text."""
    assert segmenter.segment_text("") == []
    assert segmenter.segment_text("   ") == []
    assert segmenter.segment_text("。！？") == []

def test_mixed_content_segmentation(segmenter):
    """Test segmentation of text with mixed content types."""
    text = "音乐APP2023版本发布了。"  # Mix of Chinese, English, and numbers
    words = segmenter.segment_text(text)
    
    # Verify handling of different content types
    assert len(words) > 0
    assert any("APP" in w for w in words)
    assert any("2023" in w for w in words)
    assert "。" not in words  # Punctuation should be removed
