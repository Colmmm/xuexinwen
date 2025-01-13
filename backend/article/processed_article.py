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

    def update_word_metadata(self, entities: Dict[str, Dict[str, str]]) -> None:
        """
        Update word metadata.

        Args:
            entities: Dictionary of extracted entities where the key is the word
                      and the value is a dictionary containing metadata fields.
        """
        # Iterate through each entity and add metadata
        for word, metadata in entities.items():
            self.add_word_metadata(
                word=word,
                simplified=metadata.get("simplified", ""),
                traditional=metadata.get("traditional", ""),
                grade=metadata.get("grade", "unknown"),
                definition=metadata.get("definition", ""),
                pinyin=metadata.get("pinyin", ""),
                entity_type=metadata.get("entity_type", "misc"),
                versions=metadata.get("versions", [])  # Use provided versions
            )
            
    def update_word_metadata_from_grades(self, word_levels: Dict[str, GradeType]) -> None:
        """
        Update word metadata with CEFR levels from the Grader.

        Args:
            word_levels: Dictionary mapping words to their CEFR levels.
        """
        for word, grade in word_levels.items():
            if word in self.word_metadata:
                # Update the existing metadata entry with the new grade
                self.word_metadata[word].grade = grade
            else:
                # Add a new metadata entry if it doesn't exist
                self.add_word_metadata(
                    word=word,
                    simplified=word,
                    traditional=word,
                    grade=grade,
                    definition="",
                    pinyin="",
                    entity_type=False,
                    versions=["native"]
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
    
    def get_entities(self) -> List[Dict[str, str]]:
        """
        Extracts a list of entities from the word metadata.

        Returns:
            A list of dictionaries representing entities, each containing:
            - simplified: Simplified Chinese form of the word
            - traditional: Traditional Chinese form of the word
            - entity_type: Type of the entity (e.g., person, place, organization)
            - definition: English definition or description of the entity
        """
        entities = []
        for word, metadata in self.word_metadata.items():
            if metadata.get("entity_type") and metadata["entity_type"] != "false":
                entities.append({
                    "simplified": metadata.get("simplified", word),
                    "traditional": metadata.get("traditional", word),
                    "entity_type": metadata.get("entity_type"),
                    "definition": metadata.get("definition", "")
                })
        return entities

    def get_word_grading_lists(self) -> Dict[str, List[str]]:
        """
        Groups words by their CEFR levels.

        Returns:
            A dictionary where keys are CEFR levels (A0, A1, ..., C2, unknown) and
            values are lists of words at those levels.
        """
        gradings = {level: [] for level in ["A0", "A1", "A2", "B1", "B2", "C1", "C2", "unknown"]}
        for word, metadata in self.word_metadata.items():
            grade = metadata.get("grade", "unknown")
            gradings[grade].append(word)
        return gradings

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
