"""Quick test to verify the updated scraper filters for today's editorials."""
import sys
sys.path.insert(0, '.')

from scraper import EditorialScraper
from duplicate_checker import DuplicateChecker
from article_extractor import ArticleExtractor
from content_cleaner import ContentCleaner

print("=== Testing Updated Scraper ===")
scraper = EditorialScraper()
candidates = scraper.get_latest_editorial_candidates()

print(f"\nTotal candidates returned: {len(candidates)}")
for i, c in enumerate(candidates):
    dt = c.get('pub_datetime')
    date_str = dt.strftime('%Y-%m-%d %H:%M IST') if dt else 'N/A'
    print(f"  [{i}] {date_str} | {c['title']}")
    print(f"       {c['url']}")

print("\n=== Testing Duplicate Checker ===")
dc = DuplicateChecker()
for c in candidates:
    is_dup = dc.is_duplicate(c['url'], c['title'])
    print(f"  {'[DUPLICATE]' if is_dup else '[NEW]'} {c['title']}")

print("\n=== Testing Article Extractor (first non-duplicate) ===")
for c in candidates:
    if not dc.is_duplicate(c['url'], c['title']):
        extractor = ArticleExtractor()
        data = extractor.extract_article(c['url'], c['title'])
        if data:
            cleaned = ContentCleaner.clean(data['content'])
            print(f"Selected: {data['title']}")
            print(f"Date: {data['date']}")
            print(f"Paywalled: {data.get('paywalled', False)}")
            print(f"Content length: {len(cleaned)} chars")
            print(f"First 300 chars:\n{cleaned[:300]}")
        else:
            print("EXTRACTION FAILED!")
        break
