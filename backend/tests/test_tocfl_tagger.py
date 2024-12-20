import pytest
from unittest.mock import Mock, patch, mock_open
import pandas as pd
from typing import Dict
from backend.preprocessing.tocfl_tagger import TOCFLTagger

@pytest.fixture
def mock_csv_data():
    """Create mock TOCFL dictionary data."""
    return """traditional,simplified,cefr_level
學習,学习,A2
餐廳,餐厅,A2
電腦,电脑,B1
複雜,复杂,B2
簡單,简单,A1"""

@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client."""
    with patch('backend.utils.llm_client.LLMClient') as mock:
        return mock.return_value

@pytest.fixture
def tocfl_tagger(mock_csv_data, mock_llm_client):
    """Create a TOCFLTagger with mocked dependencies."""
    with patch('pandas.read_csv') as mock_read_csv:
        # Create mock DataFrame
        df = pd.DataFrame([
            {'traditional': '學習', 'simplified': '学习', 'cefr_level': 'A2'},
            {'traditional': '餐廳', 'simplified': '餐厅', 'cefr_level': 'A2'},
            {'traditional': '電腦', 'simplified': '电脑', 'cefr_level': 'B1'},
            {'traditional': '複雜', 'simplified': '复杂', 'cefr_level': 'B2'},
            {'traditional': '簡單', 'simplified': '简单', 'cefr_level': 'A1'}
        ])
        mock_read_csv.return_value = df
        
        return TOCFLTagger("dummy/path.csv")

def test_load_tocfl_dictionary(tocfl_tagger):
    """Test loading and initialization of TOCFL dictionary."""
    # Test traditional characters
    assert tocfl_tagger.get_word_info('學習') == {'level': 'A2', 'simplified': '学习'}
    assert tocfl_tagger.get_word_info('餐廳') == {'level': 'A2', 'simplified': '餐厅'}
    assert tocfl_tagger.get_word_info('電腦') == {'level': 'B1', 'simplified': '电脑'}
    
    # Test simplified characters
    assert tocfl_tagger.get_word_info('学习') == {'level': 'A2', 'simplified': '学习'}
    assert tocfl_tagger.get_word_info('餐厅') == {'level': 'A2', 'simplified': '餐厅'}
    assert tocfl_tagger.get_word_info('电脑') == {'level': 'B1', 'simplified': '电脑'}

def test_get_word_info_unknown(tocfl_tagger):
    """Test getting info for unknown words."""
    assert tocfl_tagger.get_word_info('未知詞') is None  # Traditional
    assert tocfl_tagger.get_word_info('未知词') is None  # Simplified

def test_create_ordered_dict(tocfl_tagger):
    """Test creation of ordered dictionary with CEFR levels."""
    ordered_dict = tocfl_tagger.create_ordered_dict()
    
    # Verify all levels are present in correct order
    expected_levels = ['A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'unknown']
    assert list(ordered_dict.keys()) == expected_levels
    
    # Verify all values are empty sets
    assert all(isinstance(val, set) and len(val) == 0 for val in ordered_dict.values())

@pytest.mark.llm
@pytest.mark.slow
def test_classify_unknown_words(tocfl_tagger, mock_llm_client):
    """Test classification of unknown words using LLM."""
    # Mock LLM response
    mock_llm_client.classify_words.return_value = {
        '未知詞一': 'B1',
        '未知詞二': 'A2'
    }
    
    # Classify unknown words
    result = tocfl_tagger.classify_unknown_words({'未知詞一', '未知詞二'})
    
    # Verify LLM was called correctly
    mock_llm_client.classify_words.assert_called_once()
    
    # Verify classifications
    assert result['未知詞一'] == 'B1'
    assert result['未知詞二'] == 'A2'

def test_classify_unknown_words_empty(tocfl_tagger, mock_llm_client):
    """Test classification with empty word set."""
    result = tocfl_tagger.classify_unknown_words(set())
    
    # Verify LLM wasn't called
    mock_llm_client.classify_words.assert_not_called()
    
    # Verify empty result
    assert result == {}

@pytest.mark.llm
def test_categorize_words(tocfl_tagger, mock_llm_client):
    """Test categorization of words by CEFR level."""
    # Mix of known and unknown words (traditional characters)
    words = ['學習', '餐廳', '未知詞一', '未知詞二', '電腦']
    
    # Mock LLM response for unknown words
    mock_llm_client.classify_words.return_value = {
        '未知詞一': 'B1',
        '未知詞二': 'A2'
    }
    
    # Categorize words
    result = tocfl_tagger.categorize_words(words)
    
    # Verify categorization (results should be in simplified form)
    assert '学习' in result['A2']
    assert '餐厅' in result['A2']
    assert '电脑' in result['B1']
    assert '未知詞一' in result['B1']
    assert '未知詞二' in result['A2']

@pytest.mark.llm
def test_get_word_level_map(tocfl_tagger, mock_llm_client):
    """Test creation of word to level mapping."""
    # Mix of traditional and simplified characters
    words = ['學習', '餐厅', '未知詞一', '未知詞二', '電腦']
    
    # Mock LLM response for unknown words
    mock_llm_client.classify_words.return_value = {
        '未知詞一': 'B1',
        '未知詞二': 'A2'
    }
    
    # Get word level mapping
    result = tocfl_tagger.get_word_level_map(words)
    
    # Verify mapping (input words should map to their levels)
    assert result['學習'] == 'A2'
    assert result['餐厅'] == 'A2'
    assert result['電腦'] == 'B1'
    assert result['未知詞一'] == 'B1'
    assert result['未知詞二'] == 'A2'

@pytest.mark.llm
def test_get_word_level_map_all_unknown(tocfl_tagger, mock_llm_client):
    """Test word level mapping with all unknown words."""
    words = ['未知詞一', '未知詞二', '未知詞三']
    
    # Mock LLM failure
    mock_llm_client.classify_words.return_value = {}
    
    # Get word level mapping
    result = tocfl_tagger.get_word_level_map(words)
    
    # Verify all words are marked as unknown
    assert all(level == 'unknown' for level in result.values())

@pytest.mark.llm
def test_error_handling(tocfl_tagger, mock_llm_client):
    """Test error handling in word classification."""
    words = ['學習', '未知詞']
    
    # Mock LLM error
    mock_llm_client.classify_words.side_effect = Exception("LLM error")
    
    # Get word level mapping should not raise exception
    result = tocfl_tagger.get_word_level_map(words)
    
    # Known words should still be classified
    assert result['學習'] == 'A2'
    # Unknown word should be marked as unknown due to LLM error
    assert result['未知詞'] == 'unknown'
