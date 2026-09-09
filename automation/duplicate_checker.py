"""
MBA EDITORIAL DAILY - DUPLICATE DETECTION MODULE
Prevents re-processing and re-committing of previously processed editorials.
"""

import json
from typing import Dict, Any, List
from pathlib import Path
from config import INDEX_JSON_PATH
from logger import logger

class DuplicateChecker:
    """
    Checks article candidates against the existing JSON database index.
    """

    def __init__(self, index_path: Path = INDEX_JSON_PATH):
        self.index_path = index_path
        self.existing_records: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self):
        """Loads index.json file into memory."""
        if not self.index_path.exists():
            logger.info("index.json does not exist yet. Initializing empty duplicate tracker.")
            self.existing_records = []
            return

        try:
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.existing_records = data.get("editorials", [])
                logger.info(f"Loaded {len(self.existing_records)} existing records from index.json.")
        except Exception as e:
            logger.error(f"Error loading index.json for duplicate check: {e}")
            self.existing_records = []

    def is_duplicate(self, candidate_url: str, candidate_title: str) -> bool:
        """
        Determines whether candidate URL or Title matches any existing entry.
        """
        clean_url = candidate_url.strip().split("?")[0].rstrip("/")
        clean_title = candidate_title.strip().lower()

        for record in self.existing_records:
            # Check source URL match
            source_url = record.get("source", {}).get("url", "")
            if source_url:
                clean_record_url = source_url.strip().split("?")[0].rstrip("/")
                if clean_record_url == clean_url:
                    logger.info(f"Duplicate detected by URL: {candidate_url}")
                    return True

            # Check title similarity / exact match
            record_title = record.get("title", "").strip().lower()
            if record_title and record_title == clean_title:
                logger.info(f"Duplicate detected by Title match: '{candidate_title}'")
                return True

        return False
