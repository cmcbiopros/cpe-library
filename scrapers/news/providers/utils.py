import re
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

import random
from urllib.parse import urlsplit, urlunsplit

import requests
from bs4 import BeautifulSoup


DATE_FORMATS = [
    # Try more specific formats first (with time)
    "%b %d, %Y %I:%M%p",   # Jan 16, 2026 3:29pm
    "%b %d, %Y %I:%M %p",  # Jan 16, 2026 3:29 pm
    "%b %d, %Y %I%p",      # Jan 16, 2026 3pm
    "%b %d, %Y %I %p",     # Jan 16, 2026 3 pm
    "%B %d, %Y %I:%M%p",   # January 16, 2026 3:29pm
    "%B %d, %Y %I:%M %p",  # January 16, 2026 3:29 pm
    "%B %d, %Y %I%p",      # January 16, 2026 3pm
    "%B %d, %Y %I %p",     # January 16, 2026 3 pm
    # Then simpler date-only formats
    "%Y-%m-%d",
    "%b %d, %Y",
    "%B %d, %Y",
    "%d %b %Y",
    "%d %B %Y",
    "%B %d %Y",           # January 16 2026
    "%b %d %Y",           # Jan 16 2026
]


USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7; rv:121.0) Gecko/20100101 Firefox/121.0"
]


def build_headers(url):
    parsed = urlsplit(url)
    base = urlunsplit((parsed.scheme, parsed.netloc, "", "", ""))
    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Referer": base
    }


def fetch_html(url, retries=3, timeout=20, sleep_range=(0.5, 1.0)):
    session = requests.Session()
    for attempt in range(retries):
        try:
            time.sleep(sleep_range[0] + (sleep_range[1] - sleep_range[0]) * attempt / max(retries - 1, 1))
            response = session.get(url, timeout=timeout, headers=build_headers(url))
            response.raise_for_status()
            return response.text
        except Exception as exc:
            if attempt == retries - 1:
                raise exc
            time.sleep(0.5)


def clean_text(text):
    if not text:
        return ""
    try:
        text = text.encode("latin1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def parse_date(text):
    if not text:
        return None
    cleaned = clean_text(text)
    cleaned = re.sub(r"(\\d{1,2})(st|nd|rd|th)", r"\\1", cleaned, flags=re.IGNORECASE)
    
    # Try RFC 822 format first (common in RSS feeds)
    try:
        dt = parsedate_to_datetime(cleaned)
        if dt and dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except (ValueError, TypeError):
        pass
    
    # Try standard date formats
    for fmt in DATE_FORMATS:
        try:
            dt = datetime.strptime(cleaned, fmt)
            return dt
        except ValueError:
            continue
    
    # Try ISO format
    try:
        dt = datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
        if dt.tzinfo:
            dt = dt.replace(tzinfo=None)
        return dt
    except ValueError:
        pass
    
    return None


def soup_from_url(url):
    html = fetch_html(url)
    return BeautifulSoup(html, "html.parser")


def extract_text_from_selectors(soup, selectors):
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            return clean_text(node.get_text(" ", strip=True))
    return ""


def extract_body_text(soup, selectors):
    for selector in selectors:
        node = soup.select_one(selector)
        if node:
            paragraphs = [clean_text(p.get_text(" ", strip=True)) for p in node.find_all("p")]
            paragraphs = [p for p in paragraphs if p]
            if paragraphs:
                return " ".join(paragraphs)
    return ""