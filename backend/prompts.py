
def get_text_prompt(article):

    return (
    """
    You will be provided with a news article written in Traditional Chinese (delimited with XML tags). Your task is to simplify the language in the article for learners of Traditional Chinese.

    1. Simplify the title and text while aiming to use the top 500 most common Traditional Chinese characters. You can use essential story-related words that are not within the top 500 characters.
    2. **IMPORTANT: For names (people, groups, companies, places) please use English versions. Do not translate names into Chinese.**

    Please use XML tags for your output using the following format:
    <root>
    <title>TITLE</title>
    <text>TEXT</text>
    </root>

    Here is the news article for simplification:

    """ 
    +
    f"<title>{article.title}</title>"
    +
    "/n/n"
    +
    f"<text>{article.text}</text>"
    )

def get_dict_prompt(article):

    return (
    """
    You will be provided with a news article written in Traditional Chinese (delimited with XML tags). 
    Your task is to create a dictionary with translations, Pinyin, and English meanings for uncommon words and phrases used in the
    title and text that learners of Chinese who know roughly 500 characters would find helpful.

    Use the following format:

    <root>
    <dictionary>
    <entry>
        <word>WORD1</word>
        <pinyin>PINYIN1</pinyin>
        <description>DESCRIPTION1</description>
    </entry>
    <entry>
        <word>WORD2</word>
        <pinyin>PINYIN2</pinyin>
        <description>DESCRIPTION2</description>
    </entry>
    <!-- Include more entries as necessary -->
    </dictionary>
    </root>

    Here is the news article:
    """
    +
    f"<title>{article.simplified_title}</title>"
    +
    "/n/n"
    +
    f"<text>{article.simplified_text}</text>"
    )