import requests
from bs4 import BeautifulSoup
import json
import sys
sys.path.insert(0, '.')
from config import HTTP_HEADERS

# Check what the RSS feed returns - it may contain the full text
rss_url = 'https://indianexpress.com/section/opinion/editorials/feed/'
resp = requests.get(rss_url, headers=HTTP_HEADERS, timeout=20)
print(f'RSS Status: {resp.status_code}')

soup = BeautifulSoup(resp.text, 'xml')
items = soup.find_all('item')
print(f'Total RSS items: {len(items)}')
print()

for i, item in enumerate(items[:3]):
    print(f'=== ITEM [{i}] ===')
    print(f'Title: {item.find("title").get_text(strip=True) if item.find("title") else "N/A"}')
    print(f'Link: {item.find("link").get_text(strip=True) if item.find("link") else "N/A"}')
    
    # Check all child tags for content
    for child in item.children:
        if hasattr(child, 'name') and child.name:
            text = child.get_text(strip=True)
            if len(text) > 50:
                print(f'  <{child.name}> ({len(text)} chars): {text[:300]}')
    print()
