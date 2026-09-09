"""
MBA EDITORIAL DAILY - CENTRAL CONFIGURATION
Contains paths, HTTP constants, Gemini settings, and validation rules.
"""

import os
from pathlib import Path

# Base Paths (Relative to repository root)
BASE_DIR = Path(__file__).resolve().parent.parent
AUTOMATION_DIR = BASE_DIR / "automation"
DATA_DIR = BASE_DIR / "data" / "editorials"
INDEX_JSON_PATH = DATA_DIR / "index.json"
GLOSSARY_JSON_PATH = BASE_DIR / "data" / "glossary.json"
PROMPT_FILE_PATH = AUTOMATION_DIR / "prompts" / "editorial_prompt.txt"

# Target Editorial Source Settings (The Indian Express)
INDIAN_EXPRESS_EDITORIAL_URL = "https://indianexpress.com/section/opinion/editorials/"
INDIAN_EXPRESS_RSS_URL = "https://indianexpress.com/section/opinion/editorials/feed/"

# HTTP Request Configurations
HTTP_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}
HTTP_TIMEOUT_SECONDS = 20
HTTP_MAX_RETRIES = 3

# Article Extraction Quality Thresholds
MIN_ARTICLE_CHAR_LENGTH = 400

# Gemini AI Settings
GEMINI_MODEL_NAME = "gemini-2.5-flash"
MAX_AI_RETRIES = 2

# Security Environment Variable Name
GEMINI_API_KEY_ENV = "GEMINI_API_KEY"
