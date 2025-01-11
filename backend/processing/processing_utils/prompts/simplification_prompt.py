from typing import Dict

# CEFR level descriptions for article simplification
LEVEL_DESCRIPTIONS: Dict[str, str] = {
    'A1': """
        - Very basic vocabulary and simple sentences
        - Focus on everyday topics and concrete needs
        - Short, clear statements using common words
        - Basic grammatical structures only
        - High frequency vocabulary only
    """,
    
    'A2': """
        - Basic vocabulary and simple grammatical structures
        - Short, clear sentences about familiar topics
        - Common expressions and daily language
        - Simple connectors (and, but, because)
        - Present tense primarily, with some past tense
    """,
    
    'B1': """
        - Common vocabulary and straightforward expressions
        - Clear paragraph structure and logical flow
        - Main points clearly expressed
        - More varied sentence structures
        - Common idioms and expressions
    """,
    
    'B2': """
        - More varied vocabulary while maintaining clarity
        - Complex ideas explained in simpler terms
        - Clear structure with good paragraph organization
        - Natural flow with appropriate transitions
        - Technical terms explained when used
    """
}

def get_simplification_prompt(zh_content: str, en_content: str, target_level: str) -> str:
    """
    Generate prompt for article simplification to a target CEFR level.
    
    Args:
        zh_content: Original Chinese content
        en_content: Original English content (for context)
        target_level: Target CEFR level for simplification
        
    Returns:
        Formatted prompt string
    """
    level_desc = LEVEL_DESCRIPTIONS.get(target_level, "Simplified Chinese")
    
    return f"""
    Please simplify the following Chinese text to {target_level} level Chinese, while preserving the key information and maintaining natural flow. Use the English text as context to ensure accuracy.

    ### Target Level ({target_level}) Requirements:
    {level_desc}

    ### Guidelines:
    1. Maintain key information and main ideas
    2. Use vocabulary and grammar appropriate for {target_level} level
    3. Keep proper nouns and essential terminology (with explanations if needed)
    4. Break complex sentences into simpler ones
    5. Preserve logical connections between ideas
    6. Keep the text natural and readable
    7. Maintain the original meaning while simplifying expression
    8. Use appropriate connectors for the level
    9. Include explanatory phrases for difficult concepts when necessary

    ### Original Chinese:
    {zh_content}

    ### English Context (for reference):
    {en_content}

    Return ONLY the simplified Chinese text, without any explanations or additional text.
    The output should be a natural, flowing Chinese text that could be read independently.
    """

def get_multi_level_prompt(zh_content: str, en_content: str, levels: list) -> str:
    """
    Generate prompt for creating multiple versions at different CEFR levels.
    
    Args:
        zh_content: Original Chinese content
        en_content: Original English content
        levels: List of target CEFR levels
        
    Returns:
        Formatted prompt string
    """
    level_descriptions = "\n\n".join([
        f"### {level} Level Requirements:\n{LEVEL_DESCRIPTIONS.get(level, '')}"
        for level in levels
    ])
    
    return f"""
    Please create multiple versions of the following Chinese text, simplified to different CEFR levels while maintaining key information. Use the English text as context to ensure accuracy.

    {level_descriptions}

    ### General Guidelines:
    1. Create a separate version for each level
    2. Maintain key information and main ideas across all versions
    3. Adjust vocabulary and grammar complexity for each level
    4. Keep proper nouns and essential terminology
    5. Ensure natural flow in each version
    6. Preserve the logical structure of the content

    ### Original Chinese:
    {zh_content}

    ### English Context:
    {en_content}

    Return the simplified versions in JSON format:
    {{
        "A1": "A1 level text here",
        "A2": "A2 level text here",
        ...
    }}
    """
