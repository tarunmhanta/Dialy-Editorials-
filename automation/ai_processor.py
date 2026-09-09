"""
MBA EDITORIAL DAILY - GEMINI AI INTEGRATION MODULE
Uses the official Google Gemini SDK to transform raw article text into structured JSON.
Strictly respects API key privacy rules and environment variable extraction.
"""

import os
import json
import re
from typing import Dict, Any, Optional
from pathlib import Path

from config import (
    GEMINI_MODEL_NAME,
    GEMINI_API_KEY_ENV,
    PROMPT_FILE_PATH,
    MAX_AI_RETRIES
)
from logger import logger

try:
    from google import genai
    from google.genai import types
    SDK_AVAILABLE = True
except ImportError:
    SDK_AVAILABLE = False
    logger.warning("google-genai SDK not found. Install requirements via pip.")


class GeminiAIProcessor:
    """
    Interfaces securely with Google Gemini API to generate structured educational analysis.
    """

    def __init__(self):
        self.api_key = os.getenv(GEMINI_API_KEY_ENV)
        if not self.api_key:
            logger.error(
                f"SECURITY MANDATE VIOLATION: Environment variable '{GEMINI_API_KEY_ENV}' "
                "is missing or empty. Failing safely without exposing secrets."
            )
            raise ValueError("GEMINI_API_KEY environment variable is required.")

        if not SDK_AVAILABLE:
            raise RuntimeError("Google Gemini SDK ('google-genai') is not installed.")

        # Initialize Gemini Client using official Google SDK
        self.client = genai.Client(api_key=self.api_key)
        logger.info("Initialized Gemini AI Client successfully.")

    def _load_system_prompt(self) -> str:
        """Loads prompt template from prompts directory."""
        if not PROMPT_FILE_PATH.exists():
            raise FileNotFoundError(f"Prompt template file not found at {PROMPT_FILE_PATH}")
        
        with open(PROMPT_FILE_PATH, "r", encoding="utf-8") as f:
            return f.read()

    def _clean_raw_response(self, raw_text: str) -> str:
        """Removes accidental Markdown code block fences (e.g. ```json ... ```)."""
        text = raw_text.strip()
        # Regex to strip ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _validate_schema(self, data: Dict[str, Any]) -> bool:
        """
        Validates that generated JSON contains all mandatory schema keys.
        """
        required_root_keys = [
            "title", "source", "introduction", "summary",
            "mbaRelevance", "keyTakeaways", "terminologies", "discussionQuestion"
        ]
        for key in required_root_keys:
            if key not in data:
                logger.error(f"Schema Validation Failure: Missing root key '{key}'")
                return False

        summary_keys = ["overview", "keyArguments", "conclusion"]
        for skey in summary_keys:
            if skey not in data["summary"]:
                logger.error(f"Schema Validation Failure: Missing summary key '{skey}'")
                return False

        mba_keys = ["importance", "subjects", "managementConcepts"]
        for mkey in mba_keys:
            if mkey not in data["mbaRelevance"]:
                logger.error(f"Schema Validation Failure: Missing mbaRelevance key '{mkey}'")
                return False

        if not isinstance(data["terminologies"], list):
            logger.error("Schema Validation Failure: 'terminologies' must be a list.")
            return False

        return True

    def process_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Main processing method. Calls Gemini, handles response cleaning, schema validation, and controlled retries.
        """
        base_prompt = self._load_system_prompt()
        
        user_input = (
            f"SOURCE ARTICLE TITLE: {article['title']}\n"
            f"PUBLICATION DATE: {article['date']}\n"
            f"ORIGINAL URL: {article['url']}\n"
            f"AUTHOR: {article['author']}\n\n"
            f"FULL ARTICLE TEXT CONTENT:\n{article['content']}\n"
        )

        full_prompt = f"{base_prompt}\n\n{user_input}"

        for attempt in range(1, MAX_AI_RETRIES + 1):
            try:
                logger.info(f"Sending article to Gemini AI (Attempt {attempt}/{MAX_AI_RETRIES})...")
                
                response = self.client.models.generate_content(
                    model=GEMINI_MODEL_NAME,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        temperature=0.3
                    )
                )

                if not response or not response.text:
                    logger.warning("Empty response received from Gemini API.")
                    continue

                clean_text = self._clean_raw_response(response.text)
                
                # Parse JSON
                try:
                    json_data = json.loads(clean_text)
                except json.JSONDecodeError as je:
                    logger.warning(f"JSON Parse error on attempt {attempt}: {je}")
                    if attempt < MAX_AI_RETRIES:
                        # Append repair instruction for controlled retry
                        full_prompt += "\n\nCRITICAL FIX REQUIRED: Your previous response contained invalid JSON syntax. Return ONLY raw valid JSON following the schema."
                    continue

                # Validate Schema
                if self._validate_schema(json_data):
                    logger.info("Successfully validated Gemini AI structured JSON output.")
                    return json_data
                else:
                    logger.warning(f"Schema validation failed on attempt {attempt}.")
                    if attempt < MAX_AI_RETRIES:
                        full_prompt += "\n\nCRITICAL FIX REQUIRED: Ensure all required schema fields (introduction, summary, mbaRelevance, terminologies, discussionQuestion) are present."

            except Exception as e:
                logger.error(f"Error invoking Gemini API on attempt {attempt}: {e}")

        logger.error(f"Failed to generate valid structured JSON after {MAX_AI_RETRIES} attempts.")
        return None
