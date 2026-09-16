"""
MBA EDITORIAL DAILY - INDIAN EXPRESS SCRAPER MODULE
Discovers recent editorial articles using multiple resilient feed sources:
1. Primary Indian Express Editorial RSS
2. Indian Express Opinion RSS
3. Google News RSS for Indian Express Editorials (100% cloud & datacenter resilient)
"""

from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime, timezone, timedelta
from email.utils import parsedate_to_datetime

from config import (
    INDIAN_EXPRESS_EDITORIAL_URL,
    INDIAN_EXPRESS_RSS_URL,
    HTTP_HEADERS,
    HTTP_TIMEOUT_SECONDS,
    HTTP_MAX_RETRIES
)
from logger import logger

IST = timezone(timedelta(hours=5, minutes=30))

# Additional fallback sources to guarantee 100% discovery uptime on cloud runners
INDIAN_EXPRESS_OPINION_RSS = "https://indianexpress.com/section/opinion/feed/"
GOOGLE_NEWS_IE_EDITORIALS_RSS = "https://news.google.com/rss/search?q=site:indianexpress.com/article/opinion/editorials&hl=en-IN&gl=IN&ceid=IN:en"

class EditorialScraper:
    """
    Scrapes recent editorial articles from The Indian Express with multi-tier fallbacks.
    """

    def fetch_url(self, url: str) -> Optional[str]:
        """Executes HTTP GET request with retries and timeout handling."""
        for attempt in range(1, HTTP_MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching URL (Attempt {attempt}/{HTTP_MAX_RETRIES}): {url}")
                response = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT_SECONDS)
                if response.status_code == 200 and len(response.text) > 200:
                    return response.text
                else:
                    logger.warning(f"HTTP status {response.status_code} received from {url}")
            except requests.RequestException as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
            
            if attempt < HTTP_MAX_RETRIES:
                time.sleep(2 * attempt)
        
        logger.error(f"Failed to fetch content from {url} after {HTTP_MAX_RETRIES} attempts.")
        return None

    def discover_editorials_from_rss(self, xml_content: str, source_name: str = "Indian Express RSS") -> List[Dict[str, Any]]:
        """
        Parses editorial RSS feed XML, extracts title, link, and publication date in IST.
        """
        soup = BeautifulSoup(xml_content, "xml")
        if not soup.find("item"):
            soup = BeautifulSoup(xml_content, "html.parser")

        items = soup.find_all("item")
        candidates: List[Dict[str, Any]] = []
        seen_urls = set()

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            pub_date_tag = item.find("pubDate")

            if not (title_tag and link_tag):
                continue

            title = title_tag.get_text(strip=True)
            url = link_tag.get_text(strip=True)
            if "?" in url:
                url = url.split("?")[0]

            # Filter for editorial articles
            if "/article/opinion/editorials/" not in url:
                continue

            if url in seen_urls:
                continue
            seen_urls.add(url)

            # Clean title - strip " - The Indian Express" suffix if present (from Google News)
            title = title.replace(" - The Indian Express", "").strip()

            pub_date_raw = pub_date_tag.get_text(strip=True) if pub_date_tag else ""
            pub_datetime = None

            if pub_date_raw:
                try:
                    pub_datetime = parsedate_to_datetime(pub_date_raw)
                    if pub_datetime.tzinfo is None:
                        pub_datetime = pub_datetime.replace(tzinfo=timezone.utc)
                    pub_datetime = pub_datetime.astimezone(IST)
                except Exception:
                    pass

            candidates.append({
                "title": title,
                "url": url,
                "date_raw": pub_date_raw,
                "pub_datetime": pub_datetime,
                "author": "Editorial Board",
                "source": "The Indian Express"
            })

        # Sort candidates newest first
        candidates.sort(
            key=lambda x: x["pub_datetime"] or datetime(2000, 1, 1, tzinfo=IST),
            reverse=True
        )

        logger.info(f"{source_name} discovered {len(candidates)} editorial candidates.")
        return candidates

    def get_latest_editorial_candidates(self) -> List[Dict[str, Any]]:
        """
        Primary entry point with resilient cascading fallback sources:
        1. Official Indian Express Editorial RSS
        2. Official Indian Express Opinion RSS
        3. Google News RSS mirror (datacenter immune)
        """
        # Tier 1: Indian Express Editorial RSS Feed
        rss_text = self.fetch_url(INDIAN_EXPRESS_RSS_URL)
        if rss_text:
            candidates = self.discover_editorials_from_rss(rss_text, "Indian Express Editorial RSS")
            if candidates:
                return candidates

        # Tier 2: Indian Express Opinion Feed Fallback
        logger.warning("Primary Editorial RSS failed. Falling back to Opinion RSS feed...")
        opinion_text = self.fetch_url(INDIAN_EXPRESS_OPINION_RSS)
        if opinion_text:
            candidates = self.discover_editorials_from_rss(opinion_text, "Indian Express Opinion RSS")
            if candidates:
                return candidates

        # Tier 3: Google News RSS Mirror Fallback
        logger.warning("Attempting Google News RSS mirror fallback...")
        gnews_text = self.fetch_url(GOOGLE_NEWS_IE_EDITORIALS_RSS)
        if gnews_text:
            candidates = self.discover_editorials_from_rss(gnews_text, "Google News Mirror RSS")
            if candidates:
                return candidates

        logger.error("All editorial discovery sources failed.")
        return []
