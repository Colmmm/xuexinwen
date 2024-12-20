def get_entity_extraction_prompt(zh_content: str, en_content: str) -> str:
    """
    Generate prompt for entity extraction from parallel Chinese and English texts.
    
    Args:
        zh_content: Chinese text content
        en_content: English text content
        
    Returns:
        Formatted prompt string
    """
    return f"""
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
    """
