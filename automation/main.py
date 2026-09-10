"""
MBA EDITORIAL DAILY - MAIN AUTOMATION PIPELINE
Orchestrates editorial discovery, duplicate checking, extraction, Gemini AI analysis, and JSON database updates.
"""

import sys
import os
from typing import Optional

# Ensure automation directory is in Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from logger import logger
from scraper import EditorialScraper
from duplicate_checker import DuplicateChecker
from article_extractor import ArticleExtractor
from content_cleaner import ContentCleaner
from ai_processor import GeminiAIProcessor
from json_manager import JSONManager

def run_pipeline() -> bool:
    """
    Executes the complete daily editorial processing workflow.
    Returns True if a new editorial was successfully processed and saved, False otherwise.
    """
    logger.info("==================================================")
    logger.info("STARTING DAILY EDITORIAL AUTOMATION PIPELINE")
    logger.info("==================================================")

    # Step 1: Validate Environment Variables
    if not os.getenv("GEMINI_API_KEY"):
        logger.error("MANDATORY FAILURE: GEMINI_API_KEY environment variable is missing.")
        sys.exit(1)

    # Step 2: Initialize Discovery Scraper & Duplicate Checker
    scraper = EditorialScraper()
    duplicate_checker = DuplicateChecker()

    logger.info("Step 1/6: Discovering recent Indian Express editorial candidates...")
    candidates = scraper.get_latest_editorial_candidates()

    if not candidates:
        logger.warning("No candidate editorials discovered from source. Exiting pipeline safely.")
        return False

    logger.info(f"Discovered {len(candidates)} candidate editorials.")

    # Step 3: Filter Out Duplicates
    target_candidate: Optional[dict] = None

    for candidate in candidates:
        url = candidate.get("url", "")
        title = candidate.get("title", "")
        
        if not duplicate_checker.is_duplicate(url, title):
            target_candidate = candidate
            break

    if not target_candidate:
        logger.info("All discovered editorials have already been processed. No new articles to add.")
        return False

    logger.info(f"Selected new editorial for processing: '{target_candidate['title']}' ({target_candidate['url']})")

    # Step 4: Extract and Clean Article Body
    logger.info("Step 2/6: Extracting article content...")
    extractor = ArticleExtractor()
    article_data = extractor.extract_article(
        url=target_candidate["url"],
        fallback_title=target_candidate["title"]
    )

    if not article_data:
        logger.error("Failed to extract valid article content. Aborting pipeline without corrupting data.")
        sys.exit(1)

    logger.info("Step 3/6: Cleaning content and stripping boilerplate noise...")
    cleaned_text = ContentCleaner.clean(article_data["content"])
    article_data["content"] = cleaned_text

    # Step 5: Send to Gemini AI
    logger.info("Step 4/6: Processing article with Google Gemini AI...")
    try:
        ai_processor = GeminiAIProcessor()
        ai_output = ai_processor.process_article(article_data)
    except Exception as e:
        logger.error(f"Error during Gemini AI invocation: {e}")
        sys.exit(1)

    if not ai_output:
        logger.error("Gemini AI failed to produce valid schema-compliant JSON. Aborting pipeline.")
        sys.exit(1)

    # Step 6: Save Editorial JSON, Update index.json & glossary.json
    logger.info("Step 5/6: Writing editorial JSON database records...")
    json_manager = JSONManager()
    success = json_manager.save_editorial(ai_output, article_data["date"])

    if success:
        logger.info("==================================================")
        logger.info("SUCCESS: DAILY EDITORIAL PIPELINE COMPLETED!")
        logger.info("==================================================")
        return True
    else:
        logger.error("Failed to write JSON database records.")
        return False

if __name__ == "__main__":
    try:
        res = run_pipeline()
        if res:
            sys.exit(0)  # Success - new editorial processed
        else:
            logger.info("No new editorial processed today. Exiting with code 2.")
            sys.exit(2)  # No new article - not an error, just nothing to do
    except SystemExit:
        raise
    except Exception as err:
        logger.error(f"Pipeline uncaught failure: {err}")
        sys.exit(1)
