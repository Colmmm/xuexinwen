from typing import Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass
from article import Article
from word_metadata import WordMetadataCollection, WordMetadata, VersionType, EntityType, GradeType

class MetadataCompleter:
    """
    A class to complete word metadata based on segmented text versions.
    """
    def __init__(self, grade_dict: Dict[str, str], cedict: Dict[str, Dict]):
        self.grade_dict = grade_dict
        self.cedict = cedict

    @classmethod
    def from_segments(
        cls,
        segments: List[str],
        version: VersionType,
        existing_metadata: WordMetadataCollection
    ) -> WordMetadataCollection:
        """
        Generate a WordMetadataCollection from segmented text and a specific version.

        Args:
            segments: List of segmented words.
            version: The version of the article to which the segments belong (e.g., 'native', 'intermediate', 'beginner').
            existing_metadata: Existing WordMetadataCollection to update with new metadata.

        Returns:
            Updated WordMetadataCollection with completed metadata.
        """
		# 1) Sorting out unique new words, because if theres some words that already exist in the 
		# exisiting_metadata, we dont want to want to waste time reprocessing them so what we should do
		# is go through each of the words in the segments check if they are in exisiting_metadata, if
		# so, add the new versions and take them out of ones that need more processing
		
		# 2) grade the segments (I can reuse the grading code)
		# grader all needs to take into account that if its an artifact, it will have a grade already but 
		# it wont be official and instead a guess from LLM, but if the word exists in the dict, then we use that instead
		# as that will be more official and up to date
		word_levels = self.grader.tag_words(unique_words)  # this is a dict: {"你好": "A1", "世界": "A2"}
        # I think I should just bring the `update_word_metadata_from_grades` method from processed_article to here as well as grader. But then should I create my own wordmetadata class(?), not sure how to best handle it
        # I wonder if I should create a definite class word_metadata which is Dict[str, WordMetaData] in processed_article with useful methods so I can import them and use them here
        processed_article.update_word_metadata_from_grades(word_levels)

		# 3) Get traditional version (but function)
		import opencc
		converter = opencc.OpenCC('s2t.json')
		converter.convert('汉字')  # 漢字

		# 4) get pinyin
		from chinese_english_lookup import Dictionary # probably need to setup some dict object and init in __init__ 
		d = Dictionary()
		word_entry = d.lookup('牛油果')
		# I think I should use the chinese_english_lookup (cc_cdict) first in case the word is present then
		if len(word_entry.definition_entries)
			pinyin = word_entry.definition_entries[0].pinyin # 'niu2 you2 guo3'
			# now need to convert it into tonal form
			from pypinyin.contrib.tone_convert import to_normal, to_tone, to_initials, to_finals
			to_tone(pinyin) # need to figure out appropriate output
		else:
			# if not in dict then use this pinyin package straight (I want to use dict first because some zi have two pinyins but if its a part of a word then the dict definition probably correct)
			from pypinyin import pinyin, lazy_pinyin, Style
			pinyin('中心')  # or pinyin(['中心'])，参数值为列表时表示输入的是已分词后的数据
			# [['zhōng'], ['xīn']]

		# 5) Get the definitions
		word_entry.definition_entries[0].definitions
		#['avocado (Persea americana)']

		# 6) fill in missing data with LLM call
		# will neeed to iterate through all current and pre-exisiting metadata
		# (still need to figure out how I will manage the new processed metadata and old one)
		for wordmetadata in all_wordmetadata:
			if wordmetadata['grade'] == 'unknown' or '' or wordmetadata['definition'] == 'unknown' or '':
				metadata_w_missing_entries.append(wordmetadata)
		# get prompt for filling in missing metadata
		prompt = get_fill_missing_metadata_prompt(metadata_w_missing_entries)
		# we can define a validation function to assert the llm output and how we expect it to just be 
		# a list of dicts, basically List[wordMetadata]
		def validate_fillingMissingMetadata_response(response: str) -> bool:
			return
		try:
            # Get raw response from LLM with retry logic
            response = self.llm_client.make_request(prompt, validate_response=validate_fillingMissingMetadata_response)
            if not response:
                logger.error("No response from LLM after retries.")
                return {'beginner': '', 'intermediate': ''}

            # Parse the valid response
            simplified_versions = json.loads(response)
            return {
                'beginner': simplified_versions.get('beginner', ''),
                'intermediate': simplified_versions.get('intermediate', '')
            }

        except APIRequestError as e:
            logger.error(f"API request failed: {e}")
            return {'beginner': '', 'intermediate': ''}

        except ValidationError as e:
            logger.error(f"Response validation error: {e}")
            return {'beginner': '', 'intermediate': ''}

        except json.JSONDecodeError as e:
            logger.error("Failed to parse JSON response after validation.")
            return {'beginner': '', 'intermediate': ''}