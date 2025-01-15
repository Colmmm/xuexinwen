from typing import List, Dict

def get_metadata_completion_prompt(words_with_missing_data: List[Dict]) -> str:
    """
    Generate a prompt for completing missing metadata for Chinese words.
    
    Args:
        words_with_missing_data: List of dictionaries containing words and their current metadata
            Each dict has format:
            {
                "word": str,  # The Chinese word
                "current_metadata": {
                    "definition": str or None,  # Current definition if any
                    "grade": str or None,  # Current CEFR grade if any
                }
            }
    
    Returns:
        Formatted prompt string
    """
    words_str = "\n".join([
        f"- {word['word']}: Current definition: '{word['current_metadata']['definition']}', "
        f"Current grade: '{word['current_metadata']['grade']}'"
        for word in words_with_missing_data
    ])

    return f"""
    Please complete the missing metadata for the following Chinese words. For each word:
    1. If definition is missing or empty, provide an accurate English definition
    2. If grade is missing or 'unknown', classify according to CEFR levels (A1-C2)

    ### CEFR Level Guidelines:
    - A1 (Basic User - Breakthrough): Basic vocabulary for everyday needs
    - A2 (Basic User - Waystage): Common expressions, routine tasks
    - B1 (Independent User - Threshold): Main points of familiar topics
    - B2 (Independent User - Vantage): Complex text, technical discussions
    - C1 (Proficient User - Advanced): Demanding texts, implicit meaning
    - C2 (Proficient User - Mastery): Virtually everything, subtle meanings

    ### Words Needing Completion:
    {words_str}

    ### Response Format:
    Return ONLY a JSON array of objects with this structure:
    [
        {{
            "word": "你好",  # Original Chinese word
            "definition": "hello",  # Only if current definition is missing/empty
            "grade": "A1"  # Only if current grade is missing/unknown
        }}
    ]

    ### Important:
    - Include ONLY words that need completion
    - For each word, include ONLY fields that need to be filled
    - Ensure definitions are clear and accurate
    - Grade should reflect word complexity and usage frequency
    """

def validate_metadata_completion_response(response: str) -> bool:
    """
    Validate that the LLM response matches the expected format.
    
    Args:
        response: The LLM response string (should be JSON)
        
    Returns:
        bool: True if response is valid, False otherwise
    """
    try:
        import json
        data = json.loads(response)
        
        if not isinstance(data, list):
            return False
            
        valid_grades = {"A1", "A2", "B1", "B2", "C1", "C2"}
        
        for item in data:
            # Check basic structure
            if not isinstance(item, dict):
                return False
            if "word" not in item:
                return False
                
            # Validate optional fields if present
            if "definition" in item and not isinstance(item["definition"], str):
                return False
            if "grade" in item and item["grade"] not in valid_grades:
                return False
                
        return True
        
    except json.JSONDecodeError:
        return False
