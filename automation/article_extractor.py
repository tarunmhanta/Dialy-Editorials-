"""
MBA EDITORIAL DAILY - ARTICLE EXTRACTOR MODULE
Fetches individual Indian Express editorial article pages and extracts complete body text.
Includes automatic fallback to Indian Express /lite/ endpoint for clean, reliable content.
"""

from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

from config import HTTP_HEADERS, HTTP_TIMEOUT_SECONDS
from logger import logger

# Indian Express editorials are typically 1,200 - 3,500 characters (3-5 focused paragraphs)
MIN_CONTENT_LENGTH = 300

class ArticleExtractor:
    """
    Extracts structured body content and metadata from an Indian Express editorial page.
    """

    def fetch_html(self, url: str) -> Optional[str]:
        """Downloads page HTML with standard browser headers."""
        try:
            logger.info(f"Fetching article content from: {url}")
            response = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return response.text
            else:
                logger.warning(f"Fetch failed for {url} with status {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception during article fetch from {url}: {e}")
            return None

    def _extract_from_soup(self, soup: BeautifulSoup, url: str, fallback_title: str = "") -> Optional[Dict[str, Any]]:
        """Extracts metadata and body paragraphs from parsed HTML soup."""
        # 1. Extract Title
        title = ""
        h1 = soup.find("h1", class_=lambda c: c and ("native" in c or "title" in c or "heading" in c))
        if not h1:
            h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        if not title:
            title = fallback_title

        # Clean title - remove "Opinion" or "Editorial:" prefix that IE sometimes prefixes
        title = re.sub(r'^(?:Opinion|Editorial|IE Editorial)\s*[:|-]?\s*', '', title, flags=re.IGNORECASE).strip()

        # 2. Extract Author
        author = "Editorial Board"
        author_element = soup.find(["span", "div", "a"], class_=lambda c: c and ("author" in c or "byline" in c or "editor" in c))
        if author_element:
            author_text = author_element.get_text(strip=True)
            if author_text and len(author_text) < 60:
                author = author_text.replace("By", "").replace("by", "").strip()

        # 3. Extract Date
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        date_meta = soup.find("meta", {"property": "article:published_time"})
        if not date_meta:
            date_meta = soup.find("meta", {"name": "publish-date"})
        if not date_meta:
            date_meta = soup.find("meta", {"name": "date"})

        if date_meta and date_meta.get("content"):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", date_meta["content"])
            if match:
                date_str = match.group(1)
        else:
            time_tag = soup.find(["meta", "time", "span"], class_=lambda c: c and ("date" in c or "time" in c or "publish" in c))
            if time_tag:
                raw_date = time_tag.get("content", "") or time_tag.get_text(strip=True)
                match = re.search(r"(\d{4}-\d{2}-\d{2})", raw_date)
                if match:
                    date_str = match.group(1)

        # 4. Locate Story Container
        story_div = soup.find("div", class_=lambda c: c and ("disc-paragraph" in c or "story_details" in c or "full-details" in c or "art-content" in c or "story-details" in c))
        if not story_div:
            story_div = soup.find("div", id="storydetails")
        if not story_div:
            story_div = soup.find("div", class_="app-content")
        if not story_div:
            story_div = soup.find("main") or soup.find("article") or soup.find("body")

        if not story_div:
            return None

        # Clean noise tags
        unwanted_selectors = [
            "script", "style", "iframe", "ins", "header", "footer", "nav",
            ".ad-container", ".advertisement", ".social-share", ".read-also",
            ".newsletter-box", ".ie-app-download", ".comment-box", ".related-articles",
            ".custom-ad", "#comments", ".tags", ".story-tags", ".premium-banner"
        ]
        for sel in unwanted_selectors:
            for el in story_div.select(sel):
                el.decompose()

        # Extract all meaningful paragraphs
        paragraphs = []
        for p in story_div.find_all("p"):
            p_text = p.get_text(strip=True)
            if len(p_text) > 30 and not any(phrase in p_text.lower() for phrase in [
                "subscribe to", "download the app", "click here", "read also", "for more latest news",
                "follow us on", "get our newsletter", "express explained", "first published on"
            ]):
                paragraphs.append(p_text)

        full_content = "\n\n".join(paragraphs)

        if len(full_content) < MIN_CONTENT_LENGTH:
            return None

        return {
            "title": title,
            "url": url,
            "author": author,
            "date": date_str,
            "content": full_content
        }

    def extract_article(self, url: str, fallback_title: str = "") -> Optional[Dict[str, Any]]:
        """
        Attempts standard page extraction first.
        If blocked or incomplete, automatically falls back to Indian Express /lite/ endpoint.
        """
        # 1. Attempt primary URL
        clean_url = url.split("?")[0].rstrip("/")
        html_text = self.fetch_html(clean_url + "/")
        
        if html_text:
            soup = BeautifulSoup(html_text, "html.parser")
            data = self._extract_from_soup(soup, clean_url, fallback_title)
            if data and len(data["content"]) >= MIN_CONTENT_LENGTH:
                logger.info(f"Successfully extracted full article '{data['title']}' ({len(data['content'])} characters).")
                return data

        # 2. Attempt /lite/ endpoint fallback
        lite_url = f"{clean_url}/lite/"
        logger.info(f"Attempting /lite/ fallback endpoint: {lite_url}")
        lite_html = self.fetch_html(lite_url)
        if lite_html:
            soup = BeautifulSoup(lite_html, "html.parser")
            data = self._extract_from_soup(soup, clean_url, fallback_title)
            if data and len(data["content"]) >= MIN_CONTENT_LENGTH:
                logger.info(f"Successfully extracted via /lite/ endpoint: '{data['title']}' ({len(data['content'])} characters).")
                return data

        logger.error(f"Failed to extract article content from {url} across all methods.")
        return None
