def get_word_classification_prompt(words_str: str) -> str:
    """
    Generate prompt for classifying Chinese words into CEFR levels.
    
    Args:
        words_str: Comma-separated string of Chinese words to classify
        
    Returns:
        Formatted prompt string
    """
    return f"""
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
        - Example format:
        {{
            "word1": "A1",
            "word2": "B2",
            "word3": "C1"
        }}
    """
