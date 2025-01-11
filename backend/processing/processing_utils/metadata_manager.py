from typing import Dict, List, Optional, Tuple
from ...article.processed_article import ProcessedArticle, WordMetadata, VersionType, EntityType, GradeType
import cedict_utils.cedict as cedict

class MetadataGenerator:
    """Generates comprehensive metadata for words in a processed article."""
    
    def __init__(self, cedict_path: str):
        """
        Initialize the metadata generator.
        
        Args:
            cedict_path: Path to the CC-CEDICT dictionary file
        """
        self.cedict = cedict.read_cedict(cedict_path)
    
    def _get_cedict_entry(self, word: str) -> Optional[Dict]:
        """
        Get CC-CEDICT entry for a word.
        
        Args:
            word: Word to look up (in simplified Chinese)
            
        Returns:
            Dictionary with traditional, pinyin, and definitions if found, None otherwise
        """
        entries = self.cedict.get(word, [])
        if not entries:
            return None
            
        # Use the first entry for now
        entry = entries[0]
        return {
            'traditional': entry.traditional,
            'pinyin': entry.pinyin,
            'definitions': entry.definitions
        }
    
    def generate_metadata(
        self,
        article: ProcessedArticle,
        entity_data: Dict[str, Tuple[str, str]],  # {word: (entity_type, definition)}
        word_grades: Dict[str, GradeType]  # {word: grade_level}
    ) -> None:
        """
        Generate and add metadata for all words in the article.
        
        Args:
            article: ProcessedArticle to generate metadata for
            entity_data: Dictionary mapping words to their entity type and definition
            word_grades: Dictionary mapping words to their CEFR-like grade levels
        """
        # Track which words appear in which versions
        word_versions: Dict[str, List[VersionType]] = {}
        
        # First pass: collect word presence across versions
        for version in ["native", "intermediate", "beginner"]:
            for word in article.get_version_content(version):
                if word not in word_versions:
                    word_versions[word] = []
                word_versions[word].append(version)
        
        # Second pass: generate metadata for each word
        for word, versions in word_versions.items():
            # Get entity data if available
            entity_type: EntityType = False
            definition = ""
            if word in entity_data:
                entity_type, definition = entity_data[word]
            
            # If not an entity, try to get definition from CC-CEDICT
            if not definition:
                cedict_entry = self._get_cedict_entry(word)
                if cedict_entry:
                    definition = "; ".join(cedict_entry.get('definitions', []))
                    traditional = cedict_entry.get('traditional', word)
                    pinyin = cedict_entry.get('pinyin', '')
                else:
                    # Fallback if word not found in CC-CEDICT
                    traditional = word
                    pinyin = ''
            
            # Add metadata to the article
            article.add_word_metadata(
                word=word,
                simplified=word,  # word is already simplified
                traditional=traditional,
                grade=word_grades.get(word, 'C2'),  # Default to highest level if not found
                definition=definition,
                pinyin=pinyin,
                entity_type=entity_type,
                versions=versions
            )
