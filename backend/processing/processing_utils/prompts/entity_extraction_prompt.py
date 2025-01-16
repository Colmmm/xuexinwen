from typing import Optional

def get_entity_extraction_prompt(mandarin_content: str, english_content: Optional[str] = None) -> str:
    """
    Generate a prompt for entity extraction from parallel Chinese and English texts.

    Args:
        mandarin_content: Chinese text content
        english_content: Optional English text content for context

    Returns:
        Formatted prompt string
    """
    english_section = f"\n\n### English Content:\n{english_content}" if english_content else ""

    return f"""
    Please analyze the following Chinese text and extract all relevant entities crucial for understanding the context of the text. Focus on identifying proper nouns, important terms, and named entities, including:

    - **People**: Names of individuals (e.g., authors, historical figures, public officials).
    - **Locations**: Geographic places (e.g., countries, cities, landmarks).
    - **Organizations**: Companies, institutions, governmental bodies, etc.
    - **Miscellaneous**: Important terms, concepts, or laws that do not fit the above categories.

    These entities should represent key concepts that enhance comprehension of the text's meaning and context.

    Return a JSON array where each object contains the following keys:

    - "simplified": The simplified Chinese representation of the entity.
    - "traditional": The traditional Chinese representation of the entity.
    - "grade": CEFR-like grade level (A0 to C2).
    - "definition": The English definition of the entity.
    - "pinyin": The phonetic pronunciation of the entity using tone marks.
    - "entity_type": One of "person", "location", "organization", "misc".

    Ensure that the output is a valid JSON array and nothing else. If a value is unknown, leave it empty. Include multi-word entities when relevant.

    ### Chinese Content:
    {mandarin_content}{english_section}
    """
