from typing import Dict, List, Optional
import html

class HTMLWrapper:
    def __init__(self):
        """Initialize the HTML wrapper."""
        pass

    def wrap_word(self, word: str, level: str, definition: Optional[str] = None, 
                 pinyin: Optional[str] = None, is_entity: bool = False) -> str:
        """
        Wrap a word in HTML with appropriate attributes.
        
        Args:
            word: Chinese word to wrap
            level: CEFR level of the word
            definition: Optional English definition
            pinyin: Optional pinyin pronunciation
            is_entity: Whether the word is a named entity
            
        Returns:
            HTML string with the word wrapped in a span tag
        """
        # Escape the word and any attributes to prevent XSS
        word = html.escape(word)
        attributes = [f'class="word-{level.lower()}"']
        
        if definition:
            attributes.append(f'data-definition="{html.escape(definition)}"')
        if pinyin:
            attributes.append(f'data-pinyin="{html.escape(pinyin)}"')
        if is_entity:
            attributes.append('data-entity="true"')
            
        return f'<span {" ".join(attributes)}>{word}</span>'

    def process_article(self, article: 'Article', words: List[str], 
                       word_levels: Dict[str, str], 
                       entity_definitions: Dict[str, Dict[str, str]], 
                       pinyin_dict: Optional[Dict[str, str]] = None) -> Dict[str, str]:
        """
        Process an article and its graded versions into HTML with appropriate wrapping.
        
        Args:
            article: Article object containing original and graded content
            words: List of segmented Chinese words from original content
            word_levels: Dictionary mapping words to their CEFR levels
            entity_definitions: Dictionary of entity types mapping to {word: definition}
            pinyin_dict: Optional dictionary mapping words to their pinyin
            
        Returns:
            Dictionary mapping content levels to their HTML-wrapped versions
        """
        def process_content(content: str, words: List[str]) -> str:
            """Helper function to process a single content version."""
            # Flatten entity definitions for easier lookup
            all_entities = {}
            for entity_type, entities in entity_definitions.items():
                all_entities.update(entities)
            
            # Process each word
            wrapped_words = []
            for word in words:
                # Get word attributes
                level = word_levels.get(word, 'unknown')
                definition = all_entities.get(word)
                pinyin = pinyin_dict.get(word) if pinyin_dict else None
                is_entity = word in all_entities
                
                # Wrap the word
                wrapped_word = self.wrap_word(
                    word=word,
                    level=level,
                    definition=definition,
                    pinyin=pinyin,
                    is_entity=is_entity
                )
                wrapped_words.append(wrapped_word)
            
            return ''.join(wrapped_words)
        
        # Process original content
        result = {
            'native': process_content(article.mandarin_content, words)
        }
        
        # Process graded versions if they exist
        if article.graded_content:
            for level, content in article.graded_content.items():
                result[level] = process_content(content, words)
                
        return result
