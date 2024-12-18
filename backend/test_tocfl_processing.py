import jieba
import pandas as pd
import requests
import json
from collections import defaultdict, OrderedDict
import re
import os

# OpenRouter API configuration
OPENROUTER_API_KEY = os.environ.get('OPENROUTER_API_KEY')
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

def process_with_llm(segmented_text):
    """
    Process Jieba-segmented text with LLM to identify entities and fix segmentation.
    Returns entities and corrected segmentation.
    """
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xuexinwen.com",
    }
    
    prompt = f"""
    Analyze the following Chinese text that has been segmented by Jieba. Your task is to:
    1. Identify entities (people, places, organizations)
    2. Fix any incorrect word boundaries
    3. Return both the entities and corrected segmentation

    Segmented text: {segmented_text}

    Return a JSON object with two fields:
    1. 'entities': Array of objects with 'word' and 'type' fields
    2. 'corrections': Array of objects with 'original' (incorrectly segmented) and 'corrected' (proper segmentation) fields

    Example format:
    {{
        "entities": [
            {{"word": "英伟达", "type": "organization"}},
            {{"word": "中国", "type": "place"}}
        ],
        "corrections": [
            {{"original": "英 伟 达", "corrected": "英伟达"}},
            {{"original": "中 国", "corrected": "中国"}}
        ]
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
        
        print("\nLLM Processing Response:")
        print(response.json())
        
        content = response.json()["choices"][0]["message"]["content"]
        content = content.strip()
        if content.startswith('```json'):
            content = content[7:]
        if content.endswith('```'):
            content = content[:-3]
        content = content.strip()
        
        return json.loads(content)
    except Exception as e:
        print(f"LLM processing error: {e}")
        return {"entities": [], "corrections": []}

def classify_unknown_words(unknown_words):
    """
    Use OpenRouter API to classify unknown words into CEFR levels.
    """
    if not unknown_words:
        return {}
        
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://xuexinwen.com",
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

def process_article(title, content, tocfl_csv_path):
    """
    Process article and categorize words by TOCFL level and entity type.
    Returns lists of simplified characters organized by category.
    """
    # Initialize results with ordered dictionaries
    result = {
        "words": create_ordered_dict(),
        "entities": defaultdict(set)
    }
    
    # Load dictionary
    word_dict = load_tocfl_dictionary(tocfl_csv_path)
    
    # Step 1: Initial Jieba segmentation
    full_text = f"{title} {content}"
    initial_segments = list(jieba.cut(full_text))
    segmented_text = " ".join(initial_segments)
    
    # Step 2: Process with LLM to identify entities and fix segmentation
    llm_result = process_with_llm(segmented_text)
    
    # Step 3: Add entities to Jieba dictionary and result
    entity_types = {
        "person": "names",
        "place": "places",
        "organization": "organizations",
        "other": "misc"
    }
    
    for entity in llm_result.get("entities", []):
        word = entity["word"]
        entity_type = entity_types[entity["type"]]
        # Add to Jieba dictionary for future use
        jieba.add_word(word, freq=1000)
        # Add to results
        word_info = word_dict.get(word)
        if word_info:
            result["entities"][entity_type].add(word_info['simplified'])
        else:
            result["entities"][entity_type].add(word)
    
    # Step 4: Apply corrections to segmentation
    corrected_segments = initial_segments.copy()
    for correction in llm_result.get("corrections", []):
        original = correction["original"].split()
        corrected = correction["corrected"]
        # Find and replace the incorrect segmentation
        for i in range(len(corrected_segments)):
            if i + len(original) <= len(corrected_segments):
                if corrected_segments[i:i+len(original)] == original:
                    corrected_segments[i:i+len(original)] = [corrected]
    
    # Step 5: Process words and classify unknowns
    unknown_words = set()
    
    for word in corrected_segments:
        word = clean_word(word)
        if not word:
            continue
        
        word_info = word_dict.get(word)
        if word_info:
            level = word_info['level']
            result["words"][level].add(word_info['simplified'])
        else:
            unknown_words.add(word)
    
    # Classify unknown words
    if unknown_words:
        classifications = classify_unknown_words(list(unknown_words))
        for word, level in classifications.items():
            result["words"][level].add(word)
            if word in unknown_words:
                unknown_words.remove(word)
    
    # Add remaining unknown words
    for word in unknown_words:
        result["words"]["unknown"].add(word)
    
    # Convert sets to sorted lists
    final_result = {
        "words": {
            level: sorted(list(words))
            for level, words in result["words"].items()
            if words
        },
        "entities": {
            entity_type: sorted(list(entities))
            for entity_type, entities in result["entities"].items()
            if entities
        }
    }
    
    return final_result

# Example usage
if __name__ == "__main__":
    with open("test_article.txt", 'r', encoding='utf-8') as file:
        content = file.read()
        # Extract title (first line) and content (rest)
        lines = content.strip().split('\n', 1)
        title = lines[0].strip()
        content = lines[1].strip() if len(lines) > 1 else ""

    tocfl_csv_path = "official_tocfl_list_processed.csv"

    # Force Jieba to load user dictionary
    jieba.initialize()
    
    result = process_article(title, content, tocfl_csv_path)
    print("\nProcessed Article Result:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
