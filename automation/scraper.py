"""
MBA EDITORIAL DAILY - INDIAN EXPRESS SCRAPER MODULE
Discovers recent editorial articles from The Indian Express web section or RSS feed.
"""

from typing import List, Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import time

from config import (
    INDIAN_EXPRESS_EDITORIAL_URL,
    INDIAN_EXPRESS_RSS_URL,
    HTTP_HEADERS,
    HTTP_TIMEOUT_SECONDS,
    HTTP_MAX_RETRIES
)
from logger import logger

class EditorialScraper:
    """
    Scrapes recent editorial articles from The Indian Express.
    Supports both HTML page scraping and RSS feed parsing.
    """

    def fetch_url(self, url: str) -> Optional[str]:
        """
        Executes HTTP GET request with retries and timeout handling.
        """
        for attempt in range(1, HTTP_MAX_RETRIES + 1):
            try:
                logger.info(f"Fetching discovery URL (Attempt {attempt}/{HTTP_MAX_RETRIES}): {url}")
                response = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT_SECONDS)
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"HTTP status {response.status_code} received from {url}")
            except requests.RequestException as e:
                logger.warning(f"Network error on attempt {attempt}: {e}")
            
            if attempt < HTTP_MAX_RETRIES:
                time.sleep(2 * attempt)
        
        logger.error(f"Failed to fetch content from {url} after {HTTP_MAX_RETRIES} attempts.")
        return None

    def discover_editorials_from_html(self, html_content: str) -> List[Dict[str, Any]]:
        """
        Parses Indian Express editorial HTML listing page.
        """
        soup = BeautifulSoup(html_content, "html.parser")
        candidates: List[Dict[str, Any]] = []
        seen_urls = set()

        # Target article container blocks on Indian Express opinion/editorial layout
        articles = soup.find_all(["div", "article"], class_=lambda c: c and ("articles" in c or "title" in c or "story" in c or "nation" in c))
        if not articles:
            # Fallback link search if specific container classes shifted
            articles = soup.find_all("a", href=lambda h: h and "/article/opinion/editorials/" in h)

        for el in articles:
            a_tag = el if el.name == "a" else el.find("a", href=lambda h: h and "/article/opinion/editorials/" in h)
            if not a_tag or not a_tag.get("href"):
                continue

            href = a_tag["href"].strip()
            # Clean URL tracking parameters
            if "?" in href:
                href = href.split("?")[0]

            if href in seen_urls:
                continue
            seen_urls.add(href)

            title = a_tag.get_text(strip=True)
            if not title or len(title) < 10:
                # Try finding heading inside element if link text was empty
                h_tag = el.find(["h1", "h2", "h3", "h4"])
                if h_tag:
                    title = h_tag.get_text(strip=True)

            if not title or len(title) < 10:
                continue

            candidates.append({
                "title": title,
                "url": href,
                "author": "Editorial Board",
                "source": "The Indian Express"
            })

        logger.info(f"HTML Discovery found {len(candidates)} candidate editorial links.")
        return candidates

    def discover_editorials_from_rss(self, xml_content: str) -> List[Dict[str, Any]]:
        """
        Parses Indian Express editorial RSS Feed XML as a fallback mechanism.
        """
        soup = BeautifulSoup(xml_content, "xml")
        if not soup.find("item"):
            soup = BeautifulSoup(xml_content, "html.parser") # Fallback parser if lxml xml missing

        items = soup.find_all("item")
        candidates: List[Dict[str, Any]] = []

        for item in items:
            title_tag = item.find("title")
            link_tag = item.find("link")
            pub_date_tag = item.find("pubDate")

            if title_tag and link_tag:
                title = title_tag.get_text(strip=True)
                url = link_tag.get_text(strip=True)
                if "?" in url:
                    url = url.split("?")[0]
                
                pub_date = pub_date_tag.get_text(strip=True) if pub_date_tag else ""

                if "/article/opinion/editorials/" in url:
                    candidates.append({
                        "title": title,
                        "url": url,
                        "date_raw": pub_date,
                        "author": "Editorial Board",
                        "source": "The Indian Express"
                    })

        logger.info(f"RSS Discovery found {len(candidates)} candidate editorial items.")
        return candidates

    def get_latest_editorial_candidates(self) -> List[Dict[str, Any]]:
        """
        Primary entry point: Attempts discovery via HTML listing first, fallback to RSS feed.
        """
        html_text = self.fetch_url(INDIAN_EXPRESS_EDITORIAL_URL)
        if html_text:
            candidates = self.discover_editorials_from_html(html_text)
            if candidates:
                return candidates

        logger.info("HTML scraping yielded no items. Attempting RSS feed fallback...")
        rss_text = self.fetch_url(INDIAN_EXPRESS_RSS_URL)
        if rss_text:
            return self.discover_editorials_from_rss(rss_text)

        logger.error("Both HTML and RSS discovery failed to locate editorials.")
        return []
