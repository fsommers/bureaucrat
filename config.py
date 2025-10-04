import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

# Default settings
DEFAULT_OUTPUT_DIR = 'output'
DEFAULT_DOCUMENT_COUNT = 10

LANGUAGE_CODES = {
    'en': 'English/US context',
    'th': 'Thai context',
    'es': 'Spanish context',
    'fr': 'French context',
    'de': 'German context',
    'it': 'Italian context',
    'pt': 'Portuguese context',
    'ru': 'Russian context',
    'ja': 'Japanese context',
    'ko': 'Korean context',
    'zh': 'Chinese context',
    'ar': 'Arabic context',
    'hi': 'Hindi context',
    'nl': 'Dutch context',
    'sv': 'Swedish context',
    'no': 'Norwegian context',
    'da': 'Danish context',
    'fi': 'Finnish context',
    'pl': 'Polish context',
    'tr': 'Turkish context',
    'he': 'Hebrew context',
    'cs': 'Czech context',
    'hu': 'Hungarian context',
    'ro': 'Romanian context',
    'bg': 'Bulgarian context',
    'hr': 'Croatian context',
    'sk': 'Slovak context',
    'sl': 'Slovenian context',
    'et': 'Estonian context',
    'lv': 'Latvian context',
    'lt': 'Lithuanian context',
    'uk': 'Ukrainian context',
    'vi': 'Vietnamese context',
    'id': 'Indonesian context',
    'ms': 'Malay context',
    'tl': 'Filipino context',
    'bn': 'Bengali context',
    'ta': 'Tamil context',
    'te': 'Telugu context',
    'ml': 'Malayalam context',
    'kn': 'Kannada context',
    'gu': 'Gujarati context',
    'pa': 'Punjabi context',
    'ur': 'Urdu context',
    'fa': 'Persian context'
}

SUPPORTED_LANGUAGES = list(LANGUAGE_CODES.keys())

# US Letter page dimensions in CSS
PAGE_WIDTH = '8.5in'
PAGE_HEIGHT = '11in'
PAGE_MARGIN = '1in'