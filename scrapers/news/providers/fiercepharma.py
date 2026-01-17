from datetime import datetime
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from .utils import clean_text, extract_body_text, extract_text_from_selectors, parse_date, fetch_html, soup_from_url

PROVIDER_NAME = "Fierce Pharma"
BASE_URL = "https://www.fiercepharma.com"
RSS_FEEDS = [
    "https://www.fiercepharma.com/rss/xml",
    "https://www.fiercepharma.com/rss.xml"
]


def discover_articles(cutoff_date, seen_urls=None, max_pages=None):
    seen_urls = seen_urls or set()
    discoveries = []

    feed_content = None
    feed_url = None
    for url in RSS_FEEDS:
        try:
            feed_content = fetch_html(url)
            feed_url = url
            break
        except Exception as e:
            print(f"  Failed to fetch RSS feed {url}: {e}")
            continue

    if not feed_content:
        print(f"  No RSS feed content retrieved from {RSS_FEEDS}")
        return discoveries

    try:
        soup = BeautifulSoup(feed_content, "xml")
        items = soup.find_all("item")
        print(f"  Found {len(items)} items in RSS feed")
        
        for item in items:
            link_tag = item.find("link")
            url = clean_text(link_tag.get_text()) if link_tag else ""
            if not url:
                continue
            # RSS links are usually absolute, but ensure they're complete
            if url.startswith("/"):
                url = urljoin(BASE_URL, url)
            elif not url.startswith("http"):
                url = urljoin(BASE_URL, url)
            
            if url in seen_urls:
                continue

            title_tag = item.find("title")
            title = clean_text(title_tag.get_text()) if title_tag else ""
            
            pub_date_tag = item.find("pubDate")
            pub_date = clean_text(pub_date_tag.get_text()) if pub_date_tag else ""
            
            published_at = parse_date(pub_date)
            if not published_at:
                # If date parsing fails, try to continue anyway (will be filtered later)
                print(f"  Warning: Could not parse date '{pub_date}' for {url}")
                continue
            
            if published_at < cutoff_date:
                continue

            discoveries.append({
                "url": url,
                "published_at": published_at,
                "title": title,
                "feed_url": feed_url
            })
    except Exception as e:
        print(f"  Error parsing RSS feed: {e}")

    print(f"  Discovered {len(discoveries)} articles after filtering")
    return discoveries


def parse_article(url):
    soup = soup_from_url(url)

    title = extract_text_from_selectors(soup, ["h1", "header h1"])
    published_text = ""
    time_tag = soup.find("time")
    if time_tag and time_tag.get("datetime"):
        published_text = time_tag.get("datetime")
    elif time_tag:
        published_text = time_tag.get_text(" ", strip=True)
    else:
        published_text = extract_text_from_selectors(soup, ["meta[property='article:published_time']"])

    published_at = parse_date(published_text)
    body_text = extract_body_text(
        soup,
        [
            "article .article-body",
            "article .content",
            "article",
            ".article-content",
            ".content-body"
        ]
    )

    return {
        "title": title,
        "published_at": published_at.strftime("%Y-%m-%d") if isinstance(published_at, datetime) else "",
        "body": body_text,
        "url": url,
        "outlet": PROVIDER_NAME
    }