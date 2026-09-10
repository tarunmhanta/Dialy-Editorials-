import requests
from bs4 import BeautifulSoup
import sys
sys.path.insert(0, '.')
from config import HTTP_HEADERS

# Try today's September 10th editorial
url = 'https://indianexpress.com/article/opinion/editorials/welcome-to-the-south-american-dream-10870790/'
resp = requests.get(url, headers=HTTP_HEADERS, timeout=20)
soup = BeautifulSoup(resp.text, 'html.parser')

# Check full page structure
print('=== Full-page meta title ===')
t = soup.find('title')
if t: print(t.get_text())

print()
print(f'Total <p> tags: {len(soup.find_all("p"))}')
print()

# Show all div classes that might contain article text
print('=== Potential article containers ===')
for div in soup.find_all('div', class_=True):
    classes = ' '.join(div.get('class', []))
    if any(kw in classes.lower() for kw in ['article', 'story', 'content', 'full', 'body', 'text', 'detail', 'premium', 'paid']):
        p_count = len(div.find_all('p'))
        text_len = len(div.get_text(strip=True))
        if p_count > 0 or text_len > 200:
            print(f'  div.class="{classes[:80]}" => {p_count} <p> tags, {text_len} chars')

print()
# Check for any subscriber/paywall indicators
for kw in ['paywall', 'subscriber', 'subscribe', 'premium', 'locked', 'metered']:
    hits = soup.find_all(string=lambda t: t and kw.lower() in t.lower())
    if hits:
        print(f'Paywall keyword "{kw}" found in page: YES ({len(hits)} occurrences)')
    else:
        print(f'Paywall keyword "{kw}" found in page: NO')
