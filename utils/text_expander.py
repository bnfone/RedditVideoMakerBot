import re

def expand_abbreviations(text: str) -> str:
    """
    Expands common abbreviations and measurements in the provided text for improved TTS pronunciation.

    The function performs the following case-insensitive replacements:
      - 'etc' or 'etc.'          -> 'etcetera'
      - 'pls'                   -> 'please'
      - 'plz'                   -> 'please'
      - 'ppl'                   -> 'people'
      - 'BF'                    -> 'boyfriend'
      - 'GF'                    -> 'girlfriend'
      - 'ik'                    -> 'I know'
      - ':3'                    -> 'nyah'
      - 'idk'                   -> "i don't know"
      - 'wtf'                   -> "what the fuck"
      - 'omfg'                  -> "oh my fucking god"
      - 'tf'                    -> "the fuck"
      - 'TwT'                   -> '' (empty string)
      - 'qwq'                   -> '' (empty string)
      - 'btw'                   -> 'by the way'
      - '<3'                    -> '' (empty string)
      - 'nsfw'                  -> 'not safe for work'
      - 'sfw'                   -> 'safe for work'
      - 'kg'                    -> 'kilograms'
      - 'lbs'                   -> 'punds'
      - 'afaik'                 -> 'as far as I know'
      - 'brb'                   -> 'be right back'

    Additionally, it converts height measurements of the form 6'2 into "6 feet 2 inches"
    (keeping the digits unchanged).

    Args:
        text (str): The original text.

    Returns:
        str: The text with abbreviations and measurements expanded.
    """
    # Define simple abbreviation patterns and their replacements
    simple_replacements = {
        r'\betc\.?\b': 'etcetera',
        r'\bpls\b': 'please',
        r'\bplz\b': 'please',
        r'\bppl\b': 'people',
        r'\bBF\b': 'boyfriend',
        r'\bGF\b': 'girlfriend',
        r'\bik\b': 'I know',
        r':3': 'nyah',
        r'\bidk\b': "i don't know",
        r'\bwtf\b': "what the fuck",
        r'\bomfg\b': "oh my fucking god",
        r'\btf\b': "the fuck",
        r'\bTwT\b': '',
        r'\bqwq\b': '',
        r'\bbtw\b': 'by the way',
        r'<3': '',
        r'\bnsfw\b': 'not safe for work',
        r'\bsfw\b': 'safe for work',
        r'\bkg\b': 'kilograms',
        r'\blbs\b': 'punds',
        r'\bafaik\b': 'as far as I know',
        r'\bbrb\b': 'be right back',
        r'\babt\b': 'about',
        r'\bsmh\b': 'shaking my head',
        r'\bfr\b': 'for real',
        r'\bsmth\b': 'something',
        r'\bthx\b': 'thanks',
        r'\birl\b': 'in real life',
        r'\bomg\b': 'oh my god',
        r'\bwtbs\b': 'what the big surprise',
        r'\btysm\b': 'thank you so much',
        r'\bty\b': 'thank you',
        r'\blmao\b': 'laughing my ass off',
        r'\btbf\b': 'to be fair',
        r'\btbh\b': 'to be honest',
        r'\brn\b': 'right now',
        r'\btifu\b': 'today i fucked up',
        r'\btl;dr\b': 'to long dont read',
        r'\btldr\b': 'to long dont read',
        r'\baita\b': 'am i the asshole'
    }

    # Perform simple case-insensitive replacements
    for pattern, replacement in simple_replacements.items():
        text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

    # Expand height measurements, e.g. "6'2" -> "6 feet 2 inches"
    def height_repl(match):
        feet = match.group(1)
        inches = match.group(2)
        return f"{feet} feet {inches} inches"

    text = re.sub(r"\b(\d+)'(\d+)\b", height_repl, text)

    return text
