from typing import Dict, List, Optional, Set
import json
from backend.logger.logger import setup_logger
import opencc
import csv
from pathlib import Path
from pypinyin import pinyin, Style
from pypinyin.contrib.tone_convert import to_tone
from chinese_english_lookup import Dictionary

from backend.article.processed_article import (
    WordMetadataEntry,
    WordMetadata,
    VersionType,
    EntityType,
    GradeType
)
from .llm_client import LLMClient
from .prompts.metadata_completion_prompt import (
    get_metadata_completion_prompt,
    validate_metadata_completion_response
)

logger = setup_logger(__name__)

class MetadataGenerator:
    """
    A class to generate and complete word metadata based on segmented text versions.
    Includes integrated grading functionality.
    """
    def __init__(self):
        """Initialize the MetadataGenerator."""
        self.grade_dict = self._load_grade_dict()  # Will be populated as needed
        self.cedict = Dictionary()  # Initialize CC-CEDICT dictionary
        self.llm_client = None  # Will be initialized when needed
        self.s2t_converter = opencc.OpenCC('s2t.json')

    def _load_grade_dict(self) -> Dict[str, Dict[str, str]]:
        """
        Load the TOCFL grade dictionary from the CSV file.

        Returns:
            A dictionary mapping words (simplified) to their metadata:
            - grade: CEFR grade level
            - definitions: Word definitions
            - pinyin: Tonal pinyin
        """
        grade_dict = {}
        file_path = Path(__file__).parent.parent.parent / "assets" / "official_tocfl_list_processed.csv"
        
        try:
            with open(file_path, mode='r', encoding='utf-8') as csv_file:
                reader = csv.DictReader(csv_file)
                for row in reader:
                    simplified = row['simplified']
                    grade_dict[simplified] = {
                        "grade": row['cefr_level'],
                        "definitions": row['definitions'],
                        "pinyin": row['pinyin']
                    }
        except FileNotFoundError:
            logger.error(f"Grade dictionary file not found at {file_path}")
        except Exception as e:
            logger.error(f"Error loading grade dictionary: {e}")

        return grade_dict 

    def generate_from_segments(
        self,
        segments: List[str],
        version: VersionType,
        metadata: Optional[WordMetadata] = None
    ) -> WordMetadata:
        """
        Generate metadata from segmented text and update with version information.

        Args:
            segments: List of segmented words
            version: Version of the article being processed
            metadata: Existing metadata if any to update

        Returns:
            Updated WordMetadata
        """
        # If exisiting_metadata already exisits use it, if not initialize it
        if metadata is None:
          metadata = WordMetadata()
        
        # Process words to update versions and get new words
        unique_words = self._process_segmented_words(segments, version, metadata)

        # Process each unique word
        for word in unique_words:
            metadataEntry = self._generate_word_metadata(word, version) # metadata for single word
            metadata.add_or_update_metadata(metadataEntry)

        # Fill in missing data with LLM
        self._fill_missing_metadata(metadata)

        return metadata

    def _process_segmented_words(
        self,
        segments: List[str],
        version: VersionType,
        existing_metadata: WordMetadata
      ) -> Set[str]:
        """
        Process segmented words to update version info (if metadata already exists) and identify new words.
      
        Args:
            segments: List of segmented words.
            version: The version of the article being processed.
            existing_metadata: The existing metadata collection to update.
      
        Returns:
            Set of unique new words.
        """
        new_words = set()
      
        for word in segments:
            existing_meta = existing_metadata.get_metadata(word)
            if existing_meta:
                # Update version presence for existing word
                if version not in existing_meta.presence_in_versions:
                    existing_meta.presence_in_versions.append(version)
            else:
                # Track new word
                new_words.add(word)
      
        return new_words

    def _generate_word_metadata(self, word: str, version: VersionType) -> WordMetadataEntry:
        """Generate initial metadata for a single word."""
        # Get grade level
        grade = self._get_word_grade(word)

        # Try to get entry from dictionary
        word_entry = self.cedict.lookup(word)
        
        if word_entry and len(word_entry.definition_entries) > 0:
            # Get traditional form from dictionary
            traditional = word_entry.trad
            # Get first definition entry
            first_entry = word_entry.definition_entries[0]
            # Convert numbered pinyin to tonal
            pinyin_str = self._convert_to_tonal_pinyin(first_entry.pinyin)
            # Get definitions
            definition = '; '.join(first_entry.definitions)
        else:
            # Fallback to opencc for traditional if not in dictionary
            traditional = self.s2t_converter.convert(word)
            # Fallback to pypinyin for pinyin
            pinyin_result = pinyin(word, style=Style.TONE)
            pinyin_str = ' '.join([syl[0] for syl in pinyin_result])
            # No definition available
            definition = ""

        return WordMetadataEntry(
            simplified=word,
            traditional=traditional,
            grade=grade,
            definition=definition,
            pinyin=pinyin_str,
            entity_type=False,  # Will be updated by entity extractor if needed
            presence_in_versions=[version]
        )

    def _get_word_grade(self, word: str) -> GradeType:
        """
        Get the grade level for a word.
        
        First checks official grade dictionary, then falls back to LLM-generated grade
        if word isn't in dictionary.
        """
        # Check official grade dictionary first
        if word in self.grade_dict:
            grade = self.grade_dict[word]['grade']
            if grade and grade in GradeType.__args__:  # Ensure grade is valid and not "unknown"
                return grade

        # For now return unknown - LLM will fill this in later
        return "unknown"

    def _convert_to_tonal_pinyin(self, pinyin_str: str) -> str:
        """Convert numbered pinyin to tonal pinyin."""
        return to_tone(pinyin_str)

    def _fill_missing_metadata(self, metadata_collection: WordMetadata) -> None:
        """Fill in missing metadata fields using LLM."""
        # Collect words with missing data
        words_needing_completion = []
        for word, meta in metadata_collection.get_all_metadata().items():
            if not meta.definition or meta.grade == "unknown":
                words_needing_completion.append({
                    "word": word,
                    "current_metadata": {
                        "definition": meta.definition,
                        "grade": meta.grade
                    }
                })

        if not words_needing_completion:
            return

        try:
            # Get prompt for LLM
            prompt = get_metadata_completion_prompt(words_needing_completion)

            # Get response from LLM
            response = self.llm_client.make_request(
                prompt,
                validate_response=validate_metadata_completion_response
            )

            if not response:
                logger.error("No response from LLM after retries.")
                return

            # Update metadata with LLM responses
            completed_metadata = json.loads(response)
            for word_data in completed_metadata:
                word = word_data["word"]
                if meta := metadata_collection.get_metadata(word):
                    if not meta.definition and "definition" in word_data:
                        meta.definition = word_data["definition"]
                    if meta.grade == "unknown" and "grade" in word_data:
                        meta.grade = word_data["grade"]

        except Exception as e:
            logger.error(f"Error filling missing metadata: {e}")
