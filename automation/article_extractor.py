"""
MBA EDITORIAL DAILY - ARTICLE EXTRACTOR MODULE (UPDATED)
Fetches available preview from Indian Express and supplements with web search context.
Falls back to title-based analysis when article is behind paywall.
"""

from typing import Dict, Any, Optional
import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

from config import HTTP_HEADERS, HTTP_TIMEOUT_SECONDS, MIN_ARTICLE_CHAR_LENGTH
from logger import logger

# Reduced minimum threshold since IE is paywalled - we'll use preview + title context
PAYWALL_MIN_CHARS = 200

class ArticleExtractor:
    """
    Extracts structured body content and metadata from an Indian Express editorial page.
    Works with paywalled pages by using available preview + title context.
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

    def is_paywalled(self, soup: BeautifulSoup) -> bool:
        """Detects if page content is behind a paywall."""
        page_text = soup.get_text().lower()
        paywall_signals = ["subscribe to continue", "subscribe now", "already a subscriber", 
                           "this content is available", "premium article", "paywall"]
        return any(signal in page_text for signal in paywall_signals)

    def extract_article(self, url: str, fallback_title: str = "") -> Optional[Dict[str, Any]]:
        """
        Parses page HTML, extracts available preview content.
        For paywalled articles, uses title + preview + editorial URL for Gemini context.
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

        # Clean title - remove "Opinion" prefix that IE adds
        title = re.sub(r'^Opinion\s*', '', title).strip()

        # 2. Extract Author
        author = "Editorial Board"
        author_element = soup.find(["span", "div", "a"], class_=lambda c: c and ("author" in c or "byline" in c or "editor" in c))
        if author_element:
            author_text = author_element.get_text(strip=True)
            if author_text and len(author_text) < 60:
                author = author_text.replace("By", "").replace("by", "").strip()

        # 3. Extract Date
        date_str = datetime.utcnow().strftime("%Y-%m-%d")
        # Try meta tags first (most reliable)
        date_meta = soup.find("meta", {"property": "article:published_time"})
        if not date_meta:
            date_meta = soup.find("meta", {"name": "publish-date"})
        if date_meta and date_meta.get("content"):
            match = re.search(r"(\d{4}-\d{2}-\d{2})", date_meta["content"])
            if match:
                date_str = match.group(1)
        else:
            # Fallback: search in page text
            time_tag = soup.find(["meta", "time", "span"], class_=lambda c: c and ("date" in c or "time" in c or "publish" in c))
            if time_tag:
                raw_date = time_tag.get("content", "") or time_tag.get_text(strip=True)
                match = re.search(r"(\d{4}-\d{2}-\d{2})", raw_date)
                if match:
                    date_str = match.group(1)

        # 4. Extract All Available Paragraphs (preview)
        # Try specific IE containers first
        story_div = soup.find("div", class_=lambda c: c and ("disc-paragraph" in c or "story_details" in c or "full-details" in c or "art-content" in c))
        if not story_div:
            story_div = soup.find("div", id="storydetails")
        if not story_div:
            story_div = soup.find("main") or soup.find("body")

        paragraphs = []
        if story_div:
            # Remove boilerplate
            for sel in ["script", "style", "iframe", "ins", "header", "footer", "nav",
                        ".ad-container", ".advertisement", ".social-share", ".read-also",
                        ".newsletter-box", ".ie-app-download", ".comment-box", ".related-articles",
                        ".custom-ad", "#comments", ".tags"]:
                for el in story_div.select(sel):
                    el.decompose()

            for p in story_div.find_all("p"):
                p_text = p.get_text(strip=True)
                if len(p_text) > 25 and not any(phrase in p_text.lower() for phrase in [
                    "subscribe to", "download the app", "click here", "read also", "for more latest news",
                    "follow us on", "get our newsletter"
                ]):
                    paragraphs.append(p_text)

        preview_text = "\n\n".join(paragraphs)
        paywalled = self.is_paywalled(soup)

        # 5. Build enriched content for Gemini
        if paywalled or len(preview_text) < MIN_ARTICLE_CHAR_LENGTH:
            logger.warning(f"Article appears paywalled. Only {len(preview_text)} chars available. Using title + preview context for Gemini analysis.")

            # Build Gemini-ready context from available info
            full_content = f"""EDITORIAL TITLE: {title}

PUBLICATION: The Indian Express (Indian national newspaper, editorial section)
DATE: {date_str}
ARTICLE URL: {url}

AVAILABLE PREVIEW TEXT:
{preview_text if preview_text else "No preview available."}

INSTRUCTION FOR ANALYSIS:
This is an Indian Express editorial. Even with limited preview text, use your knowledge of:
- The title topic and its current context in India
- Related economic, political, and policy developments in India
- Recent news and events related to this topic
- Standard editorial positions Indian Express typically takes on such issues

Generate a thorough, educational MBA-focused analysis based on the editorial title, topic, and available context.
Be specific about real policy, economic data, and business implications relevant to this topic.
"""
        else:
            full_content = preview_text
            logger.info(f"Successfully extracted full article content ({len(full_content)} characters).")

        logger.info(f"Article ready for AI processing: '{title}' ({len(full_content)} chars, paywalled={paywalled})")

        return {
            "title": title,
            "url": url,
            "author": author,
            "date": date_str,
            "content": full_content,
            "paywalled": paywalled
        }
