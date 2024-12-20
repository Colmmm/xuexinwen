import jieba
import pandas as pd
import requests
import json
from collections import defaultdict, OrderedDict
import re
import os

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY") 
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

def load_tocfl_dictionary(tocfl_csv_path):
    """
    Load TOCFL dictionary and add words to Jieba.
    Returns a dictionary mapping both traditional and simplified characters to their level.
    """
    df = pd.read_csv(tocfl_csv_path)
    word_dict = {}
    
    for _, row in df.iterrows():
        # Map both traditional and simplified to the simplified form and level
        word_dict[row['traditional']] = {
            'level': row['cefr_level'],
            'simplified': row['simplified']
        }
        word_dict[row['simplified']] = {
            'level': row['cefr_level'],
            'simplified': row['simplified']
        }
        
        # Add both forms to Jieba
        jieba.add_word(row['traditional'], freq=1000)
        jieba.add_word(row['simplified'], freq=1000)
    
    return word_dict

def call_openrouter_api(zh_content, en_content):
    """
    Use OpenRouter API to extract keywords from title and content.
    Uses both Chinese and English versions to improve accuracy and provide definitions.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xuexinwen.com",
    }
    prompt = f"""
    Please analyze the following parallel Chinese and English texts and extract keywords, paying special attention to identifying ALL people mentioned. Return ONLY a valid JSON array with no additional text.

    ### Chinese Content:
    {zh_content}

    ### English Content:
    {en_content}

    ### Instructions:
    1. Extract all **relevant entities** from the text, with special focus on:
    - **Names of people** (IMPORTANT: Include ALL people mentioned, such as officials, experts, executives, etc.)
        * Look for both Chinese and English names
        * Include titles or roles when relevant (e.g., "斯坦福大学学者格雷厄姆·韦伯斯特" -> "Graham Webster, Stanford University scholar")
        * Don't miss any quoted or referenced individuals
    - **Places** (e.g., countries, cities, landmarks)
    - **Organizations** (e.g., companies, institutions, political bodies)
    - **Other important terms** (e.g., key technical terms, laws, unique concepts)

    2. Include **multi-word entities** when relevant (e.g., "美国公司", "反垄断法")
    3. Be thorough in identifying ALL named individuals in the text
    4. Use the following types for classification:
    - `"person"`: Names of people (be comprehensive!)
    - `"place"`: Geographical locations or places
    - `"organization"`: Names of companies, institutions, or organizations
    - `"other"`: Important terms or concepts not falling into the above categories

    ### Output Format:
    Return a JSON array where each object contains:
    - `"word"`: The entity in Chinese as it appears in the text
    - `"type"`: The classification type (`"person"`, `"place"`, `"organization"`, `"other"`)
    - `"english"`: The English translation/definition of the entity, including titles/roles for people
    Example:
    ```json
    [
        {{"word": "格雷厄姆·韦伯斯特", "type": "person", "english": "Graham Webster, Stanford University scholar"}},
        {{"word": "英伟达", "type": "organization", "english": "Nvidia"}},
        {{"word": "中国", "type": "place", "english": "China"}},
        {{"word": "反垄断法", "type": "other", "english": "Antitrust Law"}}
    ]
    ```
    """

    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        
        print("\nAPI Response:")
        print(response.json())
        
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        if content.rstrip().endswith(','):
            content = content.rstrip().rstrip(',') + ']'
        
        try:
            return json.loads(content)
        except json.JSONDecodeError as e:
            print(f"Initial JSON parsing failed: {e}")
            if content.count('[') > content.count(']'):
                content = content + ']'
            return json.loads(content)
            
    except requests.exceptions.RequestException as e:
        print(f"API request failed: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"JSON parsing failed: {e}")
        print(f"Raw content: {content}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def classify_unknown_words(unknown_words):
    """
    Use OpenRouter API to classify unknown words into CEFR levels.
    """
    if not unknown_words:
        return {}
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xue-xinwen.com",
    }
    
    words_str = ", ".join(unknown_words)
    prompt = f"""
        Classify the following Chinese words into CEFR levels: A0, A1, A2, B1, B2, C1, or C2 based on their complexity, frequency of use, and alignment with the CEFR level descriptions.

        ### CEFR Level Guidelines:
        - **A0 (Breakthrough Beginner)**: Basic greetings, numbers 1-10, very simple nouns and phrases for basic needs.
        - **A1 (Basic User - Breakthrough)**: 
        Can understand and use familiar, everyday expressions and very basic phrases (e.g., personal details, introductions, concrete needs).
        - **A2 (Basic User - Waystage)**: 
        Can understand frequently used expressions (e.g., family, shopping, employment) and communicate in simple, routine tasks.
        - **B1 (Independent User - Threshold)**: 
        Can understand the main points of clear, standard input on familiar topics (e.g., school, work, leisure) and produce simple connected text.
        - **B2 (Independent User - Vantage)**: 
        Can understand complex text on concrete and abstract topics, including technical discussions, and produce detailed explanations on topics.
        - **C1 (Proficient User - Advanced)**: 
        Can understand demanding texts, recognize implicit meaning, and use language fluently for academic, professional, and social purposes.
        - **C2 (Proficient User - Mastery)**: 
        Can understand virtually everything heard or read and express themselves fluently, precisely, and spontaneously, differentiating subtle shades of meaning.

        ### Input:
        Words: {words_str}

        ### Output:
        - Return ONLY a valid JSON object without explanations or additional text.
        - Each word should be assigned a CEFR level.

        ### JSON Format Example:
        {{
            "word1": "A1",
            "word2": "B2",
            "word3": "C1"
        }}
    """
    
    data = {
        "model": "openai/gpt-4o-mini",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.1
    }
    
    try:
        response = requests.post(OPENROUTER_URL, headers=headers, json=data)
        response.raise_for_status()
        
        print("\nClassification API Response:")
        print(response.json())
        
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        
        return json.loads(content)
    except Exception as e:
        print(f"Classification error: {e}")
        return {}

def clean_word(word):
    """Clean word by removing punctuation and whitespace."""
    word = word.strip()
    if re.match(r'^[\s\W]+$', word):
        return None
    return word

def create_ordered_dict():
    """Create an ordered dictionary with CEFR levels in correct order."""
    levels = ['A0', 'A1', 'A2', 'B1', 'B2', 'C1', 'C2', 'unknown']
    return OrderedDict((level, set()) for level in levels)

def process_article(zh_content, en_content, tocfl_csv_path):
    """
    Process article and categorize words by TOCFL level and entity type.
    Returns lists of simplified characters organized by category.
    Now uses both Chinese and English content for better entity detection and definitions.
    """
    # Initialize results
    result = {
        "words": create_ordered_dict(),
        "entities": {
            "names": {},
            "places": {},
            "organizations": {},
            "misc": {}
        }
    }
    
    # Load dictionary
    word_dict = load_tocfl_dictionary(tocfl_csv_path)
    
    # Process entities first using both Chinese and English content
    entities = call_openrouter_api(zh_content, en_content)
    type_mapping = {
        "person": "names",
        "place": "places",
        "organization": "organizations",
        "other": "misc"
    }
    
    # Add entities with their English definitions
    for entity in entities:
        word = entity["word"]
        entity_type = type_mapping[entity["type"]]
        english_def = entity.get("english", "")
        jieba.add_word(word, freq=1000)
        
        # Add simplified form of entity if it's in our dictionary
        word_info = word_dict.get(word)
        if word_info:
            if english_def:
                result["entities"][entity_type][word_info['simplified']] = english_def
        else:
            if english_def:
                result["entities"][entity_type][word] = english_def
    
    # Process full text
    words = jieba.cut(zh_content, cut_all=False)
    
    # Collect unknown words
    unknown_words = set()
    
    # Process each word
    for word in words:
        word = clean_word(word)
        if not word:
            continue
        
        # Get word info from dictionary
        word_info = word_dict.get(word)
        if word_info:
            level = word_info['level']
            result["words"][level].add(word_info['simplified'])
        else:
            # Add to unknown words set for later classification
            unknown_words.add(word)
    
    # Classify unknown words if any exist
    if unknown_words:
        classifications = classify_unknown_words(list(unknown_words))
        for word, level in classifications.items():
            result["words"][level].add(word)
            # Remove from unknown category if successfully classified
            if word in unknown_words:
                unknown_words.remove(word)
    
    # Add remaining unknown words to unknown category
    for word in unknown_words:
        result["words"]["unknown"].add(word)
    
    # Convert sets to sorted lists for words
    final_result = {
        "words": {
            level: sorted(list(words))
            for level, words in result["words"].items()
            if words  # Include empty levels to maintain order
        },
        "entities": {
            entity_type: definitions
            for entity_type, definitions in result["entities"].items()
            if definitions  # Only include non-empty entity types
        }
    }
    
    return final_result

# Example usage
if __name__ == "__main__":
    with open("test_article_zh.txt", 'r', encoding='utf-8') as file:
        zh_content = file.read()

    with open("test_article_en.txt", 'r', encoding='utf-8') as file:
        en_content = file.read()

    tocfl_csv_path = "official_tocfl_list_processed.csv"

    # Force Jieba to load user dictionary
    jieba.initialize()
    
    result = process_article(zh_content, en_content, tocfl_csv_path)
    print("\nProcessed Article Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
