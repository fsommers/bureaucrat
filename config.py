# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from dotenv import load_dotenv

load_dotenv()

# AI Provider Configuration
AI_PROVIDER = os.getenv('AI_PROVIDER', 'gemini')  # Default to Gemini

# Gemini Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-2.5-flash')

# Hugging Face Configuration
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')
HUGGINGFACE_MODEL = os.getenv('HUGGINGFACE_MODEL', 'meta-llama/Llama-3.2-11B-Vision-Instruct')
HUGGINGFACE_ENDPOINT = os.getenv('HUGGINGFACE_ENDPOINT')  # Optional custom endpoint

# General AI Configuration
TEMPERATURE = float(os.getenv('TEMPERATURE', '0.7'))
MAX_TOKENS = int(os.getenv('MAX_TOKENS', '8192'))

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