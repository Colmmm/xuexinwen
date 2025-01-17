import pytest
from unittest.mock import Mock, patch
from typing import Dict, List

from backend.processing.processing_utils.metadata_generator import MetadataGenerator
from backend.article.processed_article import WordMetadataEntry, WordMetadata, VersionType

# Mock dictionary entry structure to match chinese_english_lookup.Dictionary
class MockDictionaryEntry:
    def __init__(self, simp: str, trad: str, pinyin: str, definitions: List[str]):
        self.simp = simp
        self.trad = trad
        self.definition_entries = [
            Mock(pinyin=pinyin, definitions=definitions)
        ]

@pytest.fixture
def mock_dictionary():
    """Create a mock Dictionary with some predefined entries."""
    dictionary = Mock()
    
    # Define some test entries
    entries = {
        "你好": MockDictionaryEntry(
            simp="你好",
            trad="你好",
            pinyin="ni3 hao3",
            definitions=["hello", "hi"]
        ),
        "世界": MockDictionaryEntry(
            simp="世界",
            trad="世界",
            pinyin="shi4 jie4",
            definitions=["world"]
        )
    }
    
    def mock_lookup(word: str):
        return entries.get(word)
    
    dictionary.lookup = mock_lookup
    return dictionary

@pytest.fixture
def metadata_generator(mock_dictionary):
    """Create a MetadataGenerator instance with mocked dependencies."""
    with patch('backend.processing.processing_utils.metadata_generator.Dictionary') as mock_dict_class, \
         patch('backend.processing.processing_utils.metadata_generator.opencc.OpenCC') as mock_opencc, \
         patch('backend.processing.processing_utils.metadata_generator.pinyin') as mock_pinyin, \
         patch('backend.processing.processing_utils.metadata_generator.to_tone') as mock_to_tone:
        mock_dict_class.return_value = mock_dictionary
        # Mock OpenCC converter
        mock_converter = Mock()
        mock_converter.convert.side_effect = lambda x: x.replace('简', '簡')  # Simple S->T conversion for testing
        mock_opencc.return_value = mock_converter
        # Mock pypinyin
        mock_pinyin.side_effect = lambda word, style: [[f"ce{style}"] if "测" in word else [f"shi{style}"]]
        # Mock tone converter
        mock_to_tone.side_effect = lambda pinyin_str: pinyin_str.replace("ce<Style.TONE>", "cè").replace("shi<Style.TONE>", "shì")
        generator = MetadataGenerator()
        return generator

def test_generate_word_metadata_with_dictionary_entry(metadata_generator):
    """Test generating metadata for a word that exists in the dictionary."""
    metadata = metadata_generator._generate_word_metadata("你好", "native")
    
    assert isinstance(metadata, WordMetadataEntry)
    assert metadata.simplified == "你好"
    assert metadata.traditional == "你好"
    assert metadata.pinyin == "nǐ hǎo"  # Should be converted to tonal form
    assert metadata.definition == "hello; hi"
    assert metadata.grade == "unknown"  # Should be unknown until LLM fills it
    assert metadata.entity_type is False
    assert metadata.presence_in_versions == ["native"]

def test_generate_word_metadata_without_dictionary_entry(metadata_generator):
    """Test generating metadata for a word not in the dictionary."""
    metadata = metadata_generator._generate_word_metadata("测试", "native")
    
    assert isinstance(metadata, WordMetadataEntry)
    assert metadata.simplified == "测试"
    assert metadata.traditional != ""  # Should have a traditional form from opencc
    assert metadata.pinyin != ""  # Should have pinyin from pypinyin
    assert metadata.definition == ""  # Should be empty since not in dictionary
    assert metadata.grade == "unknown"
    assert metadata.entity_type is False
    assert metadata.presence_in_versions == ["native"]

def test_process_segmented_words_new_word(metadata_generator):
    """Test processing segments with a new word."""
    existing_metadata = WordMetadata()
    segments = ["你好", "世界"]
    
    new_words = metadata_generator._process_segmented_words(
        segments, "native", existing_metadata
    )
    
    assert new_words == {"你好", "世界"}

def test_process_segmented_words_existing_word(metadata_generator):
    """Test processing segments with an existing word."""
    existing_metadata = WordMetadata()
    existing_entry = WordMetadataEntry(
        simplified="你好",
        traditional="你好",
        grade="A1",
        definition="hello",
        pinyin="nǐ hǎo",
        entity_type=False,
        presence_in_versions=["native"]
    )
    existing_metadata.add_or_update_metadata(existing_entry)
    
    segments = ["你好", "世界"]
    new_words = metadata_generator._process_segmented_words(
        segments, "intermediate", existing_metadata
    )
    
    # Should only return 世界 as new word since 你好 exists
    assert new_words == {"世界"}
    # 你好 should now have both versions
    assert "intermediate" in existing_metadata.get_metadata("你好").presence_in_versions

def test_generate_from_segments_new_words(metadata_generator):
    """Test generating metadata for new words from segments."""
    segments = ["你好", "世界"]
    result = metadata_generator.generate_from_segments(segments, "native")
    
    assert isinstance(result, WordMetadata)
    assert len(result.get_all_metadata()) == 2
    assert "你好" in result.get_all_metadata()
    assert "世界" in result.get_all_metadata()

def test_generate_from_segments_with_existing_metadata(metadata_generator):
    """Test generating metadata with existing metadata."""
    existing_metadata = WordMetadata()
    existing_entry = WordMetadataEntry(
        simplified="你好",
        traditional="你好",
        grade="A1",
        definition="hello",
        pinyin="nǐ hǎo",
        entity_type=False,
        presence_in_versions=["native"]
    )
    existing_metadata.add_or_update_metadata(existing_entry)
    
    segments = ["你好", "世界"]
    result = metadata_generator.generate_from_segments(
        segments, "intermediate", existing_metadata
    )
    
    assert isinstance(result, WordMetadata)
    assert len(result.get_all_metadata()) == 2
    # Check that existing word maintained its data
    hello_entry = result.get_metadata("你好")
    assert hello_entry.grade == "A1"
    assert set(hello_entry.presence_in_versions) == {"native", "intermediate"}

@patch('backend.processing.processing_utils.metadata_generator.LLMClient')
def test_fill_missing_metadata(mock_llm, metadata_generator):
    """Test filling missing metadata using LLM."""
    # Setup mock LLM response
    mock_llm_instance = Mock()
    mock_llm_instance.make_request.return_value = '''[
        {
            "word": "测试",
            "definition": "test",
            "grade": "A2"
        }
    ]'''
    mock_llm.return_value = mock_llm_instance
    metadata_generator.llm_client = mock_llm_instance
    
    # Create metadata with missing fields
    metadata = WordMetadata()
    entry = WordMetadataEntry(
        simplified="测试",
        traditional="測試",
        grade="unknown",
        definition="",
        pinyin="cè shì",
        entity_type=False,
        presence_in_versions=["native"]
    )
    metadata.add_or_update_metadata(entry)
    
    # Fill missing metadata
    metadata_generator._fill_missing_metadata(metadata)
    
    # Check that metadata was updated
    updated_entry = metadata.get_metadata("测试")
    assert updated_entry.definition == "test"
    assert updated_entry.grade == "A2"
