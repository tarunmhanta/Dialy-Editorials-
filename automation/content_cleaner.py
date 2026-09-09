"""
MBA EDITORIAL DAILY - CONTENT CLEANER MODULE
Normalizes extracted article text and strips HTML/formatting artifacts.
"""

import re
from logger import logger

class ContentCleaner:
    """
    Cleans raw extracted article text prior to AI processing.
    """

    @staticmethod
    def clean(raw_text: str) -> str:
        if not raw_text:
            return ""

        # Normalize multiple spaces, tabs, carriage returns
        text = raw_text.replace("\r", "")

        # Split into paragraph blocks
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        cleaned_paragraphs = []
        seen = set()

        for p in paragraphs:
            # Collapse internal extra whitespace
            p_clean = re.sub(r"\s+", " ", p)

            # Deduplicate repeated paragraphs
            if p_clean in seen:
                continue
            seen.add(p_clean)

            # Strip leading/trailing bullets or noise
            p_clean = re.sub(r"^[\s\•\-\*]+", "", p_clean)

            if len(p_clean) > 20:
                cleaned_paragraphs.append(p_clean)

        final_text = "\n\n".join(cleaned_paragraphs)
        logger.info(f"Cleaned content text: Reduced to {len(cleaned_paragraphs)} paragraphs.")
        return final_text
