from typing import List, Dict, Optional

# CEFR level descriptions for article simplification
LEVEL_DESCRIPTIONS: Dict[str, str] = {
    'beginner': """
        - Based on CEFR levels A1 to A2 (Common European Framework of Reference for Languages)
        - Basic vocabulary and simple grammatical structures
        - Short, clear sentences about familiar topics
        - Common expressions and daily language
        - Simple connectors (and, but, because)
        - Present tense primarily, with some past tense
        - Aim to use mostly A1-A2 level words, with a few B1 words for variety
        - Entities needed for context should be included
        - Target length: approximately one-quarter of the original content
    """,

    'intermediate': """
        - Based on CEFR levels B1 to B2 (Common European Framework of Reference for Languages)
        - Common vocabulary and straightforward expressions
        - Clear paragraph structure and logical flow
        - Main points clearly expressed
        - More varied sentence structures
        - Common idioms and expressions
        - Aim to use mostly B1-B2 level words
        - Entities needed for context should be included
        - Target length: approximately half of the original content
    """
}

def get_simplification_prompt(
    mandarin_content: str,
    mandarin_title: str,
    entities: List[Dict[str, str]],
    word_grading_lists: Dict[str, List[str]],
    english_content: Optional[str] = None,
    english_title: Optional[str] = None
) -> str:
    """
    Generate a prompt for simplifying an article to beginner and intermediate levels.

    Args:
        mandarin_content: Original Chinese content of the article.
        mandarin_title: Title of the article in Mandarin.
        english_content: Optional English version of the content (for context).
        english_title: Optional English version of the title (for context).
        entities: List of entities extracted from the article.
        word_grading_lists: Dictionary grouping words by their CEFR levels.

    Returns:
        A formatted prompt string to guide the LLM.
    """
    entity_list = "\n".join(
        f"- {entity['simplified']} ({entity['traditional']}): {entity['entity_type']} - {entity['definition']}"
        for entity in entities
    )

    graded_words = "\n".join(
        f"{level}: {', '.join(words)}"
        for level, words in word_grading_lists.items() if words
    )

    english_context = f"\n### Context (English):\n{english_content}" if english_content else ""
    english_title_section = f"- English Title: {english_title}\n" if english_title else ""

    # Calculate original length and target lengths for beginner and intermediate
    original_length = len(mandarin_content)
    beginner_target_length = original_length // 4
    intermediate_target_length = original_length // 2

    return f"""
    Please simplify the following article to two levels: beginner and intermediate. Use the English content and title for context to ensure accuracy where available.

    ### Article Details:
    - Mandarin Title: {mandarin_title}
    {english_title_section}

    ### Original Content (Mandarin):
    {mandarin_content}

    {english_context}

    ### Entities:
    {entity_list}

    ### Word Grading Lists:
    {graded_words}

    ### Simplification Requirements:
    BEGINNER Level:
    Target length: approximately {beginner_target_length} characters
    {LEVEL_DESCRIPTIONS['beginner']}

    INTERMEDIATE Level:
    Target length: approximately {intermediate_target_length} characters
    {LEVEL_DESCRIPTIONS['intermediate']}

    ### IMPORTANT:
    - The output MUST be in JSON format exactly as specified below.
    - Do NOT include any additional text, explanations, or commentary.

    Return the simplified versions as a JSON object with the following format:
    {{
        "beginner": "Simplified content for beginner level",
        "intermediate": "Simplified content for intermediate level"
    }}
    """
