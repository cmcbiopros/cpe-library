from datetime import datetime
from urllib.parse import urljoin
import json
import re

from .utils import clean_text, extract_body_text, extract_text_from_selectors, parse_date, soup_from_url

PROVIDER_NAME = "BioProcess International"
BASE_URL = "https://www.bioprocessintl.com"
LISTING_URL = f"{BASE_URL}/bioprocess-insider/facilities-capacity"


def discover_articles(cutoff_date, seen_urls=None, max_pages=20):
    seen_urls = seen_urls or set()
    discoveries = []

    for page in range(1, max_pages + 1):
        url = f"{LISTING_URL}?page={page}"
        soup = soup_from_url(url)

        container = soup.find(attrs={"data-template": "list-content"})
        if not container:
            container = soup

        page_items = []
        for link in container.find_all("a", href=True):
            href = link["href"]
            if "/facilities-capacity/" not in href:
                continue
            href = urljoin(BASE_URL, href)
            if href in seen_urls:
                continue

            card = link.find_parent(lambda tag: tag.name in ["article", "div"] and tag.get("class") and any("ContentCard" in c or "ContentPreview" in c for c in tag.get("class", []))) or link.find_parent("article") or link.parent
            title_node = card.select_one(".ContentCard-Title") if card else None
            title = clean_text(title_node.get_text(" ", strip=True)) if title_node else clean_text(link.get_text(" ", strip=True))

            date_node = card.select_one(".ContentCard-Date") if card else None
            date_text = date_node.get_text(" ", strip=True) if date_node else ""

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
        published_text = extract_text_from_selectors(soup, ["meta[property='article:published_time']"])

    published_at = parse_date(published_text)
    if not published_at:
        for script in soup.find_all("script", type="application/ld+json"):
            if not script.string:
                continue
            try:
                data = json.loads(script.string)
            except json.JSONDecodeError:
                continue
            payloads = data if isinstance(data, list) else [data]
            for payload in payloads:
                if isinstance(payload, dict) and payload.get("datePublished"):
                    published_at = parse_date(payload.get("datePublished"))
                    if published_at:
                        break
            if published_at:
                break
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

    if not body_text or len(body_text) < 200:
        body_text = extract_body_from_stream(soup, title)

    return {
        "title": title,
        "published_at": published_at.strftime("%Y-%m-%d") if isinstance(published_at, datetime) else "",
        "body": body_text,
        "url": url,
        "outlet": PROVIDER_NAME
    }


def extract_body_from_stream(soup, title):
    script = None
    for s in soup.find_all("script"):
        if s.string and "streamController.enqueue" in s.string:
            script = s.string
            break

    if not script:
        return ""

    match = re.search(r'enqueue\("(.*)"\)', script, re.DOTALL)
    if not match:
        match = re.search(r'enqueue\("(.*)"\);', script, re.DOTALL)
    if not match:
        match = re.search(r'enqueue\("(.*)"\)\s*;', script, re.DOTALL)
    if not match:
        return ""

    payload = match.group(1)
    try:
        payload = payload.encode("utf-8").decode("unicode_escape")
        data = json.loads(payload)
    except Exception:
        return ""

    candidates = []

    def walk(obj):
        if isinstance(obj, str):
            candidates.append(obj)
        elif isinstance(obj, list):
            for item in obj:
                walk(item)
        elif isinstance(obj, dict):
            for value in obj.values():
                walk(value)

    walk(data)

    cleaned = []
    for text in candidates:
        if not text or len(text) < 80:
            continue
        if "mailto:" in text or "http" in text:
            continue
        if text.count(" ") < 8:
            continue
        cleaned.append(clean_text(text))

    if not cleaned:
        return ""

    filtered = cleaned
    if title:
        filtered = [t for t in cleaned if title not in t]
        stopwords = {"from", "deal", "with", "into", "will", "this", "that", "acquire", "acquires", "acquisition"}
        keywords = [w.lower() for w in re.findall(r"[A-Za-z]{3,}", title) if w.lower() not in stopwords]
        keyword_hits = [t for t in filtered if any(k in t.lower() for k in keywords)]
        if keyword_hits:
            filtered = keyword_hits
        if not filtered:
            filtered = cleaned

    return " ".join(filtered)
