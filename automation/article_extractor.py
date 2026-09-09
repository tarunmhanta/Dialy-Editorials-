"""
MBA EDITORIAL DAILY - ARTICLE EXTRACTOR MODULE
Fetches individual Indian Express editorial article pages and isolates main body text.
"""

from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

from config import HTTP_HEADERS, HTTP_TIMEOUT_SECONDS, MIN_ARTICLE_CHAR_LENGTH
from logger import logger

class ArticleExtractor:
    """
    Extracts structured body content and metadata from an Indian Express editorial page.
    """

    def fetch_page(self, url: str) -> Optional[str]:
        """Downloads article HTML with error handling."""
        try:
            logger.info(f"Extracting article page content from: {url}")
            response = requests.get(url, headers=HTTP_HEADERS, timeout=HTTP_TIMEOUT_SECONDS)
            if response.status_code == 200:
                return response.text
            else:
                logger.error(f"Failed to fetch article page. HTTP Status: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"Exception during article fetch: {e}")
            return None

    def extract_article(self, url: str, fallback_title: str = "") -> Optional[Dict[str, Any]]:
        """
        Parses page HTML, removes boilerplate HTML elements, and isolates article text.
        """
        html_text = self.fetch_page(url)
        if not html_text:
            return None

        soup = BeautifulSoup(html_text, "html.parser")

        # 1. Extract Title
        title = ""
        h1 = soup.find("h1", class_=lambda c: c and ("native" in c or "title" in c or "heading" in c))
        if not h1:
            h1 = soup.find("h1")
        if h1:
            title = h1.get_text(strip=True)
        if not title:
            title = fallback_title

        # 2. Extract Author
        author = "Editorial Board"
        author_element = soup.find(["span", "div", "a"], class_=lambda c: c and ("author" in c or "byline" in c or "editor" in c))
        if author_element:
            author_text = author_element.get_text(strip=True)
            if author_text and len(author_text) < 60:
                author = author_text.replace("By", "").replace("by", "").strip()

        # 3. Extract Date
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        time_tag = soup.find(["meta", "time", "span"], class_=lambda c: c and ("date" in c or "time" in c or "publish" in c))
        if time_tag:
            if time_tag.name == "meta" and time_tag.get("content"):
                raw_date = time_tag["content"]
            else:
                raw_date = time_tag.get_text(strip=True)
            
            # Attempt date extraction matching YYYY-MM-DD
            match = re.search(r"(\d{4}-\d{2}-\d{2})", raw_date)
            if match:
                date_str = match.group(1)

        # 4. Extract Main Article Body & Remove Boilerplate Noise
        # Primary container on Indian Express article pages
        story_div = soup.find("div", class_=lambda c: c and ("full-details" in c or "story-details" in c or "art-content" in c or "articles" in c))
        if not story_div:
            story_div = soup.find("div", id="storydetails")

        if not story_div:
            # Fallback to main content container if specific class changed
            story_div = soup.find("main") or soup.find("body")

        if not story_div:
            logger.error("Could not locate article body container on page.")
            return None

        # Remove unwanted boilerplate child tags (Ads, Newsletters, Social Links, Read Also boxes)
        unwanted_selectors = [
            "script", "style", "iframe", "ins", "header", "footer", "nav",
            ".ad-container", ".advertisement", ".social-share", ".read-also",
            ".newsletter-box", ".ie-app-download", ".comment-box", ".related-articles",
            ".custom-ad", "#comments", ".tags"
        ]
        for sel in unwanted_selectors:
            for el in story_div.select(sel):
                el.decompose()

        # Gather clean paragraph text
        paragraphs = []
        for p in story_div.find_all("p"):
            p_text = p.get_text(strip=True)
            # Filter short boilerplate lines, disclaimer notes, or app promotion links
            if len(p_text) > 25 and not any(phrase in p_text.lower() for phrase in [
                "subscribe to", "download the app", "click here", "read also", "for more latest news"
            ]):
                paragraphs.append(p_text)

        full_content = "\n\n".join(paragraphs)

        # 5. Quality Validation
        if len(full_content) < MIN_ARTICLE_CHAR_LENGTH:
            logger.error(
                f"Extracted article content length ({len(full_content)} chars) is below "
                f"minimum quality threshold ({MIN_ARTICLE_CHAR_LENGTH} chars)."
            )
            return None

        logger.info(f"Successfully extracted clean article '{title}' ({len(full_content)} characters).")

        return {
            "title": title,
            "url": url,
            "author": author,
            "date": date_str,
            "content": full_content
        }
