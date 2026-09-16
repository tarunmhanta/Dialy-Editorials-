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
    Returns True if a new editorial was successfully processed and saved, False if all already exist.
    Raises SystemExit(1) on actual errors.
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
        logger.error("FATAL: No candidate editorials discovered from any source. Check network or feed availability.")
        sys.exit(1)

    logger.info(f"Discovered {len(candidates)} candidate editorials across feeds.")

    # Step 3: Find Newest Unprocessed Candidate
    logger.info("Step 2/6: Filtering candidates against existing database...")
    extractor = ArticleExtractor()
    target_candidate: Optional[dict] = None
    article_data: Optional[dict] = None

    for idx, candidate in enumerate(candidates):
        url = candidate.get("url", "")
        title = candidate.get("title", "")
        
        if duplicate_checker.is_duplicate(url, title):
            continue

        logger.info(f"Candidate #{idx+1} is new: '{title}' ({url}). Attempting extraction...")
        extracted = extractor.extract_article(url=url, fallback_title=title)
        
        if extracted and len(extracted.get("content", "")) >= 300:
            target_candidate = candidate
            article_data = extracted
            break
        else:
            logger.warning(f"Candidate '{title}' could not be extracted. Trying next candidate...")

    if not target_candidate or not article_data:
        logger.info("All discovered editorials have already been processed into index.json. Database is fully up to date.")
        return False

    logger.info(f"Step 3/6: Selected editorial: '{article_data['title']}' ({article_data['date']})")

    # Step 4: Clean Content
    logger.info("Step 4/6: Cleaning content and normalizing text...")
    cleaned_text = ContentCleaner.clean(article_data["content"])
    article_data["content"] = cleaned_text

    # Step 5: Send to Gemini AI (Strict grounding in provided text only)
    logger.info("Step 5/6: Processing article with Google Gemini AI...")
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
    logger.info("Step 6/6: Writing editorial JSON database records...")
    json_manager = JSONManager()
    success = json_manager.save_editorial(ai_output, article_data["date"])

    if success:
        logger.info("==================================================")
        logger.info(f"SUCCESS: SAVED EDITORIAL '{article_data['title']}' ({article_data['date']})")
        logger.info("==================================================")
        return True
    else:
        logger.error("Failed to write JSON database records.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        res = run_pipeline()
        if res:
            sys.exit(0)  # New editorial was processed and saved
        else:
            logger.info("No new editorial needed today (already up to date). Exiting with code 2.")
            sys.exit(2)
    except SystemExit:
        raise
    except Exception as err:
        logger.error(f"Pipeline uncaught failure: {err}")
        sys.exit(1)
