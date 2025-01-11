from dataclasses import dataclass
from typing import Dict, List, Union, Literal, Optional
from datetime import datetime
from .article import Article

# Type for version names
VersionType = Literal["native", "intermediate", "beginner"]

# Type for entity types
EntityType = Literal["person", "location", "organization", "misc", False]

# Type for CEFR-like grades
GradeType = Literal["A0", "A1", "A2", "B1", "B2", "C1", "C2"]

@dataclass
class WordMetadata:
    """Metadata for a single word/phrase in the article."""
    simplified: str
    traditional: str
    grade: GradeType
    definition: str
    pinyin: str
    entity_type: EntityType
    presence_in_versions: List[VersionType]

@dataclass
class ProcessedArticle(Article):
    """
    Represents a processed article that extends the base Article class with
    segmented content for different proficiency levels and comprehensive word metadata.
    """
    # Dictionary containing segmented content for each version (native, intermediate, beginner)
    segmented_content: Dict[VersionType, List[str]]
    
    # Dictionary mapping words to their metadata
    word_metadata: Dict[str, WordMetadata]
    
    def __init__(
        self,
        article_id: str,
        url: str,
        date: datetime,
        source: str,
        authors: List[str],
        mandarin_title: str,
        english_title: str,
        mandarin_content: str,
        english_content: str,
        mandarin_section_indices: List[tuple[int, int]],
        english_section_indices: List[tuple[int, int]],
        image_url: Optional[str] = None,
        graded_content: Optional[Dict[str, str]] = None,
        metadata: Optional[Dict] = None
    ):
        """Initialize ProcessedArticle with base Article attributes plus processing-specific fields."""
        super().__init__(
            article_id=article_id,
            url=url,
            date=date,
            source=source,
            authors=authors,
            mandarin_title=mandarin_title,
            english_title=english_title,
            mandarin_content=mandarin_content,
            english_content=english_content,
            mandarin_section_indices=mandarin_section_indices,
            english_section_indices=english_section_indices,
            image_url=image_url,
            graded_content=graded_content,
            metadata=metadata
        )
        self.segmented_content = {
            "native": [],
            "intermediate": [],
            "beginner": []
        }
        self.word_metadata = {}
    
    def add_word_metadata(
        self,
        word: str,
        simplified: str,
        traditional: str,
        grade: GradeType,
        definition: str,
        pinyin: str,
        entity_type: EntityType,
        versions: List[VersionType]
    ) -> None:
        """
        Add metadata for a word/phrase.
        
        Args:
            word: The word/phrase to add metadata for (should be simplified for now)
            simplified: Simplified Chinese version
            traditional: Traditional Chinese version
            grade: CEFR-like grade level
            definition: English definition
            pinyin: Phonetic pronunciation with tone marks
            entity_type: Type of named entity or False
            versions: List of versions where this word appears
        """
        self.word_metadata[word] = WordMetadata(
            simplified=simplified,
            traditional=traditional,
            grade=grade,
            definition=definition,
            pinyin=pinyin,
            entity_type=entity_type,
            presence_in_versions=versions
        )
    
    def set_version_content(self, version: VersionType, content: List[str]) -> None:
        """
        Set the segmented content for a specific version.
        
        Args:
            version: The version to set content for
            content: List of segmented words/phrases
        """
        self.segmented_content[version] = content
    
    def get_version_content(self, version: VersionType) -> List[str]:
        """
        Get the segmented content for a specific version.
        
        Args:
            version: The version to get content for
            
        Returns:
            List of segmented words/phrases for the specified version
        """
        return self.segmented_content[version]
    
    def get_word_metadata(self, word: str) -> Union[WordMetadata, None]:
        """
        Get metadata for a specific word/phrase.
        
        Args:
            word: The word/phrase to get metadata for
            
        Returns:
            WordMetadata object if word exists, None otherwise
        """
        return self.word_metadata.get(word)
    
    def to_dict(self) -> Dict:
        """Convert ProcessedArticle to dictionary representation, including base Article fields."""
        base_dict = super().to_dict()
        return {
            **base_dict,
            'segmented_content': self.segmented_content,
            'word_metadata': {
                word: {
                    'simplified': meta.simplified,
                    'traditional': meta.traditional,
                    'grade': meta.grade,
                    'definition': meta.definition,
                    'pinyin': meta.pinyin,
                    'entity_type': meta.entity_type,
                    'presence_in_versions': meta.presence_in_versions
                }
                for word, meta in self.word_metadata.items()
            }
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'ProcessedArticle':
        """Create ProcessedArticle instance from dictionary representation."""
        # Create instance with base Article fields
        instance = super().from_dict(data)
        
        # Add ProcessedArticle-specific fields
        instance.segmented_content = data.get('segmented_content', {
            "native": [],
            "intermediate": [],
            "beginner": []
        })
        
        # Convert word metadata dict back to WordMetadata objects
        instance.word_metadata = {
            word: WordMetadata(
                simplified=meta['simplified'],
                traditional=meta['traditional'],
                grade=meta['grade'],
                definition=meta['definition'],
                pinyin=meta['pinyin'],
                entity_type=meta['entity_type'],
                presence_in_versions=meta['presence_in_versions']
            )
            for word, meta in data.get('word_metadata', {}).items()
        }
        
        return instance
