from datetime import datetime
import json
import urllib.parse

import requests
from urllib.parse import urljoin

from .utils import clean_text, extract_body_text, extract_text_from_selectors, parse_date, soup_from_url

PROVIDER_NAME = "Pharmaceutical Commerce"
BASE_URL = "https://www.pharmaceuticalcommerce.com"
LISTING_URL = f"{BASE_URL}/news"
SANITY_PROJECT_ID = "0vv8moc6"
SANITY_DATASET = "pharma_commerce"


def fetch_sanity_published_date(title, slug=None):
    if not title and not slug:
        return None
    if slug:
        query = "*[_type=='article' && url.current==$slug][0]{published}"
        params = {"query": query, "$slug": json.dumps(slug)}
    else:
        query = "*[_type=='article' && title==$title][0]{published}"
        params = {"query": query, "$title": json.dumps(title)}
    try:
        resp = requests.get(
            f"https://{SANITY_PROJECT_ID}.api.sanity.io/v1/data/query/{SANITY_DATASET}",
            params=params,
            timeout=15,
            headers={"User-Agent": "Mozilla/5.0"}
        )
        resp.raise_for_status()
        data = resp.json().get("result") or {}
        published = data.get("published")
        return published
    except Exception:
        return None


def discover_articles(cutoff_date, seen_urls=None, max_pages=20):
    seen_urls = seen_urls or set()
    discoveries = []
    for page in range(1, max_pages + 1):
        url = f"{LISTING_URL}?page={page}"
        soup = soup_from_url(url)

        cards = soup.select("article, .views-row, .listing-item, .card")
        page_items = []
        for card in cards:
            link = card.find("a", href=True)
            if not link:
                continue
            href = urljoin(BASE_URL, link["href"])
            if "/view/" not in href:
                continue
            if href in seen_urls:
                continue

            title = clean_text(link.get_text(" ", strip=True))
            date_text = ""
            time_tag = card.find("time")
            if time_tag and time_tag.get("datetime"):
                date_text = time_tag.get("datetime")
            elif time_tag:
                date_text = time_tag.get_text(" ", strip=True)
            else:
                card_text = card.get_text(" ", strip=True)
                date_text = card_text

            published_at = parse_date(date_text)
            page_items.append({
                "url": href,
                "published_at": published_at,
                "title": title
            })

        if not page_items:
            break

        discoveries.extend(page_items)

        if all(item["published_at"] and item["published_at"] < cutoff_date for item in page_items):
            break

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
        published_text = extract_text_from_selectors(soup, ["meta[property='article:published_time']", "meta[name='article:published_time']"])

    published_at = parse_date(published_text)
    author = extract_text_from_selectors(soup, [".author-name", ".byline", ".author"])

    body_text = ""
    for script in soup.find_all("script", type="application/ld+json"):
        if not script.string:
            continue
        try:
            data = json.loads(script.string)
        except json.JSONDecodeError:
            continue
        if isinstance(data, dict) and data.get("articleBody"):
            body_text = clean_text(data.get("articleBody"))
            if not title:
                title = clean_text(data.get("headline", ""))
            if not published_at and data.get("datePublished"):
                published_at = parse_date(data.get("datePublished"))
            break

    if not body_text:
        body_text = extract_body_text(
            soup,
            [
                "article .article-body",
                "article .content",
                "article .body",
                "article",
                ".article-content",
                ".content-body",
                ".field--name-body"
            ]
        )

    slug = url.rstrip("/").split("/")[-1] if url else None
    sanity_published = fetch_sanity_published_date(title, slug)
    if sanity_published:
        sanity_dt = parse_date(sanity_published)
        if sanity_dt:
            published_at = sanity_dt

    return {
        "title": title,
        "published_at": published_at.strftime("%Y-%m-%d") if isinstance(published_at, datetime) else "",
        "author": author,
        "body": body_text,
        "url": url,
        "outlet": PROVIDER_NAME
    }
